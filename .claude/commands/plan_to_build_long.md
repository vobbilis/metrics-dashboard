---
description: Creates an implementation plan for UNATTENDED execution via /build_long — every decision resolved at planning time, run policy locked into the spec, zero open questions left for the run
argument-hint: "[user prompt] [orchestration prompt]"
model: fable
context: fork
allowed-tools: Read, Grep, Glob, Bash, Write, Edit, WebSearch, WebFetch, TaskCreate, TaskUpdate, TaskList, TaskGet, AskUserQuestion
hooks:
  Stop:
    - hooks:
        - type: command
          command: >-
            uv run $HOME/.claude/hooks/validators/validate_new_file.py
            --directory specs
            --extension .md
        - type: command
          command: >-
            uv run $HOME/.claude/hooks/validators/validate_file_contains.py
            --directory specs
            --extension .md
            --contains '## Task Description'
            --contains '## Objective'
            --contains '## Relevant Files'
            --contains '## Step by Step Tasks'
            --contains '## Acceptance Criteria'
            --contains '## Team Orchestration'
            --contains '### Team Members'
            --contains '## Decision Record'
            --contains '## Run Policy'
---

# Plan To Build Long (Unattended-Execution Spec)

Create a detailed implementation plan from `USER_PROMPT`, designed to be executed **unattended** by `/build_long` on a long-horizon model (Fable 5). The build phase asks the user NOTHING — so this planning phase is where every question gets asked and every decision gets made. The spec you produce is the single, complete, self-sufficient instruction set for a multi-hour autonomous run.

Planning is interactive; the build is not. Front-load accordingly.

## Variables

USER_PROMPT: $ARGUMENTS
PLAN_OUTPUT_DIRECTORY: `specs/`
TEAM_MEMBERS: `.claude/agents/team/*.md`
GENERAL_PURPOSE_AGENT: `general-purpose`

## Instructions

All instructions from `/plan_to_build_v2` apply (planning only; analyze requirements; read `docs/design/` first; understand the codebase directly; exhaustive self-contained task descriptions; enforced `Assigned To`; design-updater tasks for medium/complex plans; exact plan format). These are the long-run additions:

- **Zero open questions may survive planning.** While drafting, keep a working list of every ambiguity, judgment call, and policy choice you encounter. Resolve each one either (a) yourself, when the codebase or design docs make the answer clear, or (b) by asking the user via `AskUserQuestion` — batched, max 4 per call — before saving the plan. A plan containing TBDs, "to be decided", or implicit assumptions an agent could trip on is a failed plan.
- **Write the `## Decision Record`.** Every resolved question goes in it: the decision, who made it (you vs. user), and one line of rationale. Builders will treat these as binding constraints; `/build_long` reads them at kickoff so it doesn't re-ask.
- **Write the `## Run Policy`.** `/build_long` executes under this policy without consulting the user. It must specify:
  - Fix-cycle budget (default 5) and the stall rule (stop when 2 consecutive cycles fix nothing new).
  - Behavior on stall/partial failure: stop-and-report (default) or best-effort-complete-remaining.
  - Any pre-authorized destructive actions for this run (default: none — agents must never need one).
  - Escalation contract: what the final report must contain if the run cannot fully succeed.
- **Size tasks for long-horizon execution.** Fable-class models hold coherence over very long traces — prefer fewer, larger, well-specified tasks over many fragmented ones, but keep genuinely parallel work split across builders so it actually runs in parallel.
- **Every task description must be compaction-proof.** Assume the executing agent's context gets summarized mid-task: the description alone (plus files on disk) must be enough to resume. Include exact file paths, validation commands, and acceptance criteria inline — never "as discussed above".
- Reference `/build_long` (not `/build_v2`) in the execution directive.

### How /build_long Executes This Plan

Identical mechanics to `/build_v2` (team creation, TaskCreate per task, enforced `Assigned To`, standing orders, validator fix tasks, wakeups, liveness pings) with these differences your plan must account for:

1. **Phase 0 Decision Lock** — `/build_long` reads `## Decision Record` and `## Run Policy` first. A complete plan means it deploys immediately with zero questions; gaps mean it interrupts the user before starting.
2. **Durable run state** — it checkpoints to `runs/<plan-name>-<timestamp>/` after every event and survives context compaction and crashes by reconstructing from disk.
3. **Progress-based fix budget** — up to 5 fix cycles, halted early by the stall rule, all without user input.
4. **No mid-run user contact** — agents that hit ambiguity make the most reasonable plan-consistent choice and log it. Your task descriptions determine how often that happens; make it never.

## Workflow

1. Analyze Requirements — parse USER_PROMPT; start the open-questions list immediately.
2. Read Design Docs — glob `docs/design/`, read everything relevant, extract prior decisions as constraints.
3. Understand Codebase — directly, without subagents.
4. Design Solution — architecture and implementation strategy consistent with prior decisions.
5. **Resolve Every Open Question** — self-resolve what the code/design docs answer; batch the rest to the user via `AskUserQuestion`. Iterate until the list is empty.
6. Define Team Members — builders (count/names/types), one validator, design-updater for medium/complex plans.
7. Define Step by Step Tasks — exhaustive, compaction-proof descriptions; enforced `Assigned To`; correct dependencies.
8. Write Decision Record & Run Policy sections.
9. Generate kebab-case filename; save to `PLAN_OUTPUT_DIRECTORY/<filename>.md`; report.

## Plan Format

Use the EXACT format from `/plan_to_build_v2` (same template, same section order, same task-entry structure), with these changes:

1. The execution directive block at the top references the long variant:

```md
> **EXECUTION DIRECTIVE**: This is a team-orchestrated plan for UNATTENDED execution.
> **FORBIDDEN**: Direct implementation (Edit, Write, NotebookEdit) by the main agent. If you are the main conversation agent and a user asks you to implement this plan, you MUST invoke `/build_long specs/<this-filename>.md` -- do NOT implement it yourself.
> **REQUIRED**: Execute ONLY via the `/build_long` command, which deploys team agents to do the work without further user input.
```

2. Insert these two sections between `## Team Orchestration`'s intro and `### Team Members`:

```md
## Decision Record

Binding decisions for this run. Builders MUST follow these; /build_long will not re-ask.

| # | Question / ambiguity | Decision | Decided by | Rationale |
|---|---------------------|----------|------------|-----------|
| 1 | <question> | <decision> | planner \| user | <one line> |

Open questions remaining: NONE <this line is mandatory and must be true>

## Run Policy

- **Fix-cycle budget**: <N, default 5>
- **Stall rule**: stop fix cycles when 2 consecutive cycles produce no newly passing validation commands
- **On stall / partial failure**: <stop-and-report | best-effort-complete-remaining>
- **Pre-authorized destructive actions**: <none | explicit list>
- **Escalation contract**: <what the final report must contain if the run cannot fully succeed>
```

## Report

After saving the plan, report using the `/plan_to_build_v2` report format with the closing line changed to:

```
Decisions resolved: <N> (planner: <n1>, user: <n2>) — open questions remaining: NONE

This plan is ready for unattended execution. Kick it off and walk away:
/build_long <path to plan>
```
