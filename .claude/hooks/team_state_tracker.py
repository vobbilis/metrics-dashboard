#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.8"
# ///

"""
PostToolUse hook: Tracks TeamCreate / TeamDelete events.

When TeamCreate succeeds → writes lead session marker file.
When TeamDelete succeeds → removes lead session marker file.

The marker file is used by enforce_team_lead.py to block the lead
from writing code directly (must delegate to team members).
"""

import json
import os
import sys
from pathlib import Path

MARKER_FILE = os.path.expanduser("~/.claude/.team_lead_session")
AUDIT_DIR = os.path.expanduser("~/.claude/.team_audit")
TEAMS_DIR = os.path.expanduser("~/.claude/teams")


def main():
    try:
        input_data = json.load(sys.stdin)
        tool_name = input_data.get("tool_name", "")
        tool_input = input_data.get("tool_input", {})
        session_id = input_data.get("session_id", "")

        if tool_name == "TeamCreate":
            # TeamCreate succeeded — mark this session as the team lead
            team_name = tool_input.get("team_name", "unknown")

            os.makedirs(os.path.dirname(MARKER_FILE), exist_ok=True)
            marker_data = {
                "lead_session_id": session_id,
                "team_name": team_name,
                "created_at": __import__("datetime").datetime.now().isoformat(),
            }
            with open(MARKER_FILE, "w") as f:
                json.dump(marker_data, f, indent=2)

            # Create team config file (TeamCreate tool doesn't persist this to disk)
            team_config_dir = os.path.join(TEAMS_DIR, team_name)
            os.makedirs(team_config_dir, exist_ok=True)
            config_data = {
                "team_name": team_name,
                "description": tool_input.get("description", ""),
                "created_at": __import__("datetime").datetime.now().isoformat(),
                "members": [],
                "lead_agent_id": f"team-lead@{team_name}",
                "lead_session_id": session_id,
            }
            config_path = os.path.join(team_config_dir, "config.json")
            with open(config_path, "w") as f:
                json.dump(config_data, f, indent=2)

            # Initialize audit tracking
            os.makedirs(AUDIT_DIR, exist_ok=True)
            audit_data = {
                "team_name": team_name,
                "lead_session_id": session_id,
                "members_spawned": [],
                "members_completed": [],
                "required_roles": ["validator", "test-architect"],
            }
            audit_path = os.path.join(AUDIT_DIR, f"{team_name}.json")
            with open(audit_path, "w") as f:
                json.dump(audit_data, f, indent=2)

            # Log to stderr so user sees confirmation
            print(
                f"TEAM LEAD LOCKED: Session {session_id[:12]}... is now team lead for '{team_name}'. "
                f"Direct Write/Edit blocked for this session — delegate to team members.",
                file=sys.stderr,
            )

        elif tool_name == "TeamDelete":
            # TeamDelete succeeded — remove the marker and team config
            if os.path.exists(MARKER_FILE):
                # Read team name before removing marker
                try:
                    with open(MARKER_FILE) as f:
                        marker = json.load(f)
                    old_team_name = marker.get("team_name", "")
                    if old_team_name:
                        team_config_dir = os.path.join(TEAMS_DIR, old_team_name)
                        config_path = os.path.join(team_config_dir, "config.json")
                        if os.path.exists(config_path):
                            os.remove(config_path)
                        if os.path.isdir(team_config_dir):
                            try:
                                os.rmdir(team_config_dir)
                            except OSError:
                                pass  # Directory not empty, leave it
                except (json.JSONDecodeError, OSError):
                    pass
                os.remove(MARKER_FILE)
                print("TEAM LEAD UNLOCKED: Team deleted, direct code access restored.", file=sys.stderr)

        elif tool_name == "Task":
            # Track team member spawns
            task_input = tool_input or {}
            team_name_param = task_input.get("team_name", "")
            agent_name = task_input.get("name", "")
            agent_type = task_input.get("subagent_type", "")

            if team_name_param and agent_name:
                # Update team config with new member
                config_path = os.path.join(TEAMS_DIR, team_name_param, "config.json")
                if os.path.exists(config_path):
                    try:
                        with open(config_path) as f:
                            config = json.load(f)
                        member = {"name": agent_name, "agentType": agent_type}
                        config.setdefault("members", []).append(member)
                        with open(config_path, "w") as f:
                            json.dump(config, f, indent=2)
                    except (json.JSONDecodeError, OSError):
                        pass

                # Update audit tracking
                audit_path = os.path.join(AUDIT_DIR, f"{team_name_param}.json")
                if os.path.exists(audit_path):
                    with open(audit_path) as f:
                        audit_data = json.load(f)
                    member_record = {
                        "name": agent_name,
                        "type": agent_type,
                        "spawned_at": __import__("datetime").datetime.now().isoformat(),
                    }
                    audit_data.setdefault("members_spawned", []).append(member_record)
                    with open(audit_path, "w") as f:
                        json.dump(audit_data, f, indent=2)

        sys.exit(0)

    except json.JSONDecodeError:
        sys.exit(0)
    except Exception:
        sys.exit(0)


if __name__ == "__main__":
    main()
