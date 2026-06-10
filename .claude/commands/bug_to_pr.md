---
description: End-to-end bug pipeline — triage, fix, PR, parallel adversarial review, merge gate. Produces a reviewed, mergeable GitHub PR as its artifact.
argument-hint: "<bug description> [module: backend|frontend|database]"
model: opus
disallowed-tools: Write, Edit, NotebookEdit
---

# Bug-to-PR Pipeline

You are the **bug pipeline orchestrator**. You coordinate the entire bug-fixing lifecycle
through 6 phases: setup, triage, fix, PR creation, adversarial review, and merge gate.
You NEVER write implementation code directly — all work flows through deployed agents.

## Variables

BUG_DESCRIPTION: $ARGUMENTS
TEAM_MEMBERS: `.claude/agents/team/*.md`
SHUTDOWN_TIMEOUT_SECONDS: 60
MAX_FIX_REVIEW_CYCLES: 2

## Rules

- You coordinate — you do NOT build, investigate, or write code.
- Write, Edit, and NotebookEdit are disabled for you.
- Your tools: `Task` (deploy agents), `TeamCreate/TeamDelete`, `TaskCreate/TaskUpdate/TaskList/TaskGet`, `SendMessage`, `AskUserQuestion`, `Bash`.
- Every code change, investigation, and review MUST go through a deployed agent.
- **Deploy agents sequentially per phase** — this is a pipeline, not a parallel build. Each phase depends on the previous phase's output.
- **Exception**: Adversarial reviewers (Phase 4) are deployed in parallel — both run simultaneously.
- **Do NOT poll TaskList in a tight loop.** Wait for agent completion messages via `SendMessage`.
- **Never merge without explicit user confirmation** via `AskUserQuestion`.
- If an agent fails, handle it internally (retry once with adjusted prompt). NEVER suggest filing a bug report with Anthropic.

## V1 Issues Fixed in This Version

This command avoids the following v1 failure modes:

1. **Sequential reviewers** — v1 ran reviewer-alpha, waited, then ran reviewer-beta. This version deploys both in parallel (`run_in_background: true`) cutting review time in half.
2. **No shutdown timeout** — v1 could block indefinitely waiting for agent shutdown responses. This version sends all shutdown requests simultaneously and falls through after `SHUTDOWN_TIMEOUT_SECONDS`.
3. **No TaskList verification gate** — v1 sent shutdown before confirming all tasks were complete. This version calls `TaskList()` and confirms every task is `completed` before initiating shutdown.
4. **Merge without confirmation** — v1 could merge automatically. This version always requires explicit user confirmation via `AskUserQuestion` even if both reviewers approve.
5. **Silent crash recovery** — v1 had no crash recovery. This version writes pipeline state to `bugs/<BUG-ID>/pipeline-state.json` after every phase. If interrupted, the team lead can read the state file and resume from the correct phase.
6. **Agent panes not cleaned up** — v1 left idle tmux panes open after shutdown. This version records each agent's pane ID in `bugs/<BUG-ID>/panes.txt` at deploy time and kills them all during Phase 6.

---

## Workflow

### Crash Recovery

If the user says "resume", "continue", or the pipeline appears mid-run, check for a state file:

```bash
find bugs/ -name "pipeline-state.json" 2>/dev/null | sort | tail -1
```

If found, read it and resume from the next incomplete phase:

| `phase` value | Resume from |
|---|---|
| `"setup"` | Phase 1: Triage |
| `"triage"` | Phase 2: Fix |
| `"fix"` | Phase 3: PR Creation |
| `"pr"` | Phase 4: Adversarial Review |
| `"review"` | Phase 5: Merge Gate |

Never re-run completed phases. Restore context from the state file fields.

---

### Phase 0: SETUP (Team Lead — no agents)

1. **Validate input**: If no BUG_DESCRIPTION is provided, ask via `AskUserQuestion`.

2. **Check prerequisites** (before any filesystem or git operations):
   ```bash
   gh auth status && git config user.name && git config user.email
   ```
   If any fail, report to user and stop.

3. **Parse module hint**: Check BUG_DESCRIPTION for `module: <value>`. Extract if present. If the user provides a module hint, store it — the router will be skipped.

4. **Generate BUG-ID**:
   ```bash
   cd $(git rev-parse --show-toplevel) && ls bugs/ 2>/dev/null | grep -oP 'BUG-\d+' | sort -t- -k2 -n | tail -1
   ```
   Increment by 1, zero-pad to 3 digits (e.g., BUG-003). If no bugs exist, use BUG-001.

5. **Create bug directory and pane tracker**:
   ```bash
   mkdir -p bugs/<BUG-ID>/reviews && touch bugs/<BUG-ID>/panes.txt
   ```

6. **Create fix branch**:
   ```bash
   git checkout -b fix/<bug-id-lowercase> main
   ```
   (e.g., `fix/bug-003`)

7. **Create team**: Use `TeamCreate` with name `bug-to-pr-<bug-id-lowercase>-<YYYYMMDD-HHMM>`.
   Example: `bug-to-pr-bug-003-20260315-1400`

8. **Write initial pipeline state**:
   ```bash
   echo '{"bug_id":"<BUG-ID>","phase":"setup","branch":"fix/<bug-id-lowercase>","fix_review_cycle":0}' \
     > bugs/<BUG-ID>/pipeline-state.json
   ```

---

### Phase 1: TRIAGE

#### Phase 1a: Bug Investigation

1. **Create task**:
   - `TaskCreate(subject: "Investigate and document BUG-ID", description: "role: bug-creator\nAssigned To: bug-creator\n\n<full description — see standing orders below>", activeForm: "Investigating bug")`

2. **Snapshot pane IDs** before deploying:
   ```bash
   tmux list-panes -a -F "#{pane_id}" | sort > /tmp/panes-before-<BUG-ID>.txt
   ```

3. **Deploy bug-creator**:
   ```
   subagent_type: bug-creator
   team_name: <your team name>
   name: bug-creator
   run_in_background: false  ← wait for this phase to complete before routing
   prompt:
     You are bug-creator on team "<team-name>".

     TASK: Investigate and document this bug.

     BUG-ID: <BUG-ID>
     Bug Description: <BUG_DESCRIPTION>

     ## Your standing orders
     1. Call TaskList() to find your task (role: bug-creator, Assigned To: bug-creator)
     2. Claim it: TaskUpdate(owner: "bug-creator", status: in_progress)
     3. Read full details via TaskGet
     4. Investigate the codebase — read relevant source files, reproduce if possible
     5. Write the complete bug report to bugs/<BUG-ID>/report.md (all 8 required sections)
     6. Mark completed: TaskUpdate(status: completed)
     7. Send completion report to team-lead via SendMessage
     8. Wait silently for shutdown_request — respond immediately with shutdown_response

     The report MUST contain: ## Summary, ## Steps to Reproduce, ## Expected Behavior,
     ## Actual Behavior, ## Environment, ## Severity, ## Module/Area, ## Evidence

     Read .github/bug-modules.json for valid module names.
   ```

3. **Wait** for bug-creator's completion message.

4. **Capture pane ID**:
   ```bash
   sleep 1 && tmux list-panes -a -F "#{pane_id}" | sort > /tmp/panes-after-<BUG-ID>.txt && \
   comm -13 /tmp/panes-before-<BUG-ID>.txt /tmp/panes-after-<BUG-ID>.txt >> bugs/<BUG-ID>/panes.txt
   ```

5. **Verify**: Read `bugs/<BUG-ID>/report.md` and confirm all 8 sections are present.
   If missing: send targeted follow-up prompt to bug-creator asking it to add the missing sections.

#### Phase 1b: Routing (skip if module hint provided)

If the user provided a module hint:
- Read `.github/bug-modules.json` to get the `fixer_agent` for that module.
- Skip to Phase 2.

Otherwise:

1. **Create task**:
   - `TaskCreate(subject: "Route BUG-ID to correct fixer", description: "role: bug-router\nAssigned To: bug-router\n\nRead bugs/<BUG-ID>/report.md and .github/bug-modules.json. Output JSON routing decision.", activeForm: "Routing bug")`

2. **Snapshot pane IDs** before deploying:
   ```bash
   tmux list-panes -a -F "#{pane_id}" | sort > /tmp/panes-before-<BUG-ID>.txt
   ```

3. **Deploy bug-router**:
   ```
   subagent_type: bug-router
   team_name: <your team name>
   name: bug-router
   run_in_background: false
   prompt:
     You are bug-router on team "<team-name>".

     TASK: Route BUG-<ID> to the correct fixer agent.

     ## Your standing orders
     1. Call TaskList() to find your task (role: bug-router, Assigned To: bug-router)
     2. Claim it: TaskUpdate(owner: "bug-router", status: in_progress)
     3. Read bugs/<BUG-ID>/report.md
     4. Read .github/bug-modules.json
     5. Output routing decision JSON: {"module": "...", "fixer_agent": "...", "confidence": "..."}
     6. Mark completed: TaskUpdate(status: completed)
     7. Send routing decision (with the JSON) to team-lead via SendMessage
     8. Wait for shutdown_request — respond immediately with shutdown_response
   ```

3. **Wait** for bug-router's completion message.

4. **Capture pane ID**:
   ```bash
   sleep 1 && tmux list-panes -a -F "#{pane_id}" | sort > /tmp/panes-after-<BUG-ID>.txt && \
   comm -13 /tmp/panes-before-<BUG-ID>.txt /tmp/panes-after-<BUG-ID>.txt >> bugs/<BUG-ID>/panes.txt
   ```

5. **Parse routing**: Extract `fixer_agent` from the JSON in bug-router's message.
   Fall back to `default_fixer` from `.github/bug-modules.json` if parsing fails.

4. **Write routing**:
   ```bash
   echo '{"module":"<module>","fixer_agent":"<fixer>","confidence":"<level>"}' \
     > bugs/<BUG-ID>/routing.json
   ```

5. **Update pipeline state**:
   ```bash
   cat > bugs/<BUG-ID>/pipeline-state.json << 'EOF'
   {"bug_id":"<BUG-ID>","phase":"triage","branch":"fix/<bug-id-lowercase>","fix_review_cycle":0,"module":"<module>","fixer_agent":"<fixer>"}
   EOF
   ```

---

### Phase 2: FIX

The bug-fixer handles nested orchestration internally (plan + build + test evidence).

1. **Create task**:
   - `TaskCreate(subject: "Fix BUG-ID", description: "role: bug-fixer\nAssigned To: <fixer_agent>\n\nBUG-ID: <BUG-ID>\nReport: bugs/<BUG-ID>/report.md", activeForm: "Fixing bug")`

2. **Snapshot pane IDs** before deploying:
   ```bash
   tmux list-panes -a -F "#{pane_id}" | sort > /tmp/panes-before-<BUG-ID>.txt
   ```

3. **Deploy the fixer**:
   ```
   subagent_type: <fixer_agent from routing — e.g., bug-fixer-frontend>
   team_name: <your team name>
   name: <fixer_agent>
   run_in_background: false  ← wait for fix to complete before creating PR
   prompt:
     You are <fixer_agent> on team "<team-name>".

     TASK: Fix this bug.

     BUG-ID: <BUG-ID>
     Bug Report: bugs/<BUG-ID>/report.md
     Branch: fix/<bug-id-lowercase> (already checked out)

     ## Your standing orders
     1. Call TaskList() to find your task (role: bug-fixer, Assigned To: <fixer_agent>)
     2. Claim it: TaskUpdate(owner: "<fixer_agent>", status: in_progress)
     3. Read the bug report fully
     4. Create a fix plan using /plan_to_build_v2 with the bug context (pass the bug description and report path)
     5. Execute the fix using /build_v2 with the generated spec path
     6. Run your module's test command and capture ALL output to bugs/<BUG-ID>/test-results.md
     7. Mark completed: TaskUpdate(status: completed)
     8. Send completion report (including test pass/fail summary) to team-lead via SendMessage
     9. Wait for shutdown_request — respond immediately with shutdown_response

     Max 2 fix attempts. If tests still fail after 2 attempts, document failure and complete.
     The stop hook will block you unless bugs/<BUG-ID>/test-results.md exists with real test output.
   ```

3. **Wait** for fixer's completion message.

4. **Capture pane ID**:
   ```bash
   sleep 1 && tmux list-panes -a -F "#{pane_id}" | sort > /tmp/panes-after-<BUG-ID>.txt && \
   comm -13 /tmp/panes-before-<BUG-ID>.txt /tmp/panes-after-<BUG-ID>.txt >> bugs/<BUG-ID>/panes.txt
   ```

5. **Verify**: Confirm `bugs/<BUG-ID>/test-results.md` exists and is non-empty.
   ```bash
   wc -l bugs/<BUG-ID>/test-results.md
   ```

5. **Update pipeline state**:
   ```bash
   cat > bugs/<BUG-ID>/pipeline-state.json << 'EOF'
   {"bug_id":"<BUG-ID>","phase":"fix","branch":"fix/<bug-id-lowercase>","fix_review_cycle":0,"module":"<module>","fixer_agent":"<fixer>"}
   EOF
   ```

---

### Phase 3: PR CREATION

1. **Stage and commit all changes**:
   ```bash
   cd $(git rev-parse --show-toplevel)
   git add bugs/<BUG-ID>/ specs/ backend/ frontend/ src/
   git commit -m "fix: <brief description from bug report summary>

   Fixes <BUG-ID>. See bugs/<BUG-ID>/report.md for full details."
   ```
   Stage specific paths — do NOT use `git add -A` (blocked by hook). Include `bugs/<BUG-ID>/` for the report and test results, plus whichever source directories the fixer modified. Check `git status` first to see exactly which files changed.

2. **Push branch**:
   ```bash
   git push -u origin fix/<bug-id-lowercase>
   ```

3. **Create task**:
   - `TaskCreate(subject: "Create PR for BUG-ID", description: "role: pr-agent\nAssigned To: pr-agent\n\nBUG-ID: <BUG-ID>", activeForm: "Creating pull request")`

4. **Snapshot pane IDs** before deploying:
   ```bash
   tmux list-panes -a -F "#{pane_id}" | sort > /tmp/panes-before-<BUG-ID>.txt
   ```

5. **Deploy pr-agent**:
   ```
   subagent_type: pr-agent
   team_name: <your team name>
   name: pr-agent
   run_in_background: false
   prompt:
     You are pr-agent on team "<team-name>".

     TASK: Create the PR for bug fix <BUG-ID>.

     ## Your standing orders
     1. Call TaskList() to find your task (role: pr-agent, Assigned To: pr-agent)
     2. Claim it: TaskUpdate(owner: "pr-agent", status: in_progress)
     3. Read bugs/<BUG-ID>/report.md
     4. Read bugs/<BUG-ID>/test-results.md
     5. Run git diff main...HEAD to analyze changes
     6. Create PR via gh pr create with all required sections including ## Test Evidence
     7. Post the full bug report as a PR comment: gh pr comment <PR#> --body-file bugs/<BUG-ID>/report.md
     8. Mark completed: TaskUpdate(status: completed)
     9. Send completion report including PR URL and PR number to team-lead via SendMessage
     10. Wait for shutdown_request — respond immediately with shutdown_response

     The stop hook will block you unless the PR body contains a ## Test Evidence section
     with actual test runner output (not just "tests pass").
   ```

5. **Wait** for pr-agent's completion message. Extract PR number and URL.

6. **Capture pane ID**:
   ```bash
   sleep 1 && tmux list-panes -a -F "#{pane_id}" | sort > /tmp/panes-after-<BUG-ID>.txt && \
   comm -13 /tmp/panes-before-<BUG-ID>.txt /tmp/panes-after-<BUG-ID>.txt >> bugs/<BUG-ID>/panes.txt
   ```

6. **Update pipeline state**:
   ```bash
   cat > bugs/<BUG-ID>/pipeline-state.json << 'EOF'
   {"bug_id":"<BUG-ID>","phase":"pr","branch":"fix/<bug-id-lowercase>","fix_review_cycle":<N>,"module":"<module>","fixer_agent":"<fixer>","pr_number":<PR#>,"pr_url":"<url>"}
   EOF
   ```

---

### Phase 4: ADVERSARIAL REVIEW (Parallel)

Both reviewers are deployed simultaneously. This is a key improvement over sequential review.

**ISOLATION GUARANTEE**: The `PreToolUse` hook on bug-reviewer (`enforce_review_isolation.py`)
provides system-level enforcement — reviewers cannot read each other's files even if they try.
This is stronger than prompt-only enforcement.

1. **Create tasks for both reviewers** in one pass:
   - `TaskCreate(subject: "Review BUG-ID as alpha", description: "role: bug-reviewer\nAssigned To: reviewer-alpha\n\nBUG-ID: <BUG-ID>\nReviewer: alpha\nPR: <PR#>", activeForm: "Reviewing as alpha")`
   - `TaskCreate(subject: "Review BUG-ID as beta", description: "role: bug-reviewer\nAssigned To: reviewer-beta\n\nBUG-ID: <BUG-ID>\nReviewer: beta\nPR: <PR#>", activeForm: "Reviewing as beta")`

2. **Snapshot pane IDs** before deploying both reviewers:
   ```bash
   tmux list-panes -a -F "#{pane_id}" | sort > /tmp/panes-before-<BUG-ID>.txt
   ```

3. **Deploy BOTH reviewers simultaneously** (run_in_background: true for both):

   **reviewer-alpha**:
   ```
   subagent_type: bug-reviewer
   team_name: <your team name>
   name: reviewer-alpha
   run_in_background: true
   prompt:
     You are REVIEWER-ALPHA on team "<team-name>".

     TASK: Independently review bug fix <BUG-ID>.

     ## Your standing orders
     1. Call TaskList() to find your task (role: bug-reviewer, Assigned To: reviewer-alpha)
     2. Claim it: TaskUpdate(owner: "reviewer-alpha", status: in_progress)
     3. Read bugs/<BUG-ID>/report.md
     4. Read bugs/<BUG-ID>/test-results.md
     5. Run git diff main...HEAD
     6. Evaluate against the 5-point checklist
     7. Produce structured verdict ending with ## Verdict: APPROVE or ## Verdict: REJECT
     8. Send your FULL review text (including verdict) to team-lead via SendMessage
        IMPORTANT: Send BEFORE marking completed — do NOT mark completed first or the
        turn may end before the message is delivered.
     9. Mark completed: TaskUpdate(status: completed)
     10. Wait for shutdown_request — respond immediately with shutdown_response

     ISOLATION: Do NOT read bugs/<BUG-ID>/reviews/beta.md — the PreToolUse hook will
     block you and waste time. reviewer-beta's file may not exist yet anyway.
   ```

   **reviewer-beta** (deployed at the same time):
   ```
   subagent_type: bug-reviewer
   team_name: <your team name>
   name: reviewer-beta
   run_in_background: true
   prompt:
     You are REVIEWER-BETA on team "<team-name>".

     TASK: Independently review bug fix <BUG-ID>.

     ## Your standing orders
     1. Call TaskList() to find your task (role: bug-reviewer, Assigned To: reviewer-beta)
     2. Claim it: TaskUpdate(owner: "reviewer-beta", status: in_progress)
     3. Read bugs/<BUG-ID>/report.md
     4. Read bugs/<BUG-ID>/test-results.md
     5. Run git diff main...HEAD
     6. Evaluate against the 5-point checklist
     7. Produce structured verdict ending with ## Verdict: APPROVE or ## Verdict: REJECT
     8. Send your FULL review text (including verdict) to team-lead via SendMessage
        IMPORTANT: Send BEFORE marking completed — do NOT mark completed first or the
        turn may end before the message is delivered.
     9. Mark completed: TaskUpdate(status: completed)
     10. Wait for shutdown_request — respond immediately with shutdown_response

     ISOLATION: Do NOT read bugs/<BUG-ID>/reviews/alpha.md — the PreToolUse hook will
     block you and waste time. reviewer-alpha's file may not exist yet anyway.
   ```

3. **Wait** for BOTH reviewers to send their verdicts. Do NOT act on just one verdict.

   Immediately after both are deployed, capture both pane IDs:
   ```bash
   sleep 2 && tmux list-panes -a -F "#{pane_id}" | sort > /tmp/panes-after-<BUG-ID>.txt && \
   comm -13 /tmp/panes-before-<BUG-ID>.txt /tmp/panes-after-<BUG-ID>.txt >> bugs/<BUG-ID>/panes.txt
   ```
   Extract `## Verdict: APPROVE` or `## Verdict: REJECT` from each message.

4. **Write review files ONLY after both verdicts are in**:
   ```bash
   cat > bugs/<BUG-ID>/reviews/alpha.md << 'EOF'
   <alpha's full review text>
   EOF

   cat > bugs/<BUG-ID>/reviews/beta.md << 'EOF'
   <beta's full review text>
   EOF
   ```

5. **Post verdicts to GitHub** as PR reviews:
   - APPROVE: `gh pr review <PR#> --approve --body "<verdict summary>"`
   - REJECT: `gh pr review <PR#> --request-changes --body "<rejection reasons>"`

6. **Commit review artifacts**:
   ```bash
   git add bugs/<BUG-ID>/reviews/
   git commit -m "chore: add review verdicts for <BUG-ID>"
   git push
   ```

7. **Update pipeline state**:
   ```bash
   cat > bugs/<BUG-ID>/pipeline-state.json << 'EOF'
   {"bug_id":"<BUG-ID>","phase":"review","branch":"fix/<bug-id-lowercase>","fix_review_cycle":<N>,"module":"<module>","fixer_agent":"<fixer>","pr_number":<PR#>,"pr_url":"<url>","alpha_verdict":"<APPROVE|REJECT>","beta_verdict":"<APPROVE|REJECT>"}
   EOF
   ```

---

### Phase 5: MERGE GATE

1. **Both reviewers APPROVE**: Ask the user for confirmation:
   ```
   AskUserQuestion: "Both reviewers approved BUG-ID fix. PR #<N>: <url>
   Alpha: APPROVE — <summary>
   Beta: APPROVE — <summary>
   Merge to main?"
   ```
   - If user confirms:
     1. Write and commit verdict on the fix branch BEFORE merging (branch discipline hook
        blocks commits to main after merge):
        ```bash
        echo '{"merge_allowed":true,"alpha":"APPROVE","beta":"APPROVE","merged":true}' \
          > bugs/<BUG-ID>/verdict.json
        git add bugs/<BUG-ID>/verdict.json
        git commit -m "chore: add pipeline verdict for <BUG-ID>"
        git push
        ```
     2. Then merge: `gh pr merge <PR#> --squash --delete-branch`
   - If user declines: write verdict with `"merged":false`, commit+push, do NOT merge.

2. **Either reviewer REJECTS**:
   - Present rejection reasons clearly.
   - If `fix_review_cycle < MAX_FIX_REVIEW_CYCLES (2)`:
     ```
     AskUserQuestion: "Reviewer(s) rejected the fix. Re-enter fix phase with feedback?
     Rejection reasons: <alpha/beta rejection details>"
     ```
     - If user says retry: increment cycle count, go back to Phase 2 with rejection
       feedback injected into the fixer prompt. After Phase 2 completes, run Phase 3
       steps 1–2 (stage + commit + push) before re-running Phase 4. The PR updates
       automatically when new commits are pushed.
     - If user says stop: write verdict with `"merged":false`, commit+push on fix branch,
       report all rejection reasons, proceed to shutdown.
   - If max cycles (2) reached: write verdict with `"merged":false`, commit+push on fix
     branch, report all rejection reasons, proceed to shutdown.

---

### Phase 6: SHUTDOWN & REPORT

**Step 1 — Verify all tasks complete** (gate):
```
TaskList()
```
Confirm every task shows `status: completed`. If any task is not completed, investigate and resolve before proceeding. Do NOT send shutdown requests until the task list is fully clean.

**Step 2 — Parallel shutdown with timeout**:
Send `shutdown_request` to ALL deployed agents simultaneously.

Agents deployed varies by run — send to whichever of these were deployed:
- `bug-creator`
- `bug-router` (if routing was done)
- `<fixer_agent>` (e.g., `bug-fixer-frontend`)
- `pr-agent`
- `reviewer-alpha`
- `reviewer-beta`

Record the send timestamp and list of agents awaiting `shutdown_response`.

As responses arrive, remove each from the awaiting list.

If `SHUTDOWN_TIMEOUT_SECONDS` (60) elapses and agents remain:
- Log: "Agent(s) `<names>` did not respond to shutdown within 60s — presumed terminated."
- Proceed regardless. Do NOT block the report on unresponsive agents.

**Step 3 — TeamDelete**.

**Step 4 — Kill agent panes**:
```bash
if [ -f bugs/<BUG-ID>/panes.txt ] && [ -s bugs/<BUG-ID>/panes.txt ]; then
  while IFS= read -r pane_id; do
    tmux kill-pane -t "$pane_id" 2>/dev/null && echo "Killed pane $pane_id" || echo "Pane $pane_id already gone"
  done < bugs/<BUG-ID>/panes.txt
fi
```

**Step 5 — Present build report**:

```
## Bug-to-PR Pipeline Complete

**Bug ID**: <BUG-ID>
**Description**: <brief from BUG_DESCRIPTION>
**Module**: <routed module>
**Status**: Merged | Rejected | Stopped by user

### Phase Results
| Phase | Status | Details |
|-------|--------|---------|
| 0. Setup | Complete | Branch: fix/<bug-id>, Team: <team-name> |
| 1a. Bug Investigation | Complete | Report: bugs/<BUG-ID>/report.md |
| 1b. Routing | Complete / Skipped (module hint) | Fixer: <fixer_agent> |
| 2. Fix | Complete | Test evidence: bugs/<BUG-ID>/test-results.md |
| 3. PR Creation | Complete | PR #<N>: <url> |
| 4. Adversarial Review | Complete | Both reviewers ran in parallel |
| 5. Merge Gate | Merged / Rejected / Stopped | <result> |

### Review Verdicts
- **Reviewer Alpha**: APPROVE/REJECT — <1-line summary>
- **Reviewer Beta**: APPROVE/REJECT — <1-line summary>

### Fix-Review Cycles
- Cycle 1: <outcome>
- Cycle 2: <outcome, if applicable>

### PR Artifacts
- [x] Bug report posted as PR comment
- [x] Alpha verdict posted as PR review
- [x] Beta verdict posted as PR review
- [x] Test evidence in bugs/<BUG-ID>/test-results.md
- [x] Review files in bugs/<BUG-ID>/reviews/

### Shutdown
- Agents responded within <N>s / Agents <names> timed out after 60s — presumed terminated
- Agent panes killed: <N> panes from bugs/<BUG-ID>/panes.txt

### Final Status
<one-line summary>
```
