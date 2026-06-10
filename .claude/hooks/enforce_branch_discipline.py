#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.8"
# ///

"""
PreToolUse hook: Enforces branch discipline — no commits or pushes to main/master.

Blocks:
  - `git commit` while on main or master branch
  - `git push` to main or master (including `git push origin main`)
  - `git merge` into main/master (while on those branches)

Allows:
  - All git operations on feature branches
  - `git checkout`, `git branch`, `git switch` (branch management)
  - `git push -u origin <branch>` for feature branches
  - `gh pr merge` (handled by merge_gate.py, not this hook)

Exit codes:
  0 = allow
  2 = block (shows error to Claude)
"""

import json
import os
import re
import subprocess
import sys


PROTECTED_BRANCHES = {"main", "master"}
BYPASS_FILE = os.path.expanduser("~/.claude/.branch_discipline_bypass")


def get_current_branch() -> str:
    """Get the current git branch name."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        return result.stdout.strip() if result.returncode == 0 else ""
    except Exception:
        return ""


def is_commit_command(command: str) -> bool:
    """Check if command is a git commit."""
    # Match: git commit, git commit -m, git commit -am, etc.
    return bool(re.search(r'\bgit\s+commit\b', command))


def is_push_to_protected(command: str) -> bool:
    """Check if command pushes to a protected branch."""
    # Match: git push (no args = pushes current branch)
    # Match: git push origin main, git push origin master
    # Match: git push --force origin main
    if not re.search(r'\bgit\s+push\b', command):
        return False

    # Check if explicitly pushing to a protected branch
    for branch in PROTECTED_BRANCHES:
        # git push origin main, git push --force origin main
        if re.search(rf'\bgit\s+push\b.*\b{branch}\b', command):
            return True

    # git push with no branch specified → pushes current branch
    # If current branch is protected, block it
    if not re.search(r'\bgit\s+push\b.*\b(origin|upstream)\s+\S+', command):
        current = get_current_branch()
        if current in PROTECTED_BRANCHES:
            return True

    return False


def is_merge_on_protected(command: str) -> bool:
    """Check if command is git merge while on a protected branch."""
    if not re.search(r'\bgit\s+merge\b', command):
        return False
    current = get_current_branch()
    return current in PROTECTED_BRANCHES


def is_reset_on_protected(command: str) -> bool:
    """Check if command is git reset --hard while on a protected branch."""
    if not re.search(r'\bgit\s+reset\s+--hard\b', command):
        return False
    current = get_current_branch()
    return current in PROTECTED_BRANCHES


def is_allowed_exception(command: str) -> bool:
    """Check for commands that should be allowed even on protected branches."""
    # Allow gh pr merge (handled by merge_gate.py)
    if "gh pr merge" in command:
        return True
    # Allow git pull on main (updating local)
    if re.search(r'\bgit\s+pull\b', command):
        return True
    # Allow git fetch
    if re.search(r'\bgit\s+fetch\b', command):
        return True
    # Allow git push --force-with-lease for retroactive branch fixes
    # (but still block regular push to main)
    return False


def main():
    try:
        input_data = json.load(sys.stdin)
        tool_name = input_data.get("tool_name", "")
        tool_input = input_data.get("tool_input", {})

        # Only check Bash commands
        if tool_name != "Bash":
            sys.exit(0)

        command = tool_input.get("command", "")
        if not command:
            sys.exit(0)

        # Admin bypass: touch ~/.claude/.branch_discipline_bypass to temporarily disable
        if os.path.exists(BYPASS_FILE):
            sys.exit(0)

        # Check allowed exceptions first
        if is_allowed_exception(command):
            sys.exit(0)

        current_branch = get_current_branch()

        # Block: git commit on protected branch
        if is_commit_command(command) and current_branch in PROTECTED_BRANCHES:
            print(
                f"BLOCKED: Cannot commit directly to '{current_branch}'.\n"
                f"Create a feature branch first:\n"
                f"  git checkout -b fix/<description>\n"
                f"  git checkout -b feat/<description>\n\n"
                f"All changes must go through PRs. Direct commits to "
                f"{'/'.join(PROTECTED_BRANCHES)} are forbidden.",
                file=sys.stderr,
            )
            sys.exit(2)

        # Block: git push to protected branch
        if is_push_to_protected(command):
            print(
                f"BLOCKED: Cannot push directly to '{current_branch}'.\n"
                f"Push to a feature branch and create a PR instead:\n"
                f"  git push -u origin <feature-branch>\n"
                f"  gh pr create\n\n"
                f"Direct pushes to {'/'.join(PROTECTED_BRANCHES)} are forbidden.",
                file=sys.stderr,
            )
            sys.exit(2)

        # Block: git merge into protected branch
        if is_merge_on_protected(command):
            print(
                f"BLOCKED: Cannot merge directly into '{current_branch}'.\n"
                f"Use a PR workflow instead:\n"
                f"  gh pr create → gh pr merge\n\n"
                f"Direct merges into {'/'.join(PROTECTED_BRANCHES)} are forbidden.",
                file=sys.stderr,
            )
            sys.exit(2)

        # Block: git reset --hard on protected branch
        if is_reset_on_protected(command):
            print(
                f"BLOCKED: Cannot reset --hard on '{current_branch}'.\n"
                f"This is a destructive operation on a protected branch.\n"
                f"Use git revert instead, or work on a feature branch.",
                file=sys.stderr,
            )
            sys.exit(2)

        # All other commands → allow
        sys.exit(0)

    except json.JSONDecodeError:
        sys.exit(0)
    except Exception:
        sys.exit(0)  # Fail open


if __name__ == "__main__":
    main()
