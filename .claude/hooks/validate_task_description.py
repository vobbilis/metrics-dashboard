#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.8"
# ///

"""
PreToolUse hook: Validates TaskCreate descriptions have required sections.

Triggered on TaskCreate calls when a team is active (i.e., during /build).
Ensures builder task descriptions contain acceptance criteria and validation
commands, so agents have clear success criteria.

Rules:
  1. Builder tasks (description starts with "role: builder") MUST contain:
     - "## Acceptance criteria" or "## acceptance criteria"
     - "## Validation command" or "## validation command"
     - "## Files to modify" or "## New files to create" or "## files to"
  2. Validator tasks (description starts with "role: validator") MUST contain:
     - "## Validation Commands" or "## validation commands"
     - "## Acceptance Criteria" or "## acceptance criteria"
  3. Spec-updater tasks (description starts with "role: spec-updater") MUST contain:
     - "## Spec File" — path to the spec file to update
     - "## Instructions" — what evidence to write
  4. All tasks MUST have a non-empty description starting with "role: builder",
     "role: validator", or "role: spec-updater"

Only enforced when a team is active (team lead marker exists).
Skips enforcement for fix tasks created by the validator (contain "fix_cycle").

Exit codes:
  0 = allow
  2 = block (description missing required sections)
"""

import json
import os
import sys

MARKER_FILE = os.path.expanduser("~/.claude/.team_lead_session")

BUILDER_REQUIRED = [
    ("acceptance criteria", ["## Acceptance criteria", "## acceptance criteria", "## Acceptance Criteria"]),
    ("validation command", ["## Validation command", "## validation command", "## Validation Command"]),
]

VALIDATOR_REQUIRED = [
    ("validation commands", ["## Validation Commands", "## validation commands", "## Validation commands"]),
    ("acceptance criteria", ["## Acceptance Criteria", "## acceptance criteria", "## Acceptance criteria"]),
]


def check_contains_any(text, alternatives):
    """Check if text contains any of the alternative strings."""
    text_lower = text.lower()
    for alt in alternatives:
        if alt.lower() in text_lower:
            return True
    return False


def main():
    try:
        input_data = json.load(sys.stdin)
        tool_name = input_data.get("tool_name", "")
        tool_input = input_data.get("tool_input", {})

        # Only validate TaskCreate calls
        if tool_name != "TaskCreate":
            sys.exit(0)

        # Only enforce when a team is active
        if not os.path.exists(MARKER_FILE):
            sys.exit(0)

        description = tool_input.get("description", "")
        subject = tool_input.get("subject", "")

        if not description:
            print(
                f"BLOCKED: TaskCreate for '{subject}' has an empty description.\n"
                f"Task descriptions must be exhaustive for autonomous agent execution.",
                file=sys.stderr,
            )
            sys.exit(2)

        # Skip validation for fix tasks created by the validator
        if "fix_cycle" in description.lower() or "fix task" in subject.lower():
            sys.exit(0)

        description_stripped = description.strip()

        # Check for role prefix
        valid_roles = ("role: builder", "role: validator", "role: spec-updater")
        if not any(description_stripped.startswith(r) for r in valid_roles):
            print(
                f"BLOCKED: TaskCreate for '{subject}' description must start with "
                f"'role: builder', 'role: validator', or 'role: spec-updater'.\n"
                f"This prefix tells agents which tasks to claim.\n"
                f"Got: '{description_stripped[:50]}...'",
                file=sys.stderr,
            )
            sys.exit(2)

        # Validate builder tasks
        if description_stripped.startswith("role: builder"):
            missing = []
            for name, alternatives in BUILDER_REQUIRED:
                if not check_contains_any(description, alternatives):
                    missing.append(name)

            if missing:
                print(
                    f"BLOCKED: Builder task '{subject}' description is missing required sections:\n",
                    file=sys.stderr,
                )
                for m in missing:
                    print(f"  - {m}", file=sys.stderr)
                print(
                    f"\nBuilder task descriptions must include acceptance criteria and "
                    f"validation commands so agents know when they're done.",
                    file=sys.stderr,
                )
                sys.exit(2)

        # Validate validator tasks
        if description_stripped.startswith("role: validator"):
            missing = []
            for name, alternatives in VALIDATOR_REQUIRED:
                if not check_contains_any(description, alternatives):
                    missing.append(name)

            if missing:
                print(
                    f"BLOCKED: Validator task '{subject}' description is missing required sections:\n",
                    file=sys.stderr,
                )
                for m in missing:
                    print(f"  - {m}", file=sys.stderr)
                print(
                    f"\nValidator task descriptions must include validation commands "
                    f"and acceptance criteria to check.",
                    file=sys.stderr,
                )
                sys.exit(2)

        # Validate spec-updater tasks
        if description_stripped.startswith("role: spec-updater"):
            spec_updater_required = [
                ("spec file", ["## Spec File", "## spec file", "## Spec file"]),
                ("instructions", ["## Instructions", "## instructions"]),
            ]
            missing = []
            for name, alternatives in spec_updater_required:
                if not check_contains_any(description, alternatives):
                    missing.append(name)

            if missing:
                print(
                    f"BLOCKED: Spec-updater task '{subject}' description is missing required sections:\n",
                    file=sys.stderr,
                )
                for m in missing:
                    print(f"  - {m}", file=sys.stderr)
                print(
                    f"\nSpec-updater task descriptions must include the spec file path "
                    f"and instructions for writing evidence.",
                    file=sys.stderr,
                )
                sys.exit(2)

        sys.exit(0)

    except json.JSONDecodeError:
        sys.exit(0)
    except Exception:
        sys.exit(0)


if __name__ == "__main__":
    main()
