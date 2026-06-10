#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///

"""
PreToolUse hook: Enforces review isolation between alpha and beta reviewers.

Fast-path: if ~/.claude/.bug_pipeline_state doesn't exist, exit 0 immediately.

When tool_name is Read and file_path matches the OTHER reviewer's review file,
blocks the access (exit 2).

Identification: checks session_id from stdin against reviewer session IDs
in pipeline state. If session matches reviewer-alpha, block reads to beta.md
and vice versa.

Exit codes:
  0 = allow
  2 = block (shows error to Claude)
"""

import json
import logging
import os
import sys
from pathlib import Path

# Logging setup - log file next to this script (wrapped to prevent crash)
try:
    SCRIPT_DIR = Path(__file__).parent
    LOG_FILE = SCRIPT_DIR / "enforce_review_isolation.log"
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[logging.FileHandler(LOG_FILE, mode='a')]
    )
except Exception:
    logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants
PIPELINE_STATE = os.path.expanduser("~/.claude/.bug_pipeline_state")


def main():
    """Main entry point."""
    try:
        # Fast-path: no pipeline state → allow everything
        if not os.path.exists(PIPELINE_STATE):
            sys.exit(0)

        input_data = json.load(sys.stdin)
        tool_name = input_data.get("tool_name", "")
        tool_input = input_data.get("tool_input", {})
        session_id = input_data.get("session_id", "")

        # Fast-path: only care about Read tool
        if tool_name != "Read":
            sys.exit(0)

        file_path = tool_input.get("file_path", "")

        # Fast-path: only care about review files
        if "/reviews/" not in file_path:
            sys.exit(0)

        logger.info(f"Review isolation check: session={session_id[:12]}... file={file_path}")

        # Read pipeline state
        try:
            with open(PIPELINE_STATE) as f:
                state = json.load(f)
        except (json.JSONDecodeError, OSError):
            logger.warning("Failed to read pipeline state, allowing through")
            sys.exit(0)

        reviewers = state.get("reviewers", {})
        if not reviewers:
            sys.exit(0)

        alpha_session = reviewers.get("alpha", {}).get("session_id", "")
        beta_session = reviewers.get("beta", {}).get("session_id", "")

        # Determine which reviewer this session is
        if session_id == alpha_session:
            # Alpha reviewer — block reads to beta.md
            if file_path.endswith("beta.md") or "/beta.md" in file_path:
                logger.warning(
                    f"BLOCKED: Reviewer alpha (session {session_id[:12]}...) "
                    f"attempted to read beta review: {file_path}"
                )
                print(
                    f"BLOCKED: Review isolation enforced. As reviewer-alpha, "
                    f"you cannot read the beta reviewer's file ({file_path}). "
                    f"Reviews must remain independent until the merge gate.",
                    file=sys.stderr,
                )
                sys.exit(2)

        elif session_id == beta_session:
            # Beta reviewer — block reads to alpha.md
            if file_path.endswith("alpha.md") or "/alpha.md" in file_path:
                logger.warning(
                    f"BLOCKED: Reviewer beta (session {session_id[:12]}...) "
                    f"attempted to read alpha review: {file_path}"
                )
                print(
                    f"BLOCKED: Review isolation enforced. As reviewer-beta, "
                    f"you cannot read the alpha reviewer's file ({file_path}). "
                    f"Reviews must remain independent until the merge gate.",
                    file=sys.stderr,
                )
                sys.exit(2)

        # Not a reviewer or no conflict → allow
        sys.exit(0)

    except json.JSONDecodeError:
        sys.exit(0)
    except Exception as e:
        logger.exception(f"Error in review isolation hook: {e}")
        sys.exit(0)  # Fail open


if __name__ == "__main__":
    main()
