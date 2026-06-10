#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///

"""
Stop hook: Validates bug routing output is valid JSON with required fields.

Checks:
1. Routing output is valid JSON with: module, fixer_agent, confidence, rationale
2. fixer_agent exists as ~/.claude/agents/team/{fixer_agent}.md
3. confidence is high or medium (blocks on low)
4. module matches .claude/bug-modules.json registry

Exit codes:
- 0: Validation passed
- 1: Validation failed

Usage:
  uv run validate_bug_routing.py
"""

import json
import logging
import os
import sys
import time
from pathlib import Path

# Logging setup - log file next to this script (wrapped to prevent crash)
try:
    SCRIPT_DIR = Path(__file__).parent
    LOG_FILE = SCRIPT_DIR / "validate_bug_routing.log"
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
AGENTS_DIR = os.path.expanduser("~/.claude/agents/team")
BUG_MODULES_FILE = ".claude/bug-modules.json"
REQUIRED_FIELDS = ["module", "fixer_agent", "confidence", "rationale"]
VALID_CONFIDENCE = {"high", "medium"}

NO_ROUTING_ERROR = (
    "VALIDATION FAILED: No routing output found.\n\n"
    "ACTION REQUIRED: The bug routing step must produce a JSON routing "
    "decision with fields: module, fixer_agent, confidence, rationale."
)

INVALID_JSON_ERROR = (
    "VALIDATION FAILED: Routing output is not valid JSON.\n\n"
    "ACTION REQUIRED: The routing output must be valid JSON. "
    "Check the routing file for syntax errors."
)

MISSING_FIELDS_ERROR = (
    "VALIDATION FAILED: Routing output is missing {count} required field(s).\n\n"
    "MISSING FIELDS:\n{missing_list}\n\n"
    "ACTION REQUIRED: Add the missing fields to the routing JSON."
)

NO_AGENT_ERROR = (
    "VALIDATION FAILED: Fixer agent '{agent}' not found.\n\n"
    "Expected file: {path}\n\n"
    "ACTION REQUIRED: Either create the agent file or update the routing "
    "to use an existing agent from ~/.claude/agents/team/."
)

LOW_CONFIDENCE_ERROR = (
    "VALIDATION FAILED: Routing confidence is '{confidence}' (must be high or medium).\n\n"
    "Rationale: {rationale}\n\n"
    "ACTION REQUIRED: Re-analyze the bug and provide a routing with higher confidence, "
    "or improve the rationale to justify the routing decision."
)

UNKNOWN_MODULE_ERROR = (
    "VALIDATION FAILED: Module '{module}' not found in bug-modules.json registry.\n\n"
    "Known modules: {known}\n\n"
    "ACTION REQUIRED: Use one of the registered modules, or update "
    ".claude/bug-modules.json to include '{module}'."
)


def find_routing_output(bug_dir: str) -> dict | None:
    """Find and parse the most recent routing output."""
    # Check pipeline state for current bug_id
    if os.path.exists(PIPELINE_STATE):
        try:
            with open(PIPELINE_STATE) as f:
                state = json.load(f)
            bug_id = state.get("bug_id", "")
            if bug_id:
                routing_file = Path(bug_dir) / bug_id / "routing.json"
                if routing_file.exists():
                    logger.info(f"Found routing file: {routing_file}")
                    with open(routing_file) as f:
                        return json.load(f)
        except (json.JSONDecodeError, OSError) as e:
            logger.warning(f"Error reading pipeline state: {e}")

    # Fallback: find newest routing.json in bug_dir
    bug_path = Path(bug_dir)
    if not bug_path.exists():
        return None

    routing_files = list(bug_path.rglob("routing.json"))
    if not routing_files:
        return None

    # Newest by mtime
    newest = max(routing_files, key=lambda p: p.stat().st_mtime)
    logger.info(f"Found routing file (fallback): {newest}")
    try:
        with open(newest) as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return None


def main():
    """Main entry point."""
    logger.info("=" * 60)
    logger.info("Validator started: validate_bug_routing")

    try:
        # Read hook input from stdin
        try:
            input_data = json.load(sys.stdin)
            logger.info(f"Stdin input received: {len(json.dumps(input_data))} bytes")
        except (json.JSONDecodeError, EOFError):
            input_data = {}
            logger.info("No stdin input or invalid JSON")

        # Find routing output
        routing = find_routing_output("bugs")

        if routing is None:
            logger.warning("FAIL: No routing output found")
            result = {"result": "block", "reason": NO_ROUTING_ERROR}
            print(json.dumps(result))
            sys.exit(1)

        # Check required fields
        missing = [f for f in REQUIRED_FIELDS if f not in routing]
        if missing:
            missing_list = "\n".join(f"  - {f}" for f in missing)
            msg = MISSING_FIELDS_ERROR.format(count=len(missing), missing_list=missing_list)
            logger.warning(f"FAIL: Missing fields: {missing}")
            result = {"result": "block", "reason": msg}
            print(json.dumps(result))
            sys.exit(1)

        fixer_agent = routing["fixer_agent"]
        confidence = routing["confidence"]
        module = routing["module"]
        rationale = routing.get("rationale", "")

        # Check fixer_agent exists
        agent_path = os.path.join(AGENTS_DIR, f"{fixer_agent}.md")
        if not os.path.exists(agent_path):
            msg = NO_AGENT_ERROR.format(agent=fixer_agent, path=agent_path)
            logger.warning(f"FAIL: Agent not found: {agent_path}")
            result = {"result": "block", "reason": msg}
            print(json.dumps(result))
            sys.exit(1)

        # Check confidence level
        if confidence.lower() not in VALID_CONFIDENCE:
            msg = LOW_CONFIDENCE_ERROR.format(confidence=confidence, rationale=rationale)
            logger.warning(f"FAIL: Low confidence: {confidence}")
            result = {"result": "block", "reason": msg}
            print(json.dumps(result))
            sys.exit(1)

        # Cross-check module against registry
        if os.path.exists(BUG_MODULES_FILE):
            try:
                with open(BUG_MODULES_FILE) as f:
                    modules_registry = json.load(f)
                known_modules = list(modules_registry.get("modules", {}).keys())
                if known_modules and module not in known_modules:
                    msg = UNKNOWN_MODULE_ERROR.format(
                        module=module,
                        known=", ".join(known_modules)
                    )
                    logger.warning(f"FAIL: Unknown module: {module}")
                    result = {"result": "block", "reason": msg}
                    print(json.dumps(result))
                    sys.exit(1)
            except (json.JSONDecodeError, OSError) as e:
                logger.warning(f"Could not read bug-modules.json: {e} (allowing through)")
        else:
            logger.info("No bug-modules.json found, skipping module cross-check")

        # All checks passed
        msg = (
            f"Routing validated: module={module}, fixer_agent={fixer_agent}, "
            f"confidence={confidence}"
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
