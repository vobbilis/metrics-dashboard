#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.8"
# ///

"""
Stop hook: Audits team member usage before allowing session end.

When a team was active during this session, this hook checks:
1. Were all required team roles spawned? (validator, test-architect)
2. Did team members actually complete work?
3. Generates an audit report.

If required roles were never spawned, it prints a LOUD WARNING
(but does not block session end — that would be too disruptive).

Also cleans up the team lead marker file on session end.
"""

import json
import os
import sys
import glob
from datetime import datetime

MARKER_FILE = os.path.expanduser("~/.claude/.team_lead_session")
AUDIT_DIR = os.path.expanduser("~/.claude/.team_audit")


def load_subagent_stop_log() -> list:
    """Load the subagent stop log to see which agents actually ran."""
    log_path = os.path.join(os.getcwd(), "logs", "subagent_stop.json")
    if not os.path.exists(log_path):
        return []
    try:
        with open(log_path) as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return []


def main():
    try:
        input_data = json.load(sys.stdin)
        session_id = input_data.get("session_id", "")

        # Check if a team was active in this session
        if not os.path.exists(MARKER_FILE):
            sys.exit(0)

        try:
            with open(MARKER_FILE) as f:
                marker = json.load(f)
        except (json.JSONDecodeError, OSError):
            sys.exit(0)

        lead_session_id = marker.get("lead_session_id", "")
        team_name = marker.get("team_name", "")

        # Only audit if this is the lead session ending
        if session_id != lead_session_id:
            sys.exit(0)

        # Load audit data
        audit_path = os.path.join(AUDIT_DIR, f"{team_name}.json")
        audit_data = {}
        if os.path.exists(audit_path):
            try:
                with open(audit_path) as f:
                    audit_data = json.load(f)
            except (json.JSONDecodeError, OSError):
                pass

        # Load subagent completion records
        subagent_logs = load_subagent_stop_log()
        completed_agents = [
            log.get("agent_id", "") for log in subagent_logs
        ]

        # Check required roles
        members_spawned = audit_data.get("members_spawned", [])
        required_roles = audit_data.get("required_roles", ["validator", "test-architect"])

        spawned_types = set()
        spawned_names = set()
        for member in members_spawned:
            spawned_types.add(member.get("type", ""))
            spawned_names.add(member.get("name", ""))

        missing_roles = []
        for role in required_roles:
            # Check if any spawned member name or type contains the role keyword
            role_found = any(
                role.lower() in name.lower() or role.lower() in t.lower()
                for name in spawned_names
                for t in spawned_types
            )
            if not role_found:
                # Also check if any spawned name loosely matches
                role_found = any(
                    role.lower().replace("-", "") in name.lower().replace("-", "")
                    for name in spawned_names
                )
            if not role_found:
                missing_roles.append(role)

        # Generate audit report
        report_lines = [
            f"{'='*60}",
            f"TEAM AUDIT REPORT — {team_name}",
            f"{'='*60}",
            f"Session:  {lead_session_id[:16]}...",
            f"Time:     {datetime.now().isoformat()}",
            f"",
            f"Team Members Spawned: {len(members_spawned)}",
        ]

        for member in members_spawned:
            report_lines.append(
                f"  - {member.get('name', '?')} (type: {member.get('type', '?')}) "
                f"at {member.get('spawned_at', '?')}"
            )

        report_lines.append(f"")
        report_lines.append(f"Subagents Completed: {len(completed_agents)}")
        report_lines.append(f"")

        if missing_roles:
            report_lines.append(f"{'!'*60}")
            report_lines.append(f"WARNING: REQUIRED ROLES NEVER SPAWNED:")
            for role in missing_roles:
                report_lines.append(f"  ✗ {role}")
            report_lines.append(f"")
            report_lines.append(
                f"The plan spec required these roles but they were never used."
            )
            report_lines.append(
                f"Work may be incomplete or unvalidated."
            )
            report_lines.append(f"{'!'*60}")
        else:
            report_lines.append(f"✓ All required roles were spawned.")

        report = "\n".join(report_lines)

        # Write audit report to logs
        log_dir = os.path.join(os.getcwd(), "logs")
        os.makedirs(log_dir, exist_ok=True)
        report_path = os.path.join(log_dir, f"team_audit_{team_name}.txt")
        with open(report_path, "w") as f:
            f.write(report)

        # Print to stderr so user sees it
        print(report, file=sys.stderr)

        # Clean up marker file (session is ending)
        try:
            os.remove(MARKER_FILE)
        except OSError:
            pass

        sys.exit(0)

    except json.JSONDecodeError:
        sys.exit(0)
    except Exception as e:
        # Log but don't block session end
        print(f"Team audit error: {e}", file=sys.stderr)
        sys.exit(0)


if __name__ == "__main__":
    main()
