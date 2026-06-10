#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///

"""
Stop hook: Validates that a bug report contains all required sections.

Checks the bugs/ directory for the newest report.md file and validates
it contains all 8 required sections.

Exit codes:
- 0: Validation passed (all sections present)
- 1: Validation failed (missing sections)

Usage:
  uv run validate_bug_report.py --bug-dir bugs
"""

import argparse
import json
import logging
import sys
import time
from pathlib import Path

# Logging setup - log file next to this script (wrapped to prevent crash)
try:
    SCRIPT_DIR = Path(__file__).parent
    LOG_FILE = SCRIPT_DIR / "validate_bug_report.log"
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[logging.FileHandler(LOG_FILE, mode='a')]
    )
except Exception:
    logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Required sections in a bug report
REQUIRED_SECTIONS = [
    "## Summary",
    "## Steps to Reproduce",
    "## Expected Behavior",
    "## Actual Behavior",
    "## Environment",
    "## Severity",
    "## Module/Area",
    "## Evidence",
]

NO_FILE_ERROR = (
    "VALIDATION FAILED: No report.md file found in {bug_dir}/.\n\n"
    "ACTION REQUIRED: Create a bug report file at {bug_dir}/<BUG-ID>/report.md "
    "with all required sections. Do not stop until the report has been created."
)

MISSING_SECTIONS_ERROR = (
    "VALIDATION FAILED: Bug report '{file}' is missing {count} required section(s).\n\n"
    "MISSING SECTIONS:\n{missing_list}\n\n"
    "ACTION REQUIRED: Use the Edit tool to add the missing sections to '{file}'. "
    "Each section must appear exactly as shown above (case-sensitive). "
    "Do not stop until all required sections are present."
)


def find_newest_report(bug_dir: str) -> str | None:
    """Find the most recently modified report.md in bug_dir subdirectories."""
    target = Path(bug_dir)
    if not target.exists():
        logger.info(f"Bug directory does not exist: {bug_dir}")
        return None

    reports = list(target.rglob("report.md"))
    if not reports:
        logger.info(f"No report.md files found in {bug_dir}")
        return None

    # Find newest by modification time
    newest = None
    newest_mtime = 0

    for report in reports:
        try:
            mtime = report.stat().st_mtime
            if mtime > newest_mtime:
                newest_mtime = mtime
                newest = str(report)
        except OSError:
            continue

    logger.info(f"Found {len(reports)} report(s), newest: {newest}")
    return newest


def validate_report(filepath: str) -> tuple[bool, list[str], list[str]]:
    """
    Validate that report contains all required sections.

    Returns:
        tuple: (all_found, found_sections, missing_sections)
    """
    try:
        content = Path(filepath).read_text(encoding='utf-8')
    except (OSError, UnicodeDecodeError) as e:
        logger.error(f"Failed to read {filepath}: {e}")
        return False, [], REQUIRED_SECTIONS[:]

    found = []
    missing = []

    for section in REQUIRED_SECTIONS:
        if section in content:
            found.append(section)
        else:
            missing.append(section)

    return len(missing) == 0, found, missing


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Validate bug report contains required sections"
    )
    parser.add_argument(
        '--bug-dir',
        type=str,
        default='bugs',
        help='Directory containing bug reports (default: bugs)'
    )
    return parser.parse_args()


def main():
    """Main entry point."""
    logger.info("=" * 60)
    logger.info("Validator started: validate_bug_report")

    try:
        args = parse_args()
        logger.info(f"Args: bug_dir={args.bug_dir}")

        # Read hook input from stdin
        try:
            input_data = json.load(sys.stdin)
            logger.info(f"Stdin input received: {len(json.dumps(input_data))} bytes")
        except (json.JSONDecodeError, EOFError):
            input_data = {}
            logger.info("No stdin input or invalid JSON")

        # Find newest report
        newest = find_newest_report(args.bug_dir)

        if not newest:
            msg = NO_FILE_ERROR.format(bug_dir=args.bug_dir)
            logger.warning(f"FAIL: No report found")
            result = {"result": "block", "reason": msg}
            print(json.dumps(result))
            sys.exit(1)

        # Validate sections
        all_found, found, missing = validate_report(newest)
        logger.info(f"Sections check - Found: {len(found)}/{len(REQUIRED_SECTIONS)}")

        if all_found:
            msg = f"Bug report '{newest}' contains all {len(REQUIRED_SECTIONS)} required sections"
            logger.info(f"PASS: {msg}")
            result = {"result": "continue", "message": msg}
            print(json.dumps(result))
            sys.exit(0)
        else:
            missing_list = "\n".join(f"  - {m}" for m in missing)
            msg = MISSING_SECTIONS_ERROR.format(
                file=newest,
                count=len(missing),
                missing_list=missing_list
            )
            logger.warning(f"FAIL: Missing {len(missing)} sections: {missing}")
            result = {"result": "block", "reason": msg}
            print(json.dumps(result))
            sys.exit(1)

    except Exception as e:
        logger.exception(f"Validation error: {e}")
        print(json.dumps({
            "result": "continue",
            "message": f"Validation error (allowing through): {str(e)}"
        }))
        sys.exit(0)


if __name__ == "__main__":
    main()
