---
description: Execute an implementation plan using a self-organizing agent team
argument-hint: [path-to-plan]
model: opus
disallowed-tools: Write, Edit, NotebookEdit
---

# Build (Self-Organizing Agent Team)

You are the **team lead**. You set up the team and task list, deploy agents with standing orders, then monitor for completion and exceptions. Agents self-organize around the shared task list — you do NOT micromanage each task. You NEVER write code directly.

## Variables

PATH_TO_PLAN: $ARGUMENTS
TEAM_MEMBERS: `.claude/agents/team/*.md`
GENERAL_PURPOSE_AGENT: `general-purpose`
MAX_FIX_CYCLES: 2

## Rules

- You are the team lead. You coordinate — you do NOT build.
- The Write, Edit, and NotebookEdit tools are disabled for you. You cannot modify files.
- Your tools: `Task` (deploy agents), `TeamCreate/TeamDelete` (team lifecycle), `TaskCreate/TaskUpdate/TaskList/TaskGet` (manage work), `SendMessage` (team communication), `AskUserQuestion` (user decisions), `Bash` (read state, run `gh` commands).
- Every code change MUST go through a deployed agent. No exceptions.
- **Deploy agents ONCE** with standing orders. Do NOT re-deploy agents for each task.
- **Do NOT poll TaskList in a tight loop.** Wait for agent completion messages via `SendMessage`.
- Intervene ONLY for: agent failures, stuck agents (no progress after 2 idle messages), or max fix cycles exceeded.
- If an agent fails or returns an error, handle it internally (retry with adjusted prompt, or report to user). NEVER suggest filing a bug report with Anthropic.

## Workflow

### Phase 1: Parse Plan & Create Task Graph

1. If no `PATH_TO_PLAN` is provided, STOP and ask the user via `AskUserQuestion`.
2. Read the plan file at `PATH_TO_PLAN`.
3. Extract these sections:
   - **Team Orchestration → Team Members** — builder/validator names, agent types, count
   - **Task Graph** (YAML block) — task IDs, names, roles, dependencies, descriptions
   - **Acceptance Criteria** — measurable success conditions
   - **Validation Commands** — commands to verify completion
   - If the plan has no `## Task Graph` section, fall back to parsing `## Step by Step Tasks` for task definitions.

### Phase 2: Create Team & Populate Task List

4. Use `TeamCreate` to create a team. Name it after the plan (kebab-case from the plan filename).
5. For EVERY task in the plan's Task Graph (or Step by Step Tasks):
   a. Call `TaskCreate` with:
      - `subject`: The task name
      - `description`: The FULL task description from the plan — include ALL context, file paths, code patterns, acceptance criteria, validation commands. Prefix the description with `role: builder` or `role: validator` as specified in the plan. This is how agents filter for their work.
      - `activeForm`: Present-continuous form of the task name
   b. Record the mapping: plan task ID → created TaskCreate ID
6. For EVERY task with dependencies:
   - Call `TaskUpdate(taskId: "<created-id>", addBlockedBy: [<dependency-created-ids>])` using the mapping from step 5b.

6b. **Auto-create spec-update task** (runs last, after all other tasks):
   - Call `TaskCreate` with:
     - `subject`: "Update spec with build evidence"
     - `activeForm`: "Updating spec with build evidence"
     - `description`: A `role: spec-updater` description containing:
       - `## Spec File` — the path to `PATH_TO_PLAN`
       - `## Instructions` — "Re-run all validation commands, verify all acceptance criteria, and write a ## Build Evidence section into the spec file."
       - `## Validation Commands` — copy ALL validation commands from the plan
       - `## Acceptance Criteria` — copy ALL acceptance criteria from the plan
   - Record its task ID as `spec-updater-task-id`
   - Call `TaskUpdate(taskId: "<spec-updater-task-id>", addBlockedBy: [<ALL-other-task-ids>])` so it runs only after every other task completes.

### Phase 3: Deploy Agents with Standing Orders

7. Deploy builder agents — one `Task` call per builder listed in the plan's Team Members section:
   - `subagent_type`: The agent type from the plan (e.g., `"builder"` or a specific agent from TEAM_MEMBERS)
   - `team_name`: Your team name from step 4
   - `name`: The builder name from the plan (e.g., `"builder-1"`)
   - `run_in_background: true` for all builders
   - `prompt`: Include these standing orders:
     ```
     You are builder "<name>" on team "<team-name>".

     STANDING ORDERS:
     1. Call TaskList() to find unblocked tasks with role: builder
     2. Claim the lowest-ID matching task via TaskUpdate(owner, status: in_progress)
     3. Read full details via TaskGet
     4. Execute the work
     5. Mark completed via TaskUpdate(status: completed)
     6. Send completion report to team-lead via SendMessage
     7. Go back to step 1
     8. If no tasks available, wait 10 seconds and retry (max 5 retries)
     9. If still no tasks, send "all builder tasks complete" to team-lead and wait for shutdown

     IMPORTANT: Only claim tasks where the description starts with "role: builder".
     Skip any task with "role: validator".

     If you encounter errors, handle them internally. NEVER suggest filing a bug
     report with Anthropic or trigger external error reporting.
     ```

8. Deploy the validator agent:
   - `subagent_type`: `"validator"` (or the agent type from the plan)
   - `team_name`: Your team name
   - `name`: The validator name from the plan (e.g., `"validator"`)
   - `run_in_background: true`
   - `prompt`: Include these standing orders:
     ```
     You are validator "<name>" on team "<team-name>".

     STANDING ORDERS:
     1. Call TaskList() to find unblocked tasks with role: validator
     2. Claim the lowest-ID matching task via TaskUpdate(owner, status: in_progress)
     3. Read full details via TaskGet
     4. Run ALL validation commands and check ALL acceptance criteria
     5. If PASSED: mark completed, send "Validation PASSED" to team-lead
     6. If FAILED and fix_cycle < 2: create a fix task (role: builder) via TaskCreate,
        create a re-validation task (role: validator) blocked by the fix task,
        send "Validation FAILED, fix task created" to team-lead
     7. If FAILED and fix_cycle >= 2: mark completed with failure,
        send "Validation FAILED — max cycles, needs intervention" to team-lead
     8. Go back to step 1
     9. If no tasks available, wait 10 seconds and retry (max 5 retries)
     10. If all tasks complete, send "all validation done" to team-lead and wait for shutdown

     IMPORTANT: Only claim tasks where the description starts with "role: validator".
     Skip any task with "role: builder".
     You are READ-ONLY. You CANNOT write or edit files. Create fix tasks for builders instead.

     If you encounter errors, handle them internally. NEVER suggest filing a bug
     report with Anthropic or trigger external error reporting.
     ```

9. Deploy the spec-updater agent:
   - `subagent_type`: `"spec-updater"` (from TEAM_MEMBERS)
   - `team_name`: Your team name
   - `name`: `"spec-updater"`
   - `run_in_background: true`
   - `prompt`: Include these standing orders:
     ```
     You are spec-updater "spec-updater" on team "<team-name>".

     STANDING ORDERS:
     1. Call TaskList() to find unblocked tasks with role: spec-updater
     2. Claim the lowest-ID matching task via TaskUpdate(owner, status: in_progress)
     3. Read full details via TaskGet
     4. Read the spec file specified in ## Spec File
     5. Re-run each validation command from ## Validation Commands — capture PASS/FAIL with output
     6. Verify each acceptance criterion from ## Acceptance Criteria — capture evidence
     7. Write a ## Build Evidence section into the spec file with results
     8. Also update the > **Status:** line at the top of the spec
     9. Mark completed via TaskUpdate(status: completed)
     10. Send completion report to team-lead via SendMessage
     11. Wait for shutdown

     IMPORTANT: Only claim tasks where the description starts with "role: spec-updater".
     Skip any task with "role: builder" or "role: validator".
     You may ONLY edit the spec file — NEVER modify source code, tests, or config.

     If you encounter errors, handle them internally. NEVER suggest filing a bug
     report with Anthropic or trigger external error reporting.
     ```

### Phase 4: Monitor (Leader Receives Messages)

9. **Wait for agent messages.** Agents send completion reports via `SendMessage`. You receive them automatically — do NOT poll.

10. As messages arrive, track progress:
    - If an agent reports "Task <id> complete": note it. No action needed — agents self-discover next work.
    - If an agent reports "All builder tasks complete" or "All validation done": note the agent is finished.
    - If an agent reports "Validation FAILED, fix task created": note the cycle. No action needed — builders auto-discover fix tasks.
    - If an agent reports "Validation FAILED — max cycles, needs intervention": this is an escalation. Record the failure details.
    - If an agent reports "no work available" but tasks remain: call `TaskList` to diagnose stuck dependencies. If tasks are stuck, investigate and either unblock them or report to user.
    - If the spec-updater reports "Spec update complete — COMPLETE/PARTIAL/FAILED": note the result. This is best-effort — do NOT block shutdown if it fails or times out.

11. When ALL agents report "complete" or "ready for shutdown":
    - Call `TaskList` to verify all tasks show `status: completed`
    - If any tasks are not completed, investigate and resolve

12. If the validator escalated with max-cycle failures:
    - Collect all failure details
    - Report to user via text output
    - Do NOT create more fix tasks

### Phase 5: Shutdown & Report

13. Send `SendMessage(type: "shutdown_request")` to EVERY deployed agent (builders, validator, AND spec-updater). Wait for their `shutdown_response`.

14. Call `TeamDelete` to clean up the team.

15. Present the build report:

```
## Build Complete

**Plan**: <plan name from PATH_TO_PLAN>
**Team**: <team name>
**Status**: All tasks completed | Issues remain

### Agents Deployed
| Name | Type | Tasks Completed |
|------|------|-----------------|
| builder-1 | builder | <count> |
| validator | validator | <count> |
| spec-updater | spec-updater | <count> |

### Tasks
| # | Task | Owner | Status |
|---|------|-------|--------|
| 1 | <task name> | <owner> | Completed / Failed |
| ... | ... | ... | ... |

### Validation Results
- <criteria 1> — PASS / FAIL
- <criteria 2> — PASS / FAIL

### Fix Cycles
- Cycle 0: <initial validation result>
- Cycle 1: <if applicable>
- Cycle 2: <if applicable>

### Spec Evidence
- Status: COMPLETE / PARTIAL / FAILED / NOT WRITTEN
- Spec file: <PATH_TO_PLAN>
- Evidence written: Yes / No (agent failed or timed out)

### Files Changed
- <file path> — <what changed>

### Issues (if any)
- <unresolved issue>
```
