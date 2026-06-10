#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.8"
# ///

"""
Stop hook: Validates that the most recently modified file in a directory
contains all required sections/strings.

Used by /plan_w_team to ensure the plan file has all required sections
before the session ends.

Usage:
  uv run validate_file_contains.py --directory specs --extension .md \
    --contains '## Task Description' \
    --contains '## Objective' \
    --contains '## Step by Step Tasks'

Exit codes:
  0 = all sections found (allow)
  2 = missing sections (block)
"""

import argparse
import glob
import os
import sys


def main():
    parser = argparse.ArgumentParser(description="Validate file contains required sections")
    parser.add_argument("--directory", required=True, help="Directory to check")
    parser.add_argument("--extension", required=True, help="File extension (e.g., .md)")
    parser.add_argument("--contains", action="append", required=True,
                        help="Required string that must appear in the file (can be repeated)")
    args = parser.parse_args()

    # Read and discard stdin (hook protocol sends event data)
    try:
        sys.stdin.read()
    except Exception:
        pass

    directory = args.directory
    extension = args.extension
    required_sections = args.contains

    # Find matching files, sorted by modification time (newest first)
    pattern = os.path.join(directory, f"*{extension}")
    matching_files = glob.glob(pattern)

    if not matching_files:
        print(
            f"BLOCKED: No {extension} files found in '{directory}/'.\n"
            f"Cannot validate contents — no plan file exists.",
            file=sys.stderr,
        )
        sys.exit(2)

    # Get the most recently modified file
    matching_files.sort(key=os.path.getmtime, reverse=True)
    target_file = matching_files[0]

    # Read the file
    try:
        with open(target_file, "r") as f:
            content = f.read()
    except (OSError, IOError) as e:
        print(f"BLOCKED: Cannot read '{target_file}': {e}", file=sys.stderr)
        sys.exit(2)

    # Check for each required section
    missing = []
    for section in required_sections:
        if section not in content:
            missing.append(section)

    if missing:
        print(
            f"BLOCKED: Plan file '{target_file}' is missing required sections:\n",
            file=sys.stderr,
        )
        for section in missing:
            print(f"  - {section}", file=sys.stderr)
        print(
            f"\nYour plan must contain ALL of these sections:\n",
            file=sys.stderr,
        )
        for section in required_sections:
            marker = "MISSING" if section in missing else "OK"
            print(f"  [{marker}] {section}", file=sys.stderr)
        print(
            f"\nAdd the missing sections to '{target_file}' before completing.",
            file=sys.stderr,
        )
        sys.exit(2)

    print(
        f"Plan file '{target_file}' contains all {len(required_sections)} required sections.",
        file=sys.stderr,
    )
    sys.exit(0)


if __name__ == "__main__":
    main()
