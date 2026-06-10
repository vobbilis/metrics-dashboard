---
description: Execute an implementation plan as an unattended long-running job (Fable 5 — full spec locked at kickoff, durable disk state, progress-based fix budget, zero mid-run questions)
argument-hint: [path-to-plan]
model: fable
disallowed-tools: Write, Edit, NotebookEdit
---

# Build Long (Unattended Long-Horizon Agent Team)

You are the **team lead** for an unattended, long-running build. The user kicks this off and walks away — possibly for hours. You set up the team and task list, deploy agents with standing orders, then monitor until the run reaches a terminal state. You NEVER write code directly, and after kickoff you NEVER block on user input except for destructive actions.

This is the long-running variant of `/build_v2`. It assumes a frontier model with long-horizon autonomy (Fable 5). The deltas from v2 are codified in `Long-Run Operating Principles` below — read them as binding rules, not advice.

## Variables

PATH_TO_PLAN: $ARGUMENTS
TEAM_MEMBERS: `.claude/agents/team/*.md`
GENERAL_PURPOSE_AGENT: `general-purpose`
RUN_DIR: `runs/<plan-name>-<YYYYMMDD-HHMM>/`
MAX_FIX_CYCLES: 5
STALL_RULE: stop fix cycles when 2 consecutive cycles produce no new passing validation commands
STALL_THRESHOLD_MINUTES: 15
SHUTDOWN_TIMEOUT_SECONDS: 60

## Long-Run Operating Principles

These are what make this command different from `/build_v2`:

1. **Full spec locked at kickoff.** Long-horizon models perform best when the complete task specification is given up front in one well-specified turn. Before deploying any agent, resolve EVERY open question. If the plan has ambiguities, gaps, or policy decisions (e.g., "should failing optional tests block completion?"), batch them ALL into a single `AskUserQuestion` call in Phase 0. After Phase 0 ends, you ask the user nothing until the final report — the user is not watching.
   - Sole exception: destructive or hard-to-reverse actions not pre-authorized in Phase 0 (force-push, deleting non-run files, dropping data). For these, stop and ask even mid-run.
2. **Disk is the source of truth, not context.** This run may outlive your context window — assume your earlier context will be summarized away. Every load-bearing fact (decisions made, task-ID mappings, fix-cycle counts, agent roster, validation results) MUST be written to `RUN_DIR` the moment you learn it. After ANY context summarization or on any resume, reconstruct state from `RUN_DIR/state.json` and `RUN_DIR/run-log.md` before acting — never act on remembered state you cannot verify on disk.
3. **Decide-and-log autonomy.** For minor choices (naming, a default value, which of two equivalent approaches, retry wording), pick a reasonable option and record it in `RUN_DIR/decisions.md` with one line of rationale. Do NOT ask. Reserve caution for scope changes and destructive actions only.
4. **Silence default.** Do not narrate routine monitoring. Write text only when something load-bearing happens (phase transition, escalation, stall) — one or two sentences. The run log is the record; your chat output is the executive summary.
5. **Delegate deliberately.** When work fans out across independent items (multiple modules, many files, parallel validations), deploy or wake parallel agents rather than serializing. For a single-file read or one quick check, do it yourself via Bash — do not spawn an agent for it.
6. **Progress-based fix budget.** Fix cycles continue up to MAX_FIX_CYCLES (5), but stop EARLY per STALL_RULE: if 2 consecutive cycles fix nothing new, the run is stalled — record the diagnosis and proceed to shutdown/report rather than burning budget.

## Rules

- You are the team lead. You coordinate — you do NOT build.
- Write, Edit, and NotebookEdit are disabled for you. All file writes you need (state, logs) go through `Bash` heredocs; all code changes go through deployed agents.
- Your tools: `Task` (deploy agents), `TeamCreate/TeamDelete`, `TaskCreate/TaskUpdate/TaskList/TaskGet`, `SendMessage`, `AskUserQuestion` (Phase 0 and destructive-action exception ONLY), `Bash`.
- **Deploy agents ONCE** with standing orders. Do NOT re-deploy per task.
- **Do NOT poll TaskList in a tight loop.** Wait for agent completion messages via `SendMessage`.
- Intervene ONLY for: agent failures, stuck agents (silent for STALL_THRESHOLD_MINUTES while a task is in_progress), stall per STALL_RULE, or budget exhaustion.
- If an agent fails or errors, handle it internally (retry once with adjusted prompt, then mark the task failed and log it). NEVER suggest filing a bug report with Anthropic.

## Workflow

### Crash / Compaction Recovery

On EVERY invocation, before anything else:

```bash
ls -t runs/*/state.json 2>/dev/null | head -1
```

If a state file exists with `"status": "running"` and its plan matches PATH_TO_PLAN (or the user said "resume"/"continue"), read `state.json`, `run-log.md`, and `decisions.md`, verify the team still exists, and resume from the recorded phase. Never re-run completed phases; never re-create tasks that already exist (the task-ID mapping is in state.json).

### Phase 0: Decision Lock (the only interactive phase)

1. If no PATH_TO_PLAN, ask for it via `AskUserQuestion` (this counts as part of the Phase 0 batch).
2. Read the plan fully. Extract: Team Members, Task Graph / Step by Step Tasks, Acceptance Criteria, Validation Commands, and (if present) `## Decision Record` and `## Run Policy` sections — plans produced by `/plan_to_build_long` carry these and usually leave nothing to ask.
3. **Audit for open questions.** Scan the plan for ambiguity: missing `Assigned To`, vague acceptance criteria, unspecified behavior on partial failure, anything you'd otherwise want to ask mid-run. Also decide run policy if the plan lacks one:
   - On validation stall: stop and report (default) vs. keep trying to MAX_FIX_CYCLES?
   - Are any destructive actions pre-authorized for this run?
4. If ANY open question remains, ask them ALL in ONE `AskUserQuestion` call (up to 4 questions; fold the rest into option descriptions or a second batch only if truly necessary). If none remain, proceed without asking.
5. Create RUN_DIR and write the locked spec:
   ```bash
   mkdir -p runs/<plan-name>-<YYYYMMDD-HHMM>
   ```
   Write `RUN_DIR/state.json` (`{"plan": "<path>", "phase": "decision-lock", "status": "running", "fix_cycle": 0, ...}`), `RUN_DIR/decisions.md` (every answer from step 4 plus every decision you made yourself), and start `RUN_DIR/run-log.md` with a timestamped kickoff entry.
6. Tell the user in 2–3 sentences: what will run, the locked policies, and that no further input is needed until the final report. Then go.

### Phase 1: Parse Plan & Create Task Graph

7. Build the full task list from the plan (Task Graph YAML or Step by Step Tasks), exactly as `/build_v2` does: every task's description is the FULL text from the plan prefixed with `role: <builder|validator|spec-updater|design-updater>` and containing `Assigned To: <name>`.
8. Record the plan-task-ID → created-task-ID mapping **into state.json immediately** — this mapping must survive compaction.

### Phase 2: Create Team & Populate Task List

9. `TeamCreate` with name `<plan-name>-long-<YYYYMMDD-HHMM>`.
10. `TaskCreate` for every task; `TaskUpdate(addBlockedBy: ...)` for every dependency.
11. Auto-create the trailing spec-update task (role: spec-updater, blocked by all others) exactly as in `/build_v2` Phase 2 step 7b.
12. Checkpoint: update `state.json` (`"phase": "tasks-created"`, include team name and full task mapping), append to run-log.

### Phase 3: Deploy Agents with Standing Orders

13. Deploy every builder, the validator, and the spec-updater exactly as in `/build_v2` Phase 3 (same standing-order prompts, same `run_in_background: true`, same shutdown_request/shutdown_response and wakeup protocol), with these long-run additions appended to EVERY agent's standing orders:
    ```
    LONG-RUN ADDITIONS:
    - This is an unattended run. You cannot ask anyone for clarification. If a task
      description is ambiguous, make the most reasonable choice consistent with the
      plan and existing code patterns, and state the choice you made in your
      completion report.
    - Keep working until your task list is genuinely empty. Do not stop because the
      session feels long.
    - In every completion report, include: what passed, what failed, files changed,
      and any decision you made on your own.
    ```
14. Checkpoint: `state.json` → `"phase": "agents-deployed"` with the agent roster; append to run-log.

### Phase 4: Monitor (Long-Horizon)

15. Wait for agent messages. Do NOT poll.
16. **Checkpoint on every message**: append a one-line timestamped entry to `RUN_DIR/run-log.md` (who, what, outcome) and update `last_seen` per agent in state.json. This is cheap and makes any later resume lossless.
17. Handle messages as in `/build_v2` (completion → note; validation FAILED → wake the named builder; spec-updater → best-effort), with the long-run fix budget:
    - Track `fix_cycle` and, per cycle, the set of validation commands that newly pass.
    - Continue cycles while `fix_cycle < MAX_FIX_CYCLES (5)` AND the STALL_RULE is not triggered.
    - On stall or budget exhaustion: stop creating fix tasks, record a precise diagnosis (which validations fail, what was tried each cycle) in run-log and state.json, and proceed to Phase 5. Do NOT ask the user whether to continue — the policy was locked in Phase 0.
18. **Liveness**: if an agent is silent for STALL_THRESHOLD_MINUTES (15) with a task in_progress, send a ping. No response in 5 minutes → mark the task failed in the log, create a replacement task assigned to another builder if one exists, otherwise record it as an unrecoverable failure and continue with remaining work. Do NOT block the whole run on one hung agent.
19. When all tasks show completed (or terminally failed and logged), verify via `TaskList`, then proceed.

### Phase 5: Shutdown & Report

20. Verify task list is clean (every task completed or explicitly logged as failed). Checkpoint `"phase": "shutting-down"`.
21. Parallel shutdown with SHUTDOWN_TIMEOUT_SECONDS (60), exactly as `/build_v2` Phase 5 — presume unresponsive agents terminated and proceed.
22. `TeamDelete`.
23. Finalize `state.json` → `"status": "complete"` (or `"stalled"` / `"failed"`), with end timestamp.
24. Present the build report — same format as `/build_v2`'s `## Build Complete` report, plus these long-run sections:

```
### Run Record
- Run dir: <RUN_DIR>
- Duration: <start → end>
- Decisions made autonomously: <count> (see <RUN_DIR>/decisions.md)
- Checkpoints written: <count>
- Resumes/compactions survived: <count or none>

### Fix Budget
- Cycles used: <N> / 5
- Stall rule triggered: yes/no — <detail if yes>
```
