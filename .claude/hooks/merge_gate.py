#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///

"""
PreToolUse hook: Merge gate requiring dual reviewer approval.

Fast-path: only activates when tool_name is Bash and command contains "gh pr merge".

Reads both review files (alpha.md and beta.md) and requires:
- BOTH must contain "## Verdict: APPROVE"
- BOTH must contain "## Test Evidence Reviewed: YES"

If either is missing, rejected, or lacks test evidence confirmation, blocks the merge.

Exit codes:
  0 = allow (both reviewers approve)
  2 = block (merge conditions not met)
"""

import json
import logging
import os
import sys
from pathlib import Path

# Logging setup - log file next to this script (wrapped to prevent crash)
try:
    SCRIPT_DIR = Path(__file__).parent
    LOG_FILE = SCRIPT_DIR / "merge_gate.log"
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
REQUIRED_VERDICT = "## Verdict: APPROVE"
REQUIRED_TEST_EVIDENCE = "## Test Evidence Reviewed: YES"


def check_review_file(filepath: str) -> tuple[bool, bool, bool]:
    """
    Check a review file for approval and test evidence.

    Returns:
        tuple: (file_exists, has_approval, has_test_evidence)
    """
    if not os.path.exists(filepath):
        return False, False, False

    try:
        content = Path(filepath).read_text(encoding='utf-8')
    except (OSError, UnicodeDecodeError):
        return True, False, False

    has_approval = REQUIRED_VERDICT in content
    has_test_evidence = REQUIRED_TEST_EVIDENCE in content

    # Also check for explicit REJECT
    if "## Verdict: REJECT" in content:
        has_approval = False

    return True, has_approval, has_test_evidence


def main():
    """Main entry point."""
    try:
        input_data = json.load(sys.stdin)
        tool_name = input_data.get("tool_name", "")
        tool_input = input_data.get("tool_input", {})

        # Fast-path: only activate for Bash commands containing "gh pr merge"
        if tool_name != "Bash":
            sys.exit(0)

        command = tool_input.get("command", "")
        if "gh pr merge" not in command:
            sys.exit(0)

        logger.info(f"Merge gate activated for command: {command[:100]}")

        # Read pipeline state for current bug_id
        if not os.path.exists(PIPELINE_STATE):
            logger.warning("No pipeline state, allowing merge (fail-open)")
            sys.exit(0)

        try:
            with open(PIPELINE_STATE) as f:
                state = json.load(f)
        except (json.JSONDecodeError, OSError) as e:
            logger.warning(f"Failed to read pipeline state: {e} (fail-open)")
            sys.exit(0)

        bug_id = state.get("bug_id", "")
        if not bug_id:
            logger.warning("No bug_id in pipeline state, allowing merge (fail-open)")
            sys.exit(0)

        # Check both review files
        alpha_path = f"bugs/{bug_id}/reviews/alpha.md"
        beta_path = f"bugs/{bug_id}/reviews/beta.md"

        logger.info(f"Checking reviews for bug {bug_id}")
        logger.info(f"  Alpha: {alpha_path}")
        logger.info(f"  Beta: {beta_path}")

        alpha_exists, alpha_approved, alpha_evidence = check_review_file(alpha_path)
        beta_exists, beta_approved, beta_evidence = check_review_file(beta_path)

        logger.info(
            f"  Alpha: exists={alpha_exists}, approved={alpha_approved}, "
            f"evidence={alpha_evidence}"
        )
        logger.info(
            f"  Beta: exists={beta_exists}, approved={beta_approved}, "
            f"evidence={beta_evidence}"
        )

        # Build detailed failure reasons
        reasons = []

        if not alpha_exists:
            reasons.append(f"Alpha review file missing: {alpha_path}")
        elif not alpha_approved:
            reasons.append(
                f"Alpha review does not contain '{REQUIRED_VERDICT}' "
                f"(may be REJECT or missing verdict)"
            )
        if alpha_exists and not alpha_evidence:
            reasons.append(
                f"Alpha review does not contain '{REQUIRED_TEST_EVIDENCE}'"
            )

        if not beta_exists:
            reasons.append(f"Beta review file missing: {beta_path}")
        elif not beta_approved:
            reasons.append(
                f"Beta review does not contain '{REQUIRED_VERDICT}' "
                f"(may be REJECT or missing verdict)"
            )
        if beta_exists and not beta_evidence:
            reasons.append(
                f"Beta review does not contain '{REQUIRED_TEST_EVIDENCE}'"
            )

        if reasons:
            reason_text = "\n".join(f"  - {r}" for r in reasons)
            msg = (
                f"MERGE BLOCKED for bug {bug_id}:\n{reason_text}\n\n"
                f"Both reviewers must approve AND confirm test evidence review "
                f"before merge is allowed.\n"
                f"Required in each review file:\n"
                f"  - {REQUIRED_VERDICT}\n"
                f"  - {REQUIRED_TEST_EVIDENCE}"
            )
            logger.warning(f"BLOCKED: {msg}")
            print(msg, file=sys.stderr)
            sys.exit(2)

        # Both approved with test evidence
        logger.info(f"PASS: Both reviewers approved bug {bug_id}, merge allowed")
        sys.exit(0)

    except json.JSONDecodeError:
        sys.exit(0)
    except Exception as e:
        logger.exception(f"Merge gate error: {e}")
        sys.exit(0)  # Fail open


if __name__ == "__main__":
    main()
