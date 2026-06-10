#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.8"
# ///

"""
PreToolUse hook: Blocks the team LEAD from directly writing code.

When a team is active (marker file exists from TeamCreate), the lead
session is BLOCKED from using Write, Edit, NotebookEdit, and file-writing
Bash commands. Subagents (different session_id) are allowed through.

This enforces the plan_w_team contract: the lead orchestrates, team
members build.

Exit codes:
  0 = allow
  2 = block (shows error to Claude)
"""

import json
import os
import sys

MARKER_FILE = os.path.expanduser("~/.claude/.team_lead_session")

# Tools the lead must NOT use directly
BLOCKED_TOOLS = {"Write", "Edit", "NotebookEdit", "MultiEdit"}

# Bash patterns that indicate file creation/modification
BASH_WRITE_PATTERNS = [
    "cat >", "cat <<", "echo >", "echo >>",
    "printf >", "printf >>",
    "tee ", "> /", ">> /",
]


def is_file_writing_bash(command: str) -> bool:
    """Check if a Bash command writes files."""
    lower = command.lower().strip()
    for pattern in BASH_WRITE_PATTERNS:
        if pattern in lower:
            return True
    return False


def main():
    try:
        input_data = json.load(sys.stdin)
        tool_name = input_data.get("tool_name", "")
        tool_input = input_data.get("tool_input", {})
        session_id = input_data.get("session_id", "")

        # No marker file → no active team → allow everything
        if not os.path.exists(MARKER_FILE):
            sys.exit(0)

        # Read the marker to get the lead's session_id
        try:
            with open(MARKER_FILE) as f:
                marker = json.load(f)
        except (json.JSONDecodeError, OSError):
            sys.exit(0)  # Corrupt marker → fail open

        lead_session_id = marker.get("lead_session_id", "")
        team_name = marker.get("team_name", "unknown")

        # If current session is NOT the lead → allow (it's a team member/subagent)
        if session_id != lead_session_id:
            sys.exit(0)

        # Current session IS the lead — check if the tool is blocked
        if tool_name in BLOCKED_TOOLS:
            file_path = tool_input.get("file_path", "")
            # Allow editing hook/config files (the lead may need to configure things)
            if file_path and ("/.claude/" in file_path or "/specs/" in file_path):
                sys.exit(0)

            print(
                f"BLOCKED: You are the team LEAD for '{team_name}'. "
                f"You cannot use {tool_name} directly.\n"
                f"Deploy a team member via Task tool with team_name='{team_name}' to do this work.\n"
                f"If you need to override this, delete ~/.claude/.team_lead_session first.",
                file=sys.stderr,
            )
            sys.exit(2)

        if tool_name == "Bash":
            command = tool_input.get("command", "")
            if is_file_writing_bash(command):
                # Allow writes to pipeline state and bug artifacts (operational, not code)
                if any(p in command for p in ["/.claude/", "bugs/", "verdict.json", "routing.json", "pipeline_state"]):
                    sys.exit(0)
                print(
                    f"BLOCKED: Team lead for '{team_name}' cannot write files via Bash.\n"
                    f"Delegate file creation to a builder team member.\n"
                    f"Allowed Bash: git, npm, cargo, ls, test commands, etc.",
                    file=sys.stderr,
                )
                sys.exit(2)

        # All other tools (Task, TaskCreate, TaskUpdate, SendMessage, Read, Glob, Grep, etc.) → allow
        sys.exit(0)

    except json.JSONDecodeError:
        sys.exit(0)
    except Exception:
        sys.exit(0)


if __name__ == "__main__":
    main()
