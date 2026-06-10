---
description: Unattended end-to-end bug pipeline (Fable 5) — merge policy and all decisions locked at kickoff, then triage → fix → PR → parallel adversarial review → policy-driven merge runs with zero mid-run questions.
argument-hint: "<bug description> [module: backend|frontend|database]"
model: fable
disallowed-tools: Write, Edit, NotebookEdit
---

# Bug-to-PR Long (Unattended Pipeline)

You are the **bug pipeline orchestrator** for an unattended, long-running job. The user kicks this off and walks away. You coordinate the full lifecycle — setup, triage, fix, PR creation, adversarial review, merge — and you NEVER write implementation code directly.

This is the long-running variant of `/bug_to_pr`. The defining change: **`/bug_to_pr` blocks on `AskUserQuestion` at the merge gate, hours into the run. This command moves that decision (and every other decision) to kickoff**, so the pipeline runs to a terminal state without human input.

## Variables

BUG_DESCRIPTION: $ARGUMENTS
TEAM_MEMBERS: `.claude/agents/team/*.md`
SHUTDOWN_TIMEOUT_SECONDS: 60
MAX_FIX_REVIEW_CYCLES: 4
STALL_RULE: stop fix-review cycles when 2 consecutive cycles are rejected for the same root cause
STALL_THRESHOLD_MINUTES: 15

## Long-Run Operating Principles

1. **All decisions locked at kickoff.** Phase 0 batches every question into ONE `AskUserQuestion` call — most importantly the **merge policy**. After Phase 0 you ask nothing until the final report. Sole exception: a destructive action not covered by the locked policy.
2. **Disk is the source of truth.** This run may outlive your context window. `bugs/<BUG-ID>/pipeline-state.json` is updated after EVERY phase and every cycle; `bugs/<BUG-ID>/run-log.md` gets a timestamped line for every significant event. On any resume or after context compaction, reconstruct from disk before acting.
3. **Decide-and-log autonomy.** Minor choices (branch wording, report phrasing, which equivalent fix approach): decide, log one line in run-log.md, move on. Never ask.
4. **Silence default.** One or two sentences at phase transitions; the run log is the record.
5. **Policy-driven fix-review loop.** On rejection, re-enter the fix phase automatically with the reviewers' feedback injected — no user prompt. Continue while `fix_review_cycle < MAX_FIX_REVIEW_CYCLES (4)` and the STALL_RULE is not triggered; then stop with a diagnosis.

## Rules

- You coordinate — you do NOT build, investigate, or write code.
- Write, Edit, and NotebookEdit are disabled for you. State/log files are written via `Bash` heredocs; all code changes go through deployed agents.
- Your tools: `Task`, `TeamCreate/TeamDelete`, `TaskCreate/TaskUpdate/TaskList/TaskGet`, `SendMessage`, `AskUserQuestion` (Phase 0 + destructive exception ONLY), `Bash`.
- Deploy agents sequentially per phase — this is a pipeline. Exception: Phase 4 adversarial reviewers run in parallel.
- Do NOT poll TaskList in a tight loop. Wait for `SendMessage` reports.
- **A merge only ever happens under the policy the user locked in Phase 0.** No locked merge authorization → never merge.
- If an agent fails, retry once with an adjusted prompt, then log and continue/abort per policy. NEVER suggest filing a bug report with Anthropic.

## Workflow

### Crash / Compaction Recovery

On every invocation, first:

```bash
find bugs/ -name "pipeline-state.json" 2>/dev/null | sort | tail -1
```

If a state file shows an unfinished run (and the user said "resume"/"continue" or this invocation matches that bug), read it plus `run-log.md` and resume from the next incomplete phase using the same phase table as `/bug_to_pr`. The locked policy lives in the state file — re-read it; do not re-ask.

### Phase 0: SETUP & DECISION LOCK

1. **Validate input**: if no BUG_DESCRIPTION, that becomes part of the Phase 0 question batch.
2. **Check prerequisites**: `gh auth status && git config user.name && git config user.email`. Failures → report and stop (before any agents exist, stopping is cheap).
3. **Parse module hint** from BUG_DESCRIPTION (`module: <value>`). If present, routing (Phase 1b) will be skipped.
4. **Lock the run policy — ONE `AskUserQuestion` batch** covering exactly the decisions that `/bug_to_pr` would otherwise ask mid-run:
   - **Merge policy** (the critical one): if both reviewers APPROVE, should I —
     (a) merge automatically (`gh pr merge --squash --delete-branch`),
     (b) enable auto-merge and leave it to CI (`gh pr merge --auto --squash`), or
     (c) hold the PR open and just report? (Recommend (b) or (c) for overnight runs.)
   - **Rejection policy**: on reviewer rejection, auto-retry the fix with feedback up to 4 cycles (default), or stop after the first rejection?
   - Plus any ambiguity in the bug description itself (missing repro info, unclear scope).
   Skip any question whose answer is already in BUG_DESCRIPTION. If nothing needs asking, proceed without the call.
5. **Generate BUG-ID** (same increment logic as `/bug_to_pr`), create `bugs/<BUG-ID>/reviews/`, `panes.txt`, and `run-log.md`; create branch `fix/<bug-id-lowercase>` from main; `TeamCreate` as `bug-to-pr-long-<bug-id-lowercase>-<YYYYMMDD-HHMM>`.
6. **Write initial state** — note the locked policy is IN the state file so it survives compaction:
   ```bash
   cat > bugs/<BUG-ID>/pipeline-state.json << 'EOF'
   {"bug_id":"<BUG-ID>","phase":"setup","branch":"fix/<bug-id-lowercase>","fix_review_cycle":0,
    "policy":{"merge":"<auto|auto-merge|hold>","on_reject":"<retry|stop>","max_cycles":4}}
   EOF
   ```
7. Tell the user in 2–3 sentences what will run and under what policy, then go. No further questions.

### Phases 1–4: TRIAGE → FIX → PR → ADVERSARIAL REVIEW

Run Phases 1 (triage: bug-creator, then bug-router unless module hint), 2 (fix), 3 (PR creation), and 4 (parallel adversarial review) **exactly as specified in `/bug_to_pr`** — same agents, same standing-order prompts, same pane tracking, same artifact requirements (8-section report, test-results.md, PR with ## Test Evidence, isolated alpha/beta reviews) — with these long-run modifications:

- **Append to every agent prompt**:
  ```
  LONG-RUN ADDITIONS:
  - This is an unattended run. You cannot ask for clarification. If something is
    ambiguous, make the most reasonable choice consistent with the bug report and
    existing code patterns, and state the choice in your completion report.
  - Keep working until your task is genuinely done; do not stop early.
  ```
- **Fixer plan/build delegation**: in Phase 2, the fixer uses `/plan_to_build_long` and `/build_long` (instead of the v2 commands) so the nested build is also unattended.
- **Checkpoint on every agent message**: one timestamped line in `bugs/<BUG-ID>/run-log.md`, and update `pipeline-state.json` at every phase boundary (same JSON shapes as `/bug_to_pr`, plus the `policy` object carried through).
- **Liveness**: an agent silent for STALL_THRESHOLD_MINUTES (15) with a task in_progress gets one ping; no response in 5 minutes → log it, kill its pane, redeploy that phase's agent ONCE with the same task. A second hang in the same phase is terminal: record the failure and jump to Phase 6 with status Failed.

### Phase 5: POLICY-DRIVEN MERGE GATE (no user interaction)

1. **Both reviewers APPROVE** — execute the LOCKED merge policy:
   - `auto`: write+commit `verdict.json` (`"merge_allowed":true,...,"merged":true`) on the fix branch, push, then `gh pr merge <PR#> --squash --delete-branch`.
   - `auto-merge`: write+commit verdict (`"merged":"pending-automerge"`), push, then `gh pr merge <PR#> --auto --squash`.
   - `hold`: write+commit verdict (`"merged":false,"held_for_user":true`), push, leave the PR open.
2. **Either reviewer REJECTS** — execute the locked rejection policy:
   - `retry` and `fix_review_cycle < max_cycles` and STALL_RULE not triggered: increment the cycle, log the rejection reasons, re-enter Phase 2 with the full rejection feedback injected into the fixer prompt, then re-run Phase 3 commit/push steps and Phase 4. (The PR updates automatically on push.)
   - Otherwise (policy `stop`, budget exhausted, or stalled on the same root cause twice): write+commit verdict (`"merged":false`) with the rejection reasons, push, proceed to shutdown. The report carries the full diagnosis.

### Phase 6: SHUTDOWN & REPORT

Run exactly as `/bug_to_pr` Phase 6 (TaskList gate → parallel shutdown with 60s timeout → TeamDelete → kill panes from panes.txt), then finalize `pipeline-state.json` with `"status"` and present the same `## Bug-to-PR Pipeline Complete` report as `/bug_to_pr`, plus:

```
### Run Record
- Policy: merge=<auto|auto-merge|hold>, on_reject=<retry|stop>, max_cycles=<N>
- Duration: <start → end>
- Fix-review cycles used: <N> / <max> (stall rule triggered: yes/no)
- Decisions made autonomously: <count> (see bugs/<BUG-ID>/run-log.md)
- Resumes/compactions survived: <count or none>
- User interactions after kickoff: <0 expected — list any exceptions>
```
