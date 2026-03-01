#!/usr/bin/env python3
"""
PostToolUse validator — Copilot format.

Reads .github/project.json to determine which lint/typecheck commands
to run for each file type. No project-specific commands are hardcoded.

Input schema (Copilot):
  {
    "timestamp":  int,
    "cwd":        "/path/to/workspace",
    "toolName":   "editFiles" | "createFile" | "runCommand" | ...,
    "toolArgs":   "{...json string...}",
    "toolResult": "...",
    "sessionId":  "..."
  }

Output schema (Copilot):
  { "continue": true }
  OR
  {
    "decision":   "block",
    "reason":     "short reason",
    "hookSpecificOutput": {
      "hookEventName":   "postToolUse",
      "additionalContext": "message injected into agent context"
    }
  }

NOTE: Copilot hooks use "toolName" (not "tool_name") and
      "toolArgs" (not "tool_input"). The event name is
      "postToolUse" (camelCase), not "PostToolUse".
"""

import json
import os
import re
import subprocess
import sys
from pathlib import Path

# Required sections in specs/*.md plan files
SPEC_REQUIRED_SECTIONS = [
    "## Task Description",
    "## Objective",
    "## Relevant Files",
    "## Step by Step Tasks",
    "## Acceptance Criteria",
    "## Team Orchestration",
    "### Team Members",
]

# Required sections in bugs/*/report.md bug reports
BUG_REPORT_REQUIRED_SECTIONS = [
    "## Summary",
    "## Steps to Reproduce",
    "## Expected Behavior",
    "## Actual Behavior",
    "## Environment",
    "## Severity",
    "## Module/Area",
    "## Evidence",
]

# Copilot tool names that write/modify files
FILE_WRITE_TOOLS = {
    "editFiles",
    "createFile",
    "writeFile",
    "edit",
    "write",
    "str_replace",
    "insert",
}


def read_input() -> dict:
    try:
        raw = sys.stdin.read()
        return json.loads(raw) if raw.strip() else {}
    except Exception:
        return {}


def is_file_write(tool_name: str) -> bool:
    # If tool name is empty/unknown, be conservative and run validation
    if not tool_name:
        return True
    return tool_name in FILE_WRITE_TOOLS


def get_changed_file(tool_args_str: str) -> str | None:
    """Extract file path from toolArgs JSON string if present."""
    try:
        args = json.loads(tool_args_str) if tool_args_str else {}
        return (
            args.get("path")
            or args.get("file_path")
            or args.get("filename")
            # editFiles passes a list; take first entry
            or (args.get("files", [None])[0] if isinstance(args.get("files"), list) else None)
        )
    except Exception:
        return None


def run(cmd: list[str], cwd: Path) -> tuple[bool, str]:
    result = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    return result.returncode == 0, (result.stdout + result.stderr).strip()


def block(reason: str, context: str) -> None:
    print(json.dumps({
        "decision": "block",
        "reason": reason,
        "hookSpecificOutput": {
            "hookEventName": "postToolUse",
            "additionalContext": context,
        }
    }))
    sys.exit(1)


def allow() -> None:
    print(json.dumps({"continue": True}))


def load_project_config(cwd: Path) -> dict | None:
    """Load .github/project.json if it exists."""
    cfg_path = cwd / ".github" / "project.json"
    if not cfg_path.exists():
        return None
    try:
        return json.loads(cfg_path.read_text(encoding="utf-8"))
    except Exception:
        return None


def find_module_for_file(changed_file: str, project_cfg: dict) -> str | None:
    """Find which module owns the changed file based on path prefixes."""
    for mod_name, mod_cfg in project_cfg.get("modules", {}).items():
        for path_prefix in mod_cfg.get("paths", []):
            if changed_file.startswith(path_prefix) or changed_file.startswith(f"./{path_prefix}"):
                return mod_name
    return None


def parse_command(cmd_str: str, cwd: Path) -> tuple[list[str], Path]:
    """Parse a command string like 'cd backend && ruff check .' into (cmd_list, working_dir).

    Handles patterns:
      - "cd <dir> && <command>"  → runs <command> in cwd/<dir>
      - "<command>"              → runs <command> in cwd
    """
    if "&&" in cmd_str:
        parts = cmd_str.split("&&", 1)
        cd_part = parts[0].strip()
        cmd_part = parts[1].strip()
        if cd_part.startswith("cd "):
            subdir = cd_part[3:].strip()
            return cmd_part.split(), cwd / subdir
    return cmd_str.split(), cwd


def main() -> None:
    data = read_input()
    cwd = Path(data.get("cwd", os.getcwd()))

    tool_name = data.get("toolName", "")
    tool_args = data.get("toolArgs", "")

    if not is_file_write(tool_name):
        allow()
        return

    changed_file = get_changed_file(tool_args)

    # ── Load project config for dynamic lint/typecheck commands ──────────────
    project_cfg = load_project_config(cwd)

    # ── Source file changed → run module's lint/typecheck commands ────────────
    if changed_file and project_cfg:
        module = find_module_for_file(changed_file, project_cfg)
        if module:
            mod_cfg = project_cfg["modules"][module]
            mod_dir = cwd / mod_cfg["paths"][0]

            # Run lint command if defined
            if "lint" in mod_cfg and mod_dir.exists():
                lint_cmd, lint_cwd = parse_command(mod_cfg["lint"], cwd)
                ok, out = run(lint_cmd, lint_cwd)
                if not ok:
                    block(
                        reason=f"Lint failed ({module} module)",
                        context=(
                            f"🛑 Lint failed on {changed_file}:\n\n{out}\n\n"
                            f"Command: {mod_cfg['lint']}\n"
                            "Fix the lint errors before continuing."
                        )
                    )

            # Run typecheck command if defined
            if "typecheck" in mod_cfg and mod_dir.exists():
                tc_cmd, tc_cwd = parse_command(mod_cfg["typecheck"], cwd)
                ok, out = run(tc_cmd, tc_cwd)
                if not ok:
                    block(
                        reason=f"Typecheck failed ({module} module)",
                        context=(
                            f"🛑 Typecheck failed after editing {changed_file}:\n\n{out}\n\n"
                            f"Command: {mod_cfg['typecheck']}\n"
                            "Fix the type errors before continuing."
                        )
                    )

    # ── Spec file written to specs/ → validate required sections ─────────────
    if changed_file and re.search(r"(^|/)specs/.*\.md$", changed_file):
        spec_path = cwd / changed_file if not Path(changed_file).is_absolute() else Path(changed_file)
        if spec_path.exists():
            content = spec_path.read_text(encoding="utf-8")
            missing = [s for s in SPEC_REQUIRED_SECTIONS if s not in content]
            if missing:
                block(
                    reason="Spec file missing required sections",
                    context=(
                        f"🛑 Plan file {changed_file} is missing required sections:\n\n"
                        + "\n".join(f"  - {s}" for s in missing)
                        + "\n\nAll plan files in specs/ must contain these sections:\n"
                        + "\n".join(f"  - {s}" for s in SPEC_REQUIRED_SECTIONS)
                        + "\n\nAdd the missing sections before continuing."
                    ),
                )

            # ── Validator frequency check ────────────────────────────────────
            builder_count = len(re.findall(
                r"^-\s+\*\*Role\*\*:\s*builder\s*$", content, re.MULTILINE
            ))
            validator_count = len(re.findall(
                r"^-\s+\*\*Role\*\*:\s*validator\s*$", content, re.MULTILINE
            ))
            if builder_count > 5:
                # Require at least 1 intermediate validator + 1 final = 2
                # For 11+, require 1 per 5 builders + 1 final
                required_validators = (builder_count // 5) + 1
                if validator_count < required_validators:
                    block(
                        reason="Spec file has insufficient intermediate validators",
                        context=(
                            f"🛑 Plan file {changed_file} has {builder_count} builder tasks "
                            f"but only {validator_count} validator task(s).\n\n"
                            f"Rule: Plans with >5 builder tasks need intermediate validators.\n"
                            f"  - {builder_count} builders → need ≥{required_validators} "
                            f"validator tasks ({required_validators - 1} intermediate + 1 final).\n"
                            f"  - Currently have: {validator_count}.\n\n"
                            f"Add intermediate validator tasks (e.g., 'validate-phase-1') "
                            f"after every ~5 builder tasks. These should run all tests, lint, "
                            f"and typecheck to catch regressions early."
                        ),
                    )

    # ── Bug report written to bugs/*/report.md → validate required sections ──
    if changed_file and re.search(r"bugs/.+/report\.md$", changed_file):
        report_path = (
            cwd / changed_file
            if not Path(changed_file).is_absolute()
            else Path(changed_file)
        )
        if report_path.exists():
            content = report_path.read_text(encoding="utf-8")
            missing = [s for s in BUG_REPORT_REQUIRED_SECTIONS if s not in content]
            if missing:
                block(
                    reason="Bug report missing required sections",
                    context=(
                        f"🛑 Bug report {changed_file} is missing required sections:\n\n"
                        + "\n".join(f"  - {s}" for s in missing)
                        + "\n\nAll bug reports must contain these 8 sections:\n"
                        + "\n".join(f"  - {s}" for s in BUG_REPORT_REQUIRED_SECTIONS)
                        + "\n\nAdd the missing sections before continuing."
                    ),
                )

    allow()


if __name__ == "__main__":
    main()
