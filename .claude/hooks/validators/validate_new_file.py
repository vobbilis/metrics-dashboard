#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.8"
# ///

"""
Stop hook: Validates that a new/modified file exists in the specified directory.

Used by /plan_w_team to ensure a plan file was actually created before
the session ends.

Usage:
  uv run validate_new_file.py --directory specs --extension .md

Exit codes:
  0 = file found (allow)
  2 = no file found (block)
"""

import argparse
import glob
import os
import sys
import time


def main():
    parser = argparse.ArgumentParser(description="Validate a new file exists")
    parser.add_argument("--directory", required=True, help="Directory to check")
    parser.add_argument("--extension", required=True, help="File extension to look for (e.g., .md)")
    args = parser.parse_args()

    # Read and discard stdin (hook protocol sends event data)
    try:
        sys.stdin.read()
    except Exception:
        pass

    directory = args.directory
    extension = args.extension

    # Check if directory exists
    if not os.path.isdir(directory):
        print(
            f"BLOCKED: Directory '{directory}' does not exist.\n"
            f"You must create a plan file in '{directory}/' before completing.",
            file=sys.stderr,
        )
        sys.exit(2)

    # Find files matching the extension
    pattern = os.path.join(directory, f"*{extension}")
    matching_files = glob.glob(pattern)

    if not matching_files:
        print(
            f"BLOCKED: No {extension} files found in '{directory}/'.\n"
            f"You must save your plan to '{directory}/<plan-name>{extension}' before completing.",
            file=sys.stderr,
        )
        sys.exit(2)

    # Check if any file was modified in the last 30 minutes (likely created this session)
    recent_threshold = time.time() - (30 * 60)
    recent_files = [f for f in matching_files if os.path.getmtime(f) > recent_threshold]

    if not recent_files:
        print(
            f"BLOCKED: No recently modified {extension} files in '{directory}/'.\n"
            f"Existing files were not modified this session. Save your plan before completing.",
            file=sys.stderr,
        )
        sys.exit(2)

    # Sort by modification time, newest first
    recent_files.sort(key=os.path.getmtime, reverse=True)
    newest = recent_files[0]
    print(f"Plan file found: {newest}", file=sys.stderr)
    sys.exit(0)


if __name__ == "__main__":
    main()
