---
description: Creates a concise engineering implementation plan with team orchestration and saves it to specs directory (v2 — enforced task ownership)
argument-hint: "[user prompt] [orchestration prompt]"
model: opus
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
---

# Plan To Build v2

Create a detailed implementation plan based on the user's requirements provided through the `USER_PROMPT` variable. Analyze the request, think through the implementation approach, and save a comprehensive specification document to `PLAN_OUTPUT_DIRECTORY/<name-of-plan>.md` that can be used as a blueprint for actual development work. Follow the `Instructions` and work through the `Workflow` to create the plan.

## Variables

USER_PROMPT: $ARGUMENTS
PLAN_OUTPUT_DIRECTORY: `specs/`
TEAM_MEMBERS: `.claude/agents/team/*.md`
GENERAL_PURPOSE_AGENT: `general-purpose`

## Instructions

- **PLANNING ONLY**: Do NOT build, write code, or deploy agents. Your only output is a plan document saved to `PLAN_OUTPUT_DIRECTORY`.
- If no `USER_PROMPT` is provided, stop and ask the user to provide it.
- If the user prompt includes orchestration guidance (team composition, task granularity, parallel/sequential preferences), use it to guide the plan design.
- Carefully analyze the user's requirements provided in the USER_PROMPT variable
- Determine the task type (chore|feature|refactor|fix|enhancement) and complexity (simple|medium|complex)
- Think deeply (ultrathink) about the best approach to implement the requested functionality or solve the problem
- **Read `docs/design/` before planning** — scan for any existing design docs relevant to the domains this plan will touch. Read them fully. Inject prior decisions and established patterns into task descriptions so builders do not repeat past mistakes or contradict prior architectural choices.
- Understand the codebase directly without subagents to understand existing patterns and architecture
- Follow the Plan Format below to create a comprehensive implementation plan
- Include all required sections and conditional sections based on task type and complexity
- Generate a descriptive, kebab-case filename based on the main topic of the plan
- Save the complete implementation plan to `PLAN_OUTPUT_DIRECTORY/<descriptive-name>.md`
- Ensure the plan is detailed enough that another developer could follow it to implement the solution
- Include code examples or pseudo-code where appropriate to clarify complex concepts
- Consider edge cases, error handling, and scalability concerns
- Understand how `/build_v2` executes plans. Refer to the `Team Orchestration` section in the Plan Format for details. Your plan must be complete enough for agents to work autonomously.
- **Include design-updater tasks** — for any plan of medium or complex complexity, or any plan that makes non-trivial architectural decisions, include one or more `design-updater` tasks at the end of the task graph (after validate-all). Each task targets a specific `docs/design/<domain>.md`. The planner decides how many design-updater tasks are needed and where in the dependency graph they belong.

### How /build_v2 Executes This Plan

The `/build_v2` command creates a **self-organizing agent team**:

1. **Creates a team** via `TeamCreate` — name is `<plan-name>-<timestamp>` to prevent collisions
2. **Populates the task list** — one `TaskCreate` per task in this plan, with dependencies via `addBlockedBy`
3. **Deploys agents once** with standing orders — builders and validators listed in Team Members
4. **Agents self-organize** — they poll `TaskList`, claim tasks **assigned to their own name**, execute work, mark completed, and loop
5. **Validator auto-creates fix tasks** if validation fails — builders pick them up automatically (max 2 fix cycles); leader sends a wakeup so builders re-check immediately
6. **Leader monitors** via `SendMessage` reports — pings agents silent for 10+ minutes, only intervenes for escalations

#### What This Means for Plan Quality

Because agents work autonomously:
- **Task descriptions must be exhaustive** — agents cannot ask the leader for clarification
- **`Assigned To` is enforced** — every task must have an `Assigned To` matching a builder name from Team Members; agents only claim tasks assigned to them
- **Dependencies must be correct** — agents trust `blockedBy` to prevent premature starts
- **Team composition must be complete** — `/build_v2` deploys exactly what's listed, no more
- **Validation must be specific** — the validator runs exactly the commands listed

## Workflow

IMPORTANT: **PLANNING ONLY** - Do not execute, build, or deploy. Output is a plan document.

1. Analyze Requirements - Parse the USER_PROMPT to understand the core problem and desired outcome
2. Read Design Docs - Glob `docs/design/` for existing design documents. Read any that are relevant to the domains this plan touches. Extract prior decisions and established patterns — these become constraints injected into task descriptions.
3. Understand Codebase - Without subagents, directly understand existing patterns, architecture, and relevant files
4. Design Solution - Develop technical approach including architecture decisions and implementation strategy. Ensure the approach is consistent with prior decisions captured in design docs.
5. Define Team Members - Determine team composition: builder count, names, agent types, one validator, and one design-updater (for medium/complex plans). Identify from `.claude/agents/team/*.md` or use `general-purpose`. Document in plan.
6. Define Step by Step Tasks - Write exhaustive task descriptions with IDs, dependencies, assignments, and role (builder/validator/design-updater). Each description must be fully self-contained. Every task MUST have an `Assigned To` that matches a name in Team Members. For builder tasks, inject relevant prior decisions from design docs. Document in plan.
7. Generate Filename - Create a descriptive kebab-case filename based on the plan's main topic
8. Save Plan - Write the plan to `PLAN_OUTPUT_DIRECTORY/<filename>.md`
9. Save & Report - Follow the `Report` section to write the plan to `PLAN_OUTPUT_DIRECTORY/<filename>.md` and provide a summary of key components

## Plan Format

- IMPORTANT: Replace <requested content> with the requested content. It's been templated for you to replace. Consider it a micro prompt to replace the requested content.
- IMPORTANT: Anything that's NOT in <requested content> should be written EXACTLY as it appears in the format below.
- IMPORTANT: Follow this EXACT format when creating implementation plans:

```md
# Plan: <task name>

> **EXECUTION DIRECTIVE**: This is a team-orchestrated plan.
> **FORBIDDEN**: Direct implementation (Edit, Write, NotebookEdit) by the main agent. If you are the main conversation agent and a user asks you to implement this plan, you MUST invoke `/build_v2 specs/<this-filename>.md` -- do NOT implement it yourself.
> **REQUIRED**: Execute ONLY via the `/build_v2` command, which deploys team agents to do the work.

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

- The `/build_v2` command deploys a **self-organizing agent team**. Agents autonomously discover, claim, and execute tasks from a shared task list.
- You are responsible for designing the team composition and task graph so agents can work autonomously.
- IMPORTANT: The plan is the **single source of truth**. `/build_v2` is a pure executor — it does NOT make decisions. Everything must be specified here: team members, task assignments, dependencies, and exhaustive task descriptions.
- **`Assigned To` is enforced**: `/build_v2` injects each agent's name into their standing orders. Agents only claim tasks where `Assigned To` matches their own name. Every task MUST have an `Assigned To`.
- Agents cannot ask for clarification mid-task. Every task description must be fully self-contained with all context needed for autonomous execution.

### Team Members
<list ALL team members. The plan specifies exact count, names, and types. /build_v2 deploys exactly what's listed here.>

- Builder
  - Name: <unique name, e.g., "builder-1". Multiple builders get unique names: "builder-1", "builder-2", etc.>
  - Role: <the focus area for this builder, e.g., "API implementation", "database schema">
  - Agent Type: <agent type from TEAM_MEMBERS files or GENERAL_PURPOSE_AGENT. Must be "builder" unless a specialized agent is needed.>
- <add more builders if parallel work is possible. Each gets a unique name.>
- Validator
  - Name: <typically "validator">
  - Role: Validates all acceptance criteria and runs validation commands
  - Agent Type: validator
- <for medium/complex plans or plans making architectural decisions, include a design-updater:>
- Design Updater
  - Name: design-updater
  - Role: Updates docs/design/<domain>.md with code-aligned design decisions after build completes
  - Agent Type: design-updater

## Step by Step Tasks

- These tasks are executed by self-organizing agents. Agents discover and claim tasks autonomously from the shared task list.
- Each task maps directly to a `TaskCreate` call made by `/build_v2`.
- Task descriptions must be **exhaustive** — agents cannot ask for clarification. Include ALL context: file paths, code patterns, acceptance criteria, and validation commands.
- Every task MUST have an `Assigned To` matching a name in Team Members. This is enforced — tasks without a valid `Assigned To` will not be claimed.
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

### 3. <Continue Pattern>

### N. <Final Validation Task>
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

### N+1. <Design Doc Update — include for medium/complex plans>
- **Task ID**: update-design-<domain>
- **Role**: design-updater
- **Depends On**: validate-all
- **Assigned To**: design-updater
- **Description**: |
    Update the living design document for the <domain> domain to reflect
    what was actually built in this plan.

    ## Target Design Doc
    docs/design/<domain>.md

    ## Spec File
    specs/<this-plan-filename>.md

    ## Scope
    <describe which domain areas changed — e.g., "API routing layer, pagination
    pattern, new endpoint structure">

    ## Prior Decisions to Check
    <list any prior decisions from the existing design doc that may be affected
    by this build — e.g., "cursor-based pagination decision from 2026-01-28">

    ## What to Record
    Read git diff HEAD~1 HEAD, then the changed source files, then the existing
    design doc. Update Current Design to match the implementation. Append a
    Design Decision entry for each non-trivial architectural choice made in
    this build. Every claim must cite a file:line from the actual code.

<continue with additional tasks as needed>

## Acceptance Criteria
<list specific, measurable criteria that must be met for the task to be considered complete>

## Validation Commands
Execute these commands to validate the task is complete:

<list specific commands to validate the work. Be precise about what to run>
- Example: `uv run python -m py_compile apps/*.py` - Test to ensure the code compiles

## Notes
<optional additional context, considerations, or dependencies. If new libraries are needed, specify using `uv add`>
```

## Report

After creating and saving the implementation plan, provide a concise report with the following format:

```
Implementation Plan Created

File: PLAN_OUTPUT_DIRECTORY/<filename>.md
Topic: <brief description of what the plan covers>
Key Components:
- <main component 1>
- <main component 2>
- <main component 3>

Team Task List:
- <list of tasks, and owner (concise)>

Team members:
- <list of team members and their roles (concise)>

When you're ready, you can execute the plan in a new agent by running:
/build_v2 <replace with path to plan>
```
