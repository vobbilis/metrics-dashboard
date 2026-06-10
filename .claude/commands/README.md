# Custom Commands

Three generations of the same orchestration pipeline. All variants share the core design: the orchestrator never writes code (Write/Edit disabled), every change flows through deployed team agents (`.claude/agents/team/*.md`), and Stop hooks validate output contracts.

## Lineage

| Pipeline | v1 | v2 | Long (Fable 5) |
|---|---|---|---|
| Plan | `plan_to_build` | `plan_to_build_v2` (enforced task ownership) | `plan_to_build_long` |
| Build | `build` | `build_v2` (indefinite polling, liveness detection) | `build_long` |
| Bug → PR | — | `bug_to_pr` (crash recovery, parallel review, merge gate) | `bug_to_pr_long` |

## When to use which

- **v2** — interactive sessions where you're at the keyboard. The orchestrator can ask you questions mid-run (e.g. `bug_to_pr`'s merge gate).
- **Long** — unattended/overnight jobs on a long-horizon frontier model (`model: fable`). Designed around how Fable-class models do their best long-running work:
  - **Full spec up front**: one `AskUserQuestion` batch at kickoff locks every decision (including merge policy), then zero questions until the final report.
  - **Durable disk state**: checkpoints to `runs/<run>/` (or `bugs/<BUG-ID>/`) after every event, so the run survives context compaction and crashes.
  - **Decide-and-log autonomy**: minor choices are made and logged, not asked.
  - **Progress-based fix budgets**: up to 5 cycles, halted early by a stall rule, instead of a hard 2-cycle cap.
  - **Silence default**: minimal narration; the run log is the record.

The long pipeline composes: `plan_to_build_long` produces a spec with a mandatory `## Decision Record` (open questions: NONE) and `## Run Policy`; `build_long` reads those at kickoff and runs unattended; `bug_to_pr_long`'s fixer delegates to both.
