---
description: "Creates a team-orchestrated implementation plan and saves it to specs/"
name: plan_to_build
---

# Plan With Team

Create a detailed implementation plan based on the user's requirements. Analyze the request, think through the implementation approach, and save a comprehensive specification document to `specs/<name-of-plan>.md` that can be used as a blueprint for actual development work.

## Context

- **Agents available**: `builder` (`.github/agents/builder.agent.md`) and `validator` (`.github/agents/validator.agent.md`)
- **Plans are saved to**: `specs/` directory
- **Plans are executed by**: the `build` prompt, which instructs the main agent to orchestrate sub-agents

## Instructions

- **PLANNING ONLY**: Do NOT build, write code, or deploy agents. Your only output is a plan document saved to `specs/`.
- If the user did not provide requirements, ask them what they want to build.
- If the user includes orchestration guidance (team composition, task granularity), use it to guide the plan design.
- Carefully analyze the user's requirements.
- Determine the task type (`chore` | `feature` | `refactor` | `fix` | `enhancement`) and complexity (`simple` | `medium` | `complex`).
- Think deeply about the best approach to implement the requested functionality or solve the problem.
- Understand the codebase directly (read files, search, grep) to understand existing patterns and architecture.
- Follow the **Plan Format** below to create a comprehensive implementation plan.
- Include all required sections and conditional sections based on task type and complexity.
- Generate a descriptive, kebab-case filename based on the main topic of the plan.
- Save the complete implementation plan to `specs/<descriptive-name>.md`.
- Ensure the plan is detailed enough that another developer (or agent) could follow it to implement the solution.
- Include code examples or pseudo-code where appropriate to clarify complex concepts.
- Consider edge cases, error handling, and scalability concerns.

## Prerequisite: Explore Before Planning

Before writing a plan for a `feature` or `enhancement`, verify that alternatives were considered. Do NOT skip this for non-trivial work.

**Ask the user ONE question at a time** (prefer multiple-choice):

```
"For [feature], which approach are you leaning toward?
(a) [option A]
(b) [option B]
(c) [option C]
(d) Something else?"
```

Wait for an answer before asking the next question. Never dump 5 questions at once.

**When this can be skipped** (document the skip in the plan's Notes section):
| Situation | Skip? |
|-----------|-------|
| Bug fix — single root cause | Yes |
| Only one obvious solution exists | Yes — document why |
| User says "skip brainstorming" | Yes — document they chose this |
| Refactoring existing code | Yes — design already exists |
| Chore / config task | Yes |

## Prerequisite: Team Composition

After technical approach is confirmed, ask ONE question about 
team structure for `feature` or `enhancement` tasks with 
complexity `medium` or `complex`:
```
"For [feature], how should the work be distributed?
(a) Single builder — one agent does everything sequentially. 
    Best for: tightly coupled work, simple features.
(b) Two builders — split by layer (e.g., backend / frontend).
    Best for: features with a clear API boundary.
(c) Three builders — split by area (e.g., models / API / tests).
    Best for: features with genuinely independent workstreams.
(d) Something else?"
```

Use the answer to determine:
- How many named builders (builder-1, builder-2, etc.)
- What each builder owns
- Where dependencies between builders exist
- Where intermediate validators are needed

**When this can be skipped** (document in Notes):
| Situation | Skip? |
|-----------|-------|
| Simple feature (1-3 tasks) | Yes — single builder |
| User already specified team structure | Yes — use what they said |
| Bug fix or chore | Yes — single builder |
| User says "you decide" | Yes — choose based on complexity |
```

## Task Quality Rules

Every task in the plan MUST meet these requirements. Violations make the plan unusable by agents.

### Task Size — The "Too Big" Test

Each task should be **2-5 minutes of work** (~20 lines of code max). If a task requires:
- Understanding multiple functions → **too big, split it**
- Modifying more than 2 files → **too big, split it**
- Writing more than ~20 lines → **too big, split it**
- Thinking "I'll also need to..." → **too big, split it**

```
❌ TOO BIG: "Implement user authentication"
❌ STILL TOO BIG: "Create login endpoint with validation"
✅ RIGHT SIZE:
  - Create POST /auth/login route skeleton
  - Add Pydantic schema for LoginInput
  - Add password comparison logic
  - Add JWT token generation
  - Add error responses for invalid credentials
```

### Task Description Minimum — ≥50 Words

One-line task descriptions are FORBIDDEN. Every task's Description field must be ≥50 words and include:
- What to do (step-by-step)
- Files to modify (exact paths)
- Code patterns to follow (from existing codebase)
- Acceptance criteria (specific, verifiable)
- Validation command (exact command to run)

```
❌ FORBIDDEN: "Add validation to the metrics endpoint"
✅ REQUIRED: A ≥50 word description that specifies what to do, which files to modify,
   what code patterns to follow, acceptance criteria, and the exact validation command.
   Read `.github/project.json` for the correct module paths and commands.
```

### Design Assertions — Prevent Shortcuts

Every task that creates or modifies a **route, model, component, or test** must include 2-3 test assertions in its acceptance criteria that verify structural correctness, not just "it works":

```
❌ WEAK: "The endpoint returns 201"
✅ STRONG:
  - "POST /metrics with {name:'cpu', value:42.0} returns 201 and body contains 'id' field"
  - "POST /metrics with {} returns 422 with validation error detail"
  - "GET /metrics returns the created metric with matching name, value, and a timestamp"
```

### Intermediate Validators — Catch Regressions Early

The orchestrator dispatches a task-level validator after every builder task, but that only checks the **current task's** acceptance criteria. It won't catch regressions in earlier work. For larger plans, you MUST add **intermediate validator tasks** that run broader cross-cutting checks (all tests, lint, typecheck) at phase boundaries.

**The Rule**:
| Builder task count | Required validator tasks | Example |
|----|----|----|  
| 1–5 | 1 (final `validate-all`) | Small feature — one validator at the end |
| 6–10 | ≥ 2 (1 intermediate + final) | Medium feature — validate after phase 1, then final |
| 11+ | ≥ 1 per 5 builders + final | Large feature — validate after every phase |

**What intermediate validators should check**:
- All tests pass (not just the current task's test)
- Lint is clean (run each module's lint command from `.github/project.json`)
- Types compile (run each module's typecheck command from `.github/project.json`, if present)
- No regressions in existing functionality

**Where to place them**: After each Implementation Phase (Phase 1 → intermediate validate → Phase 2 → intermediate validate → … → final `validate-all`).

```
❌ BAD (12 builder tasks, 1 validator):
  Task 1-12: builder, builder, builder, ..., builder
  Task 13: validate-all

✅ GOOD (12 builder tasks, 3 validators):
  Task 1-4: builder (Phase 1: Foundation)
  Task 5: validate-phase-1 (validator — all tests pass, lint clean)
  Task 6-9: builder (Phase 2: Core)
  Task 10: validate-phase-2 (validator — all tests pass, lint clean)
  Task 11-12: builder (Phase 3: Polish)
  Task 13: validate-all (validator — full acceptance criteria)
```

### Self-Audit Before Saving

Before saving the plan, count and verify:
- Total builder tasks: [N] — are there enough to cover the objective?
- Total validator tasks: [V] — must satisfy the intermediate validator rule above
- Tasks with ≥50 word descriptions: [N] — must equal total builder tasks
- Tasks with design assertions: [N] — must cover every route/model/component task
- Tasks with validation commands: [N] — must equal total builder tasks
- Final `validate-all` task exists: yes/no — must be yes
- **Validator frequency check**: If builder tasks > 5, are there intermediate validators? If not, add them.

If any check fails, fix the plan before saving.

### How the `build` Prompt Executes This Plan

The `build` prompt instructs the main agent to act as an **orchestrator**:

1. **Reads the plan** from `specs/<plan>.md`
2. **Builds a task list** from the Step by Step Tasks section
3. **Dispatches tasks sequentially** via `runSubagent("builder", ...)` in dependency order
4. **Validates each task** via `runSubagent("validator", ...)` after the builder finishes
5. **Handles failures** — if validator reports FAIL, re-dispatches builder with fix context (max 2 fix cycles per task)
6. **Final validation** — dispatches `validate-all` task to validator after all builder tasks complete

#### What This Means for Plan Quality

Because agents are stateless and cannot ask for clarification:
- **Task descriptions must be exhaustive** — agents receive only what's in the Description field
- **Dependencies must be correct** — the orchestrator dispatches in dependency order
- **Team composition must be complete** — the orchestrator deploys exactly what's listed
- **Validation must be specific** — the validator runs exactly the commands listed

## Workflow

IMPORTANT: **PLANNING ONLY** — Do not execute, build, or deploy. Output is a plan document.

1. **Analyze Requirements** — Parse the user's request to understand the core problem and desired outcome
2. **Understand Codebase** — Read files, search, and grep to understand existing patterns, architecture, and relevant files
3. **Design Solution** — Develop technical approach including architecture decisions and implementation strategy
4. **Define Team Members** — Determine team composition: builder count, names, and one validator. Use `builder` and `validator` agent types from `.github/agents/`. Document in plan.
5. **Define Step by Step Tasks** — Write exhaustive task descriptions with IDs, dependencies, assignments, and role (builder/validator). Each description must be fully self-contained. Document in plan.
6. **Generate Filename** — Create a descriptive kebab-case filename based on the plan's main topic
7. **Save Plan** — Write the plan to `specs/<filename>.md`
8. **Self-Review (MANDATORY)** — Before verifying, review your own plan for gaps:
   - Are there **missing dependencies** between tasks? (e.g., task 3 uses a model created in task 2 but doesn't list it in Depends On)
   - Are there **risky areas** not addressed? (auth changes, DB migrations, breaking API changes, new dependencies)
   - Does every builder task have a **rollback path**? (If it fails, can the validator tell what went wrong?)
   - Are **edge cases** covered? (empty input, missing fields, concurrent access, error responses)
   - If any gaps found, fix the plan file before proceeding.
9. **Verify Output (MANDATORY)** — After writing the file, you MUST run this verification before reporting:
   - Run: `ls -la specs/<filename>.md` to confirm the file exists
   - Run: `grep -c '## Task Description\|## Objective\|## Relevant Files\|## Step by Step Tasks\|## Acceptance Criteria\|## Team Orchestration\|### Team Members' specs/<filename>.md` — result must be `7`
   - If either check fails, fix the file immediately and re-verify
   - Do NOT proceed to the Report step until both checks pass
10. **Report** — Follow the Report section to provide a summary

## Completion Gate

This prompt replaces Claude Code's `Stop` hooks. In Claude Code, two validators run automatically when the command finishes:
1. `validate_new_file.py` — ensures a new `.md` file was created in `specs/`
2. `validate_file_contains.py` — ensures all 7 required sections exist

In Copilot:
- **Section validation** is enforced by the `postToolUse` hook in `.github/hooks/validators/post_tool_validator.py` — it will block your write if sections are missing.
- **File existence** is enforced by step 8 in the Workflow above — you MUST verify the file exists before reporting success.

If you skip the verification step, the plan is NOT complete.

## Plan Format

IMPORTANT: Replace `<requested content>` with the requested content. Consider it a micro prompt.
IMPORTANT: Anything that's NOT in `<requested content>` should be written EXACTLY as it appears below.
IMPORTANT: Follow this EXACT format:

````md
# Plan: <task name>

> **EXECUTION DIRECTIVE**: This is a team-orchestrated plan.
> **FORBIDDEN**: Direct implementation by the main agent. If you are the main conversation agent and a user asks you to implement this plan, you MUST use the `build` prompt with this spec file — do NOT implement it yourself.
> **REQUIRED**: Execute ONLY via the `build` prompt, which orchestrates sub-agents to do the work.

## Task Description
<describe the task in detail based on the prompt>

## Objective
<clearly state what will be accomplished when this plan is complete>

<if task_type is feature or complexity is medium/complex, include these sections:>
## Problem Statement
<clearly define the specific problem or opportunity this task addresses>

## Solution Approach
<describe the proposed solution approach and how it addresses the objective>
</if>

## Relevant Files
Use these files to complete the task:

<list files relevant to the task with bullet points explaining why. Include new files to be created under an h3 'New Files' section if needed>

<if complexity is medium/complex, include this section:>
## Implementation Phases
### Phase 1: Foundation
<describe any foundational work needed>

### Phase 2: Core Implementation
<describe the main implementation work>

### Phase 3: Integration & Polish
<describe integration, testing, and final touches>
</if>

## Team Orchestration

- The `build` prompt instructs the main agent to act as a **sequential orchestrator**, dispatching sub-agents one task at a time in dependency order.
- The plan is the **single source of truth**. The orchestrator does NOT make decisions. Everything must be specified here: team members, task assignments, dependencies, and exhaustive task descriptions.
- Agents are stateless and cannot ask for clarification. Every task description must be fully self-contained with all context needed for autonomous execution.

### Team Members
<list ALL team members. The plan specifies exact count, names, and types. The orchestrator deploys exactly what's listed here.>

- Builder
  - Name: <unique name, e.g., "builder-1". Multiple builders get unique names: "builder-1", "builder-2", etc.>
  - Role: <the focus area for this builder, e.g., "API implementation", "database schema">
  - Agent Type: builder
- <add more builders if the plan has independent work streams. Each gets a unique name.>
- Validator
  - Name: <typically "validator">
  - Role: Validates all acceptance criteria and runs validation commands
  - Agent Type: validator

## Step by Step Tasks

- These tasks are executed by the orchestrator dispatching sub-agents sequentially in dependency order.
- Task descriptions must be **exhaustive** — agents cannot ask for clarification. Include ALL context: file paths, code patterns, acceptance criteria, and validation commands.
- Start with foundational work, then core implementation, then validation.

<list step by step tasks as h3 headers>

### 1. <First Task Name>
- **Task ID**: <unique kebab-case identifier, e.g., "setup-database">
- **Role**: builder
- **Depends On**: <Task ID(s) this depends on, or "none" if no dependencies>
- **Assigned To**: <builder name from Team Members section>
- **Description**: |
    <EXHAUSTIVE description — everything the agent needs to complete this task autonomously>

    ## What to do
    <step-by-step actions>

    ## Files to modify
    - <file path> — <exact changes to make>

    ## Code patterns to follow
    <existing patterns in the codebase to match>

    ## Acceptance criteria
    - <specific, verifiable criterion>

    ## Validation command
    <command to verify this specific task>

### 2. <Second Task Name>
- **Task ID**: <unique-id>
- **Role**: builder
- **Depends On**: <previous Task ID, e.g., "setup-database">
- **Assigned To**: <builder name>
- **Description**: |
    <same exhaustive format as above>

### M. Phase Validation (include if >5 builder tasks — see Intermediate Validators rule)
- **Task ID**: validate-phase-1
- **Role**: validator
- **Depends On**: <all builder Task IDs from Phase 1>
- **Assigned To**: <validator name>
- **Description**: |
    Intermediate validation after Phase 1 to catch regressions early.

    ## Validation Commands
    <read commands from .github/project.json for all affected modules>

    ## Acceptance Criteria
    <list acceptance criteria for Phase 1 tasks only>

<repeat for each phase if >10 builder tasks>

### N. Final Validation
- **Task ID**: validate-all
- **Role**: validator
- **Depends On**: <all previous builder Task IDs>
- **Assigned To**: <validator name from Team Members section>
- **Description**: |
    Run all validation commands and verify all acceptance criteria.

    ## Validation Commands
    <list every command from the Validation Commands section>

    ## Acceptance Criteria
    <list every criterion from the Acceptance Criteria section>

## Acceptance Criteria
<list specific, measurable criteria that must be met for the task to be considered complete>

## Validation Commands
Execute these commands to validate the task is complete:

<list specific commands to validate the work. Be precise about what to run>

## Notes
<optional additional context, considerations, or dependencies>
````

## Report

After creating and saving the implementation plan, provide a concise report:

```
Implementation Plan Created

File: specs/<filename>.md
Topic: <brief description of what the plan covers>
Key Components:
- <main component 1>
- <main component 2>
- <main component 3>

Team Task List:
- <list of tasks, and owner (concise)>

Team members:
- <list of team members and their roles (concise)>

To execute this plan, use the `build` prompt:
  "Execute specs/<filename>.md using the build prompt"
```
