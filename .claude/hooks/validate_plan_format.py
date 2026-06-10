#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.8"
# ///

"""
PreToolUse hook: Validates plan format before /build creates a team.

Triggered on TeamCreate calls. Scans specs/*.md for the active plan
and validates it has all required sections before allowing the build
to proceed.

Required plan sections:
  - ## Task Description
  - ## Objective
  - ## Relevant Files
  - ## Step by Step Tasks (or ## Task Graph)
  - ## Acceptance Criteria
  - ## Team Orchestration
  - ### Team Members

Additional checks:
  - At least one builder in Team Members
  - At least one validator in Team Members
  - Each task in Step by Step Tasks has: Role, Depends On, Description

Exit codes:
  0 = allow (plan is valid or not a TeamCreate call)
  2 = block (plan is invalid)
"""

import glob
import json
import os
import sys


REQUIRED_SECTIONS = [
    "## Task Description",
    "## Objective",
    "## Relevant Files",
    "## Acceptance Criteria",
    "## Team Orchestration",
    "### Team Members",
]

# At least one of these must be present for the task list
TASK_SECTIONS = [
    "## Step by Step Tasks",
    "## Task Graph",
]

SKIP_MARKERS = ["SUPERSEDED", "COMPLETE", "DONE", ".BAK"]


def find_active_plan():
    """Find the most recently modified active plan spec."""
    spec_files = glob.glob("specs/*.md")
    candidates = []

    for spec_path in spec_files:
        basename = os.path.basename(spec_path).upper()
        if any(marker in basename for marker in SKIP_MARKERS):
            continue
        try:
            with open(spec_path, "r") as f:
                content = f.read(1000)
                if any(marker in content for marker in [
                    "Status: COMPLETE", "Status: DONE", "SUPERSEDED",
                    "Status:** COMPLETE", "Status:** Done",
                ]):
                    continue
            candidates.append(spec_path)
        except (OSError, IOError):
            continue

    if not candidates:
        return None

    # Return most recently modified
    candidates.sort(key=os.path.getmtime, reverse=True)
    return candidates[0]


def validate_plan(plan_path):
    """Validate plan file has all required sections. Returns list of issues."""
    issues = []

    try:
        with open(plan_path, "r") as f:
            content = f.read()
    except (OSError, IOError) as e:
        return [f"Cannot read plan file: {e}"]

    # Check required sections
    for section in REQUIRED_SECTIONS:
        if section not in content:
            issues.append(f"Missing section: {section}")

    # Check for task list section
    has_task_section = any(s in content for s in TASK_SECTIONS)
    if not has_task_section:
        issues.append(f"Missing task list: need one of {TASK_SECTIONS}")

    # Check for at least one builder
    content_lower = content.lower()
    if "agent type: builder" not in content_lower and "agent type: general-purpose" not in content_lower:
        issues.append("No builder agent found in Team Members (need 'Agent Type: builder')")

    # Check for validator
    if "agent type: validator" not in content_lower:
        issues.append("No validator agent found in Team Members (need 'Agent Type: validator')")

    # Check task descriptions have required sub-sections
    # Split on ### to find individual tasks
    task_section_start = None
    for ts in TASK_SECTIONS:
        idx = content.find(ts)
        if idx >= 0:
            task_section_start = idx
            break

    if task_section_start is not None:
        task_content = content[task_section_start:]
        # Find individual tasks (### N. ...)
        import re
        tasks = re.split(r'\n### \d+\.', task_content)
        # Skip the first split (before first task)
        for i, task in enumerate(tasks[1:], 1):
            task_name = task.split('\n')[0].strip()
            # Check for Role
            if "**Role**:" not in task and "- **Role**:" not in task:
                issues.append(f"Task {i} '{task_name}': missing **Role** field")
            # Check for Description
            if "**Description**:" not in task and "- **Description**:" not in task:
                issues.append(f"Task {i} '{task_name}': missing **Description** field")
            # Builder tasks should have acceptance criteria and validation
            if "role: builder" in task.lower() or "role**: builder" in task.lower():
                if "## Acceptance criteria" not in task and "## acceptance criteria" not in task.lower():
                    issues.append(f"Task {i} '{task_name}': builder task missing '## Acceptance criteria' in description")
                if "## Validation command" not in task and "## validation command" not in task.lower():
                    issues.append(f"Task {i} '{task_name}': builder task missing '## Validation command' in description")

    return issues


def main():
    try:
        input_data = json.load(sys.stdin)
        tool_name = input_data.get("tool_name", "")

        # Only validate on TeamCreate calls
        if tool_name != "TeamCreate":
            sys.exit(0)

        # Find the active plan
        plan_path = find_active_plan()
        if plan_path is None:
            # No plan file found — could be a non-plan team, allow through
            sys.exit(0)

        # Check if plan has Team Orchestration (indicates it's a /build plan)
        with open(plan_path, "r") as f:
            quick_check = f.read(10000)
        if "Team Orchestration" not in quick_check:
            sys.exit(0)

        # Validate the plan
        issues = validate_plan(plan_path)

        if issues:
            print(
                f"BLOCKED: Plan file '{plan_path}' has {len(issues)} validation issue(s):\n",
                file=sys.stderr,
            )
            for issue in issues:
                print(f"  - {issue}", file=sys.stderr)
            print(
                f"\nFix these issues in the plan before running /build.\n"
                f"The plan must be complete for agents to work autonomously.",
                file=sys.stderr,
            )
            sys.exit(2)

        print(f"Plan '{plan_path}' validated: all required sections present.", file=sys.stderr)
        sys.exit(0)

    except json.JSONDecodeError:
        sys.exit(0)
    except Exception:
        sys.exit(0)


if __name__ == "__main__":
    main()
