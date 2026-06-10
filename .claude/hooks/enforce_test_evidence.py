#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///

"""
Stop hook: Validates that test evidence exists for the current bug fix.

Checks:
1. Reads ~/.claude/.bug_pipeline_state for current bug_id
2. Checks bugs/{BUG-ID}/test-results.md exists and is non-empty
3. Validates content contains actual test output patterns

Exit codes:
- 0: Validation passed (test evidence found)
- 1: Validation failed (no test evidence)

Usage:
  uv run enforce_test_evidence.py
"""

import json
import logging
import os
import re
import sys
from pathlib import Path

# Logging setup - log file next to this script (wrapped to prevent crash)
try:
    SCRIPT_DIR = Path(__file__).parent
    LOG_FILE = SCRIPT_DIR / "enforce_test_evidence.log"
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

# Patterns that indicate real test output (case-insensitive)
TEST_OUTPUT_PATTERNS = [
    r"PASSED",
    r"FAILED",
    r"tests?\s+ran",
    r"\bok\b",
    r"test\s+suites?",
    r"assertions?",
    r"tests?\s+passed",
    r"tests?\s+failed",
    r"\d+\s+passing",
    r"\d+\s+failing",
    r"Tests:\s+\d+",
    r"PASS\s",
    r"FAIL\s",
    r"✓",
    r"✗",
    r"test result:",
]

NO_STATE_ERROR = (
    "VALIDATION FAILED: No bug pipeline state found.\n\n"
    "ACTION REQUIRED: The bug pipeline state file (~/.claude/.bug_pipeline_state) "
    "must exist with a valid bug_id before test evidence can be verified."
)

NO_FILE_ERROR = (
    "VALIDATION FAILED: Test results file not found: {path}\n\n"
    "ACTION REQUIRED: Run the test suite and save the output to {path}. "
    "The file must contain actual test output (not prose). "
    "Do not stop until test evidence has been captured."
)

EMPTY_FILE_ERROR = (
    "VALIDATION FAILED: Test results file is empty: {path}\n\n"
    "ACTION REQUIRED: Run the test suite and save the actual output to {path}. "
    "The file must contain real test runner output."
)

NO_TEST_OUTPUT_ERROR = (
    "VALIDATION FAILED: File '{path}' does not contain recognizable test output.\n\n"
    "The file appears to be prose without actual test runner output.\n\n"
    "ACTION REQUIRED: Run the actual test suite (pytest, jest, cargo test, etc.) "
    "and capture the raw output to '{path}'. Look for patterns like: "
    "PASSED, FAILED, 'tests ran', assertions, test suites."
)


def main():
    """Main entry point."""
    logger.info("=" * 60)
    logger.info("Validator started: enforce_test_evidence")

    try:
        # Read hook input from stdin
        try:
            input_data = json.load(sys.stdin)
            logger.info(f"Stdin input received: {len(json.dumps(input_data))} bytes")
        except (json.JSONDecodeError, EOFError):
            input_data = {}
            logger.info("No stdin input or invalid JSON")

        # Read pipeline state
        if not os.path.exists(PIPELINE_STATE):
            logger.warning("No pipeline state file found")
            result = {"result": "block", "reason": NO_STATE_ERROR}
            print(json.dumps(result))
            sys.exit(1)

        try:
            with open(PIPELINE_STATE) as f:
                state = json.load(f)
        except (json.JSONDecodeError, OSError) as e:
            logger.warning(f"Failed to read pipeline state: {e}")
            result = {"result": "block", "reason": NO_STATE_ERROR}
            print(json.dumps(result))
            sys.exit(1)

        bug_id = state.get("bug_id", "")
        if not bug_id:
            logger.warning("No bug_id in pipeline state")
            result = {"result": "block", "reason": NO_STATE_ERROR}
            print(json.dumps(result))
            sys.exit(1)

        # Check test-results.md exists
        test_results_path = f"bugs/{bug_id}/test-results.md"
        logger.info(f"Checking test evidence: {test_results_path}")

        if not os.path.exists(test_results_path):
            msg = NO_FILE_ERROR.format(path=test_results_path)
            logger.warning(f"FAIL: File not found: {test_results_path}")
            result = {"result": "block", "reason": msg}
            print(json.dumps(result))
            sys.exit(1)

        # Check file is non-empty
        try:
            content = Path(test_results_path).read_text(encoding='utf-8').strip()
        except (OSError, UnicodeDecodeError) as e:
            logger.error(f"Failed to read {test_results_path}: {e}")
            msg = NO_FILE_ERROR.format(path=test_results_path)
            result = {"result": "block", "reason": msg}
            print(json.dumps(result))
            sys.exit(1)

        if not content:
            msg = EMPTY_FILE_ERROR.format(path=test_results_path)
            logger.warning(f"FAIL: File is empty: {test_results_path}")
            result = {"result": "block", "reason": msg}
            print(json.dumps(result))
            sys.exit(1)

        # Validate content has actual test output patterns
        found_patterns = []
        for pattern in TEST_OUTPUT_PATTERNS:
            if re.search(pattern, content, re.IGNORECASE):
                found_patterns.append(pattern)

        logger.info(f"Test output patterns found: {len(found_patterns)}")

        if not found_patterns:
            msg = NO_TEST_OUTPUT_ERROR.format(path=test_results_path)
            logger.warning(f"FAIL: No test output patterns found in {test_results_path}")
            result = {"result": "block", "reason": msg}
            print(json.dumps(result))
            sys.exit(1)

        # All checks passed
        msg = (
            f"Test evidence validated for {bug_id}: "
            f"{test_results_path} ({len(content)} chars, "
            f"{len(found_patterns)} test output patterns matched)"
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
