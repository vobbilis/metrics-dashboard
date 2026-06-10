#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.8"
# ///

"""
PreToolUse hook: Requires TeamCreate before launching Task agents
when a plan_w_team spec exists.

Rules:
1. If specs/*.md contains "Team Orchestration" AND no team marker exists
   → BLOCK Task calls with: "Call TeamCreate first"
2. If a team is active AND Task is called without team_name parameter
   → BLOCK with: "Include team_name in your Task call"

This prevents the lead from launching anonymous background agents
instead of proper team members.

Exit codes:
  0 = allow
  2 = block
"""

import json
import os
import sys
import glob

MARKER_FILE = os.path.expanduser("~/.claude/.team_lead_session")


def has_team_spec() -> bool:
    """Check if any ACTIVE spec file contains a Team Orchestration section.

    Skips specs that are completed/superseded by checking for:
    - Filename contains 'SUPERSEDED' or 'COMPLETE'
    - File starts with 'SUPERSEDED', 'COMPLETE', or 'DONE'
    - File contains '## Status: Complete' or '## Status: Done'
    - .bak extension
    """
    spec_files = glob.glob("specs/*.md")
    for spec_path in spec_files:
        basename = os.path.basename(spec_path).upper()
        # Skip files that look completed/superseded by name
        if any(marker in basename for marker in ["SUPERSEDED", "COMPLETE", "DONE", ".BAK"]):
            continue
        try:
            with open(spec_path, "r") as f:
                content = f.read(10000)  # Read first 10KB
                # Skip files marked complete/done in content
                if any(marker in content for marker in [
                    "## Status: Complete",
                    "## Status: Done",
                    "Status: COMPLETE",
                    "Status: DONE",
                    "Status:** COMPLETE",
                    "Status:** Done",
                    "SUPERSEDED",
                ]):
                    continue
                if "Team Orchestration" in content or "## Team Members" in content:
                    return True
        except (OSError, IOError):
            continue
    return False


def team_is_active() -> bool:
    """Check if a team has been created (marker file exists)."""
    return os.path.exists(MARKER_FILE)


def get_team_name() -> str:
    """Get the active team name from the marker file."""
    try:
        with open(MARKER_FILE) as f:
            marker = json.load(f)
            return marker.get("team_name", "")
    except (json.JSONDecodeError, OSError):
        return ""


def main():
    try:
        input_data = json.load(sys.stdin)
        tool_name = input_data.get("tool_name", "")
        tool_input = input_data.get("tool_input", {})
        session_id = input_data.get("session_id", "")

        # Only intercept Task tool calls
        if tool_name != "Task":
            sys.exit(0)

        # Bug pipeline manages its own Task lifecycle — allow through
        bug_pipeline_state = os.path.expanduser("~/.claude/.bug_pipeline_state")
        if os.path.exists(bug_pipeline_state):
            sys.exit(0)

        # Check if current session is the lead
        if os.path.exists(MARKER_FILE):
            try:
                with open(MARKER_FILE) as f:
                    marker = json.load(f)
                lead_session_id = marker.get("lead_session_id", "")
                # If this is NOT the lead session, allow (subagent spawning sub-tasks)
                if session_id != lead_session_id:
                    sys.exit(0)
            except (json.JSONDecodeError, OSError):
                pass

        # Rule 1: Team spec exists but no TeamCreate was called
        if has_team_spec() and not team_is_active():
            print(
                "BLOCKED: A plan_w_team spec exists in specs/ but no team has been created.\n"
                "You MUST call TeamCreate first before launching any Task agents.\n"
                "The spec defines team members — use them.\n\n"
                "Required steps:\n"
                "  1. TeamCreate with team_name from the spec\n"
                "  2. Task with team_name parameter for each team member\n"
                "  3. Never use Task without team_name when a team spec exists",
                file=sys.stderr,
            )
            sys.exit(2)

        # Rule 2: Team is active but Task is missing team_name
        if team_is_active():
            team_name_param = tool_input.get("team_name", "")
            if not team_name_param:
                active_team = get_team_name()
                print(
                    f"BLOCKED: Team '{active_team}' is active but your Task call is missing team_name.\n"
                    f"Add team_name='{active_team}' to your Task call to spawn a proper team member.\n"
                    f"Anonymous background agents are not allowed when a team is active.",
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
