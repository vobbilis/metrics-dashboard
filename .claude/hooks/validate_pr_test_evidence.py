#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///

"""
Stop hook: Validates that the most recent PR contains test evidence.

Checks:
1. Gets most recent open PR via gh CLI
2. Checks PR body contains ## Test Evidence section
3. Validates section has actual test output (not placeholder)

Exit codes:
- 0: Validation passed
- 1: Validation failed

Usage:
  uv run validate_pr_test_evidence.py
"""

import json
import logging
import re
import subprocess
import sys
from pathlib import Path

# Logging setup - log file next to this script (wrapped to prevent crash)
try:
    SCRIPT_DIR = Path(__file__).parent
    LOG_FILE = SCRIPT_DIR / "validate_pr_test_evidence.log"
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[logging.FileHandler(LOG_FILE, mode='a')]
    )
except Exception:
    logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Test output patterns (case-insensitive)
TEST_OUTPUT_PATTERNS = [
    r"PASSED",
    r"FAILED",
    r"tests?\s+ran",
    r"\bok\b",
    r"test\s+suites?",
    r"assertions?",
    r"\d+\s+passing",
    r"\d+\s+failing",
    r"Tests:\s+\d+",
    r"PASS\s",
    r"FAIL\s",
    r"test result:",
]

# Placeholder patterns to reject
PLACEHOLDER_PATTERNS = [
    r"TODO",
    r"TBD",
    r"add test.*here",
    r"paste test.*here",
    r"insert test.*here",
    r"will add.*later",
]

NO_PR_ERROR = (
    "VALIDATION FAILED: No open pull request found.\n\n"
    "ACTION REQUIRED: Create a pull request with test evidence before proceeding."
)

NO_SECTION_ERROR = (
    "VALIDATION FAILED: PR #{number} is missing '## Test Evidence' section.\n\n"
    "ACTION REQUIRED: Edit the PR body to include a '## Test Evidence' section "
    "with actual test output from running the test suite."
)

PLACEHOLDER_ERROR = (
    "VALIDATION FAILED: PR #{number} has a '## Test Evidence' section but it "
    "contains placeholder text instead of actual test output.\n\n"
    "ACTION REQUIRED: Run the test suite and paste the actual output into the "
    "'## Test Evidence' section of the PR body."
)

NO_OUTPUT_ERROR = (
    "VALIDATION FAILED: PR #{number} has a '## Test Evidence' section but it "
    "does not contain recognizable test output.\n\n"
    "ACTION REQUIRED: Run the test suite (pytest, jest, cargo test, etc.) "
    "and paste the raw output into the '## Test Evidence' section."
)


def get_latest_pr() -> dict | None:
    """Get the most recent open PR via gh CLI."""
    try:
        result = subprocess.run(
            ["gh", "pr", "list", "--state", "open", "--json", "number,body", "--limit", "1"],
            capture_output=True,
            text=True,
            timeout=15
        )
        if result.returncode != 0:
            logger.warning(f"gh pr list failed: {result.stderr}")
            return None

        prs = json.loads(result.stdout)
        if not prs:
            return None

        return prs[0]
    except (subprocess.TimeoutExpired, subprocess.SubprocessError, json.JSONDecodeError) as e:
        logger.warning(f"Failed to get PRs: {e}")
        return None


def extract_test_evidence_section(body: str) -> str | None:
    """Extract the ## Test Evidence section content from PR body."""
    # Match ## Test Evidence and capture until the next ## heading or end of string
    match = re.search(
        r"##\s+Test\s+Evidence\s*\n(.*?)(?=\n##\s|\Z)",
        body,
        re.DOTALL | re.IGNORECASE
    )
    if match:
        return match.group(1).strip()
    return None


def main():
    """Main entry point."""
    logger.info("=" * 60)
    logger.info("Validator started: validate_pr_test_evidence")

    try:
        # Read hook input from stdin
        try:
            input_data = json.load(sys.stdin)
            logger.info(f"Stdin input received: {len(json.dumps(input_data))} bytes")
        except (json.JSONDecodeError, EOFError):
            input_data = {}
            logger.info("No stdin input or invalid JSON")

        # Get latest PR
        pr = get_latest_pr()

        if not pr:
            logger.warning("FAIL: No open PR found")
            result = {"result": "block", "reason": NO_PR_ERROR}
            print(json.dumps(result))
            sys.exit(1)

        pr_number = pr.get("number", "?")
        body = pr.get("body", "")
        logger.info(f"Checking PR #{pr_number} ({len(body)} chars)")

        # Check for ## Test Evidence section
        evidence_section = extract_test_evidence_section(body)

        if evidence_section is None:
            msg = NO_SECTION_ERROR.format(number=pr_number)
            logger.warning(f"FAIL: No Test Evidence section in PR #{pr_number}")
            result = {"result": "block", "reason": msg}
            print(json.dumps(result))
            sys.exit(1)

        logger.info(f"Test Evidence section found ({len(evidence_section)} chars)")

        # Check for placeholder text
        for pattern in PLACEHOLDER_PATTERNS:
            if re.search(pattern, evidence_section, re.IGNORECASE):
                msg = PLACEHOLDER_ERROR.format(number=pr_number)
                logger.warning(f"FAIL: Placeholder text detected in PR #{pr_number}")
                result = {"result": "block", "reason": msg}
                print(json.dumps(result))
                sys.exit(1)

        # Check for actual test output patterns
        found_patterns = []
        for pattern in TEST_OUTPUT_PATTERNS:
            if re.search(pattern, evidence_section, re.IGNORECASE):
                found_patterns.append(pattern)

        if not found_patterns:
            msg = NO_OUTPUT_ERROR.format(number=pr_number)
            logger.warning(f"FAIL: No test output patterns in PR #{pr_number}")
            result = {"result": "block", "reason": msg}
            print(json.dumps(result))
            sys.exit(1)

        # All checks passed
        msg = (
            f"PR #{pr_number} test evidence validated: "
            f"{len(found_patterns)} test output patterns matched"
        )
        logger.info(f"PASS: {msg}")
        result = {"result": "continue", "message": msg}
        print(json.dumps(result))
        sys.exit(0)

    except Exception as e:
        logger.exception(f"Validation error: {e}")
        print(json.dumps({
            "result": "continue",
            "message": f"Validation error (allowing through): {str(e)}"
        }))
        sys.exit(0)


if __name__ == "__main__":
    main()
