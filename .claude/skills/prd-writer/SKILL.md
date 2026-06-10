---
name: prd-writer
description: Use when writing or generating a PRD/Product Requirements Document from a user story, feature request, or epic. MANDATORY for producing feature breakdown, success criteria, architecture/design specs, and implementation + TDD test/automation task lists. FORBIDDEN patterns include skipping success criteria prompts, producing tasks without test-first ordering, or proposing implementation without invoking relevant skills. REQUIRED patterns are structured PRD output, explicit prompts for missing inputs, and a “Ralph Wiggum loop” gap/risk check with at least one revision pass.
---

# PRD Writer

## THE MANDATE

When this skill applies, you MUST:

1. **Prompt for the user story** (or confirm it) and extract: persona, need, outcome.
2. **Prompt for success criteria** BEFORE architecture/design/tasks.
3. Produce a **complete PRD** with:
   - Feature breakdown from the user story
   - Tech stack assumptions (explicit)
   - Architecture specification (interfaces, data flow, dependencies)
   - Design specification (UX flows + API/contract spec as relevant)
   - Implementation task breakdown
   - **Test-driven development plan** and automation design + test tasks
4. Run the **“Ralph Wiggum loop”** (gap/risk check) and revise at least once.

This skill is about producing a high-quality PRD that is directly executable by engineering.

## FORBIDDEN PATTERNS

- ❌ **FORBIDDEN**: Writing architecture/design/tasks before prompting for **success criteria**.
- ❌ **FORBIDDEN**: Generating “tasks” that start with implementation and tack tests on at the end.
- ❌ **FORBIDDEN**: Vague PRDs (“build a dashboard”, “add caching”) without explicit scope, acceptance criteria, and measurable success.
- ❌ **FORBIDDEN**: Making up constraints, compliance needs, or SLAs as facts. If unknown, ask.
- ❌ **FORBIDDEN**: Proceeding to implementation without invoking the relevant repo skills (see Required Patterns).

## REQUIRED PATTERNS

### ✅ Required Interaction Pattern (Prompting)

If inputs are missing, you MUST ask concise questions.

**Ask in this order (do not skip):**
1. **User story** (or confirm): “As a … I want … so that …”
2. **Success criteria**: metrics, thresholds, guardrails, and time window
3. **Constraints**: timeline, rollout constraints, compliance/security, dependencies, “must integrate with X”
4. **Out-of-scope**: what is explicitly NOT being built

**Question style:**
- Prefer 3–6 focused questions total.
- If user is senior and wants speed, offer a “defaults” mode (clearly labeled assumptions) plus a checklist of what to confirm.

### ✅ Required Output Structure (PRD)

Produce a PRD with the following sections, in this order:

1. **Title / Summary**
2. **Problem Statement**
3. **User Story**
4. **Goals / Non-Goals**
5. **Personas & Use Cases**
6. **Feature Breakdown** (derived from the user story)
   - Capabilities
   - User flows
   - Edge cases
   - Acceptance criteria per feature
7. **Success Criteria (Measurable)**
   - Product metrics
   - System metrics (latency/throughput/error budget)
   - Guardrails (cost, reliability)
8. **Requirements**
   - Functional requirements
   - Non-functional requirements
   - Security/privacy requirements
9. **Tech Stack & Dependencies**
   - Current repo tech assumptions (explicit)
   - New libraries/services (if any) + justification
10. **Architecture Spec**
   - Components and responsibilities
   - Data model and storage
   - APIs/contracts and schemas
   - Control flow (sequence)
   - Failure modes and recovery
   - Observability (logs/metrics/tracing)
11. **Design Spec**
   - UX flows (even if backend-only: describe API UX)
   - Wireframe-level description (text)
   - Error states
   - Accessibility considerations (if UI)
12. **Implementation Plan (Tasks)**
   - Break down into milestones
   - Each milestone includes: scope, deliverables, risks
13. **Testing & Automation Plan (TDD-first)**
   - Test strategy by level (unit/integration/e2e)
   - Test data and fixtures
   - Automation (CI, smoke tests, load/perf where applicable)
   - Explicit test tasks ordered before implementation tasks
14. **Rollout Plan**
   - Feature flags, progressive delivery, migration plan
15. **Risks & Mitigations**
16. **Open Questions**

**PRD Task List format (required):**
- Include a checkbox task list that is compatible with autonomous task runners (e.g., markdown `- [ ] ...`).
- Group tasks by milestone, and ensure test tasks appear before implementation tasks.

### ✅ Required Task Ordering (TDD)

When generating task lists, you MUST order work as:

1. **Tests first (RED)**: add failing tests that define the behavior
2. **Minimal implementation (GREEN)**: smallest change to pass tests
3. **Refactor**: clean-up with tests green
4. **Verification**: run targeted then broader checks

### ✅ Required Skill Invocation Rules

If the user asks to proceed from PRD into design/implementation in this repo, you MUST invoke relevant skills:

- Always start with `using-skills` to determine workflow ordering.
- For solution exploration: `brainstorming`.
- If multiple options exist: `design-evaluation`.
- To produce an actionable plan file: `writing-plans`.
- Before coding: `executing-plans` + `test-driven-development`.
- Before declaring “done”: `verification-before-completion`.
- If touching query/storage/hot paths: `performance-gate`.
- If refactoring/moving code: `code-refactoring`.
- If debugging: `systematic-debugging`.

## THE “RALPH WIGGUM LOOP” (Ralphy-Style Completion Loop)

This project’s reference for “Ralph Wiggum loop” is an **autonomous completion loop** (like the `ralphy` repo) that keeps iterating on a PRD/task list until it is actually complete.

You MUST run this loop at least once before finalizing the PRD.

**Loop trigger:** after producing the first PRD draft.

**Loop steps (required):**
1. **Generate Draft v0**: produce a full PRD and a checkbox task list (`- [ ] ...`).
2. **PRD completeness scan**: verify every required PRD section exists and is non-empty; flag missing inputs explicitly.
3. **Task list correctness scan**:
   - Each feature has acceptance criteria and at least one corresponding test task.
   - Test tasks appear before implementation tasks (TDD-first).
   - Tasks are small, verifiable, and phrased as outcomes.
4. **Assumption + dependency audit**: list assumptions and dependencies; convert any “unknowns” into open questions.
5. **Risk + failure-mode audit**: list top risks and mitigations (keep this short but concrete).
6. **Ask targeted follow-ups**: ask only the questions required to remove blockers/ambiguity.
7. **Revise Draft v1**: incorporate answers and update tasks; repeat steps 2–6 until there are no blocking gaps.

**Output requirement:** Include a short “Ralph Wiggum loop results” subsection showing what changed between v0 and v1.

## CHECKLIST

### Before Writing the PRD
- [ ] Ask for (or confirm) the user story.
- [ ] Ask for success criteria (metrics + thresholds + timeframe).
- [ ] Ask for constraints and non-goals.
- [ ] Ask for dependencies/integrations and any compliance/security constraints.

### While Writing the PRD
- [ ] Derive a feature breakdown from the user story (do not invent unrelated features).
- [ ] Include explicit acceptance criteria per feature.
- [ ] Include architecture and design specs at the level engineers can implement.
- [ ] Include a task breakdown with milestones.
- [ ] Include a TDD-first test and automation plan; tests precede implementation tasks.

### Ralph Wiggum Loop
- [ ] Run the pre-mortem.
- [ ] List assumptions and ask for confirmations.
- [ ] Ensure each feature has a clear first failing test.
- [ ] Revise the PRD at least once.

### Hand-off Readiness
- [ ] PRD has measurable success criteria.
- [ ] PRD has a clear scope boundary (goals/non-goals).
- [ ] PRD has an implementation plan that is test-first.
- [ ] PRD has risks, mitigations, and open questions.
