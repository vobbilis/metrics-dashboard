---
name: executing-plans
description: Use when you have a written implementation plan to execute. MANDATORY for plan execution. FORBIDDEN is executing without checkpoints. REQUIRED is batch execution with verification and review between batches. PREREQUISITE is a written plan file.
---

# Executing Plans

## THE MANDATE

**Execute plans methodically with checkpoints.**

Don't rush through a plan. Execute in batches, verify each task, and checkpoint with the user between batches.

---

## PREREQUISITE CHECK - MANDATORY

**Before executing anything, verify the workflow was followed:**

```
┌─────────────────────────────────────────────────────────────┐
│  PREREQUISITE 1: PLAN EXISTS                                │
│  ────────────────────────────────────────────────────────── │
│  □ Is there a written plan file?                            │
│  □ Location: docs/plans/YYYY-MM-DD-<topic>.md               │
│                                                             │
│  If NO → STOP. Use writing-plans skill first.               │
│                         ↓                                   │
│  PREREQUISITE 2: PLAN IS COMPLETE                           │
│  ────────────────────────────────────────────────────────── │
│  □ Does each task have verification steps?                  │
│  □ Are tasks bite-sized (2-5 minutes each)?                 │
│  □ Are file paths specified?                                │
│                                                             │
│  If NO → STOP. Complete the plan first.                     │
│                         ↓                                   │
│  PREREQUISITE 3: WORKFLOW WAS FOLLOWED                      │
│  ────────────────────────────────────────────────────────── │
│  □ Was brainstorming done? (options explored)               │
│  □ Was design-evaluation done? (if multiple options)        │
│  □ Is there evidence for the chosen approach?               │
│                                                             │
│  If NO → Raise concern before proceeding.                   │
└─────────────────────────────────────────────────────────────┘
```

### How to Check Prerequisites

**Step 1: Look for the plan file**
```bash
ls docs/plans/*.md
```

**Step 2: Review the plan header**
Good plans have:
- Created date
- Status field
- Overview section
- Prerequisites section

**Step 3: Verify workflow context**
Ask: "Were alternatives considered before choosing this approach?"
- If yes with evidence → Proceed
- If no → Raise concern: "I notice we jumped to planning without exploring options. Should we step back?"

### When to Raise Concerns

```markdown
## Workflow Concern

Before executing this plan, I noticed:
- ⚠️ No brainstorming phase documented
- ⚠️ No comparison of alternatives
- ⚠️ Decision rationale not recorded

Options:
1. Proceed anyway (user accepts risk)
2. Quick brainstorm session (15 min)
3. Document rationale retroactively

Which would you prefer?
```

---

### The Golden Rule: Update the Plan File

As you complete each task, **mark it complete in the plan file itself**:

```markdown
## Tasks

- [x] Task 1: Create User model ✓
- [x] Task 2: Add password hashing ✓  
- [ ] Task 3: Create login endpoint ← YOU ARE HERE
- [ ] Task 4: Add JWT generation
```

**Why?** The plan file becomes:
1. A progress tracker
2. A resumption point if interrupted
3. A record of what was done
4. Proof of execution for code review

---

## THE PROCESS

```
┌─────────────────────────────────────────────────────────────┐
│  1. LOAD PLAN                                               │
│     Read and understand the full plan                       │
│         ↓                                                   │
│  2. REVIEW                                                  │
│     Raise any concerns before starting                      │
│         ↓                                                   │
│  3. EXECUTE BATCH (3 tasks default)                         │
│     Complete each task with verification                    │
│         ↓                                                   │
│  4. CHECKPOINT                                              │
│     Report progress, get feedback                           │
│         ↓                                                   │
│  5. REPEAT                                                  │
│     Continue until plan complete                            │
└─────────────────────────────────────────────────────────────┘
```

---

## STEP 1: LOAD AND REVIEW

Before executing:

1. **Read the entire plan**
2. **Understand the goal**
3. **Review each task**
4. **Identify concerns**

```markdown
## Plan Review

**Plan:** docs/plans/2024-01-15-password-reset.md
**Tasks:** 6 total
**Estimated time:** 45 minutes

**Concerns:**
- None, plan looks complete

**OR**

**Concerns:**
- Task 3 missing test verification
- Task 5 depends on Task 4 but doesn't say so

**Design Assertion Pre-flight:**
- Struct/trait/handler/wiring tasks: [count]
- Tasks with design assertions: [count] — must match above
- Tasks with only `is_ok()` assertions: [list or "none"]
- If any struct/trait/handler task is missing design assertions → STOP.
  Add them before executing, or flag as concern.

Shall I proceed or should we address these first?
```

**If concerns exist, raise them before starting.**

---

## STEP 2: EXECUTE IN BATCHES

Default batch size: **3 tasks**

For each task:

```markdown
### Task 1: [Name] - IN PROGRESS

**Status:** Starting...

[Write test with design assertions first — see plan task for assertions]
[Run test — MUST see RED (fail)]
[Write implementation]
[Run test — MUST see GREEN (pass)]

**Verification:**
$ [command from plan]
[actual output]

**Design Assertion Check:** Do the passing tests assert structural properties (types, fields, non-placeholder data), not just `is_ok()`? [Yes/No]

**Status:** ✓ Complete
```

---

## STEP 3: CHECKPOINT

After each batch:

```markdown
## Checkpoint: Batch 1 Complete

**Completed:**
- ✓ Task 1: Add resetToken field to User model
- ✓ Task 2: Create password reset request endpoint
- ✓ Task 3: Create password reset endpoint

**Verification Summary:**
- All tests passing
- Endpoints responding correctly

**Design Assertion Scan (30-second check):**
- Task 1: Design assertions verify field types via downcast ✓
- Task 2: Design assertions verify response contains non-placeholder data ✓
- Task 3: Design assertions verify handler calls real service (not stub) ✓
- Tasks with only `is_ok()` / compilation checks: NONE ✓

**Next batch:**
- Task 4: Add rate limiting
- Task 5: Add email template
- Task 6: Add integration tests

**Ready for feedback.** Any changes before I continue?
```

**Wait for user feedback before continuing.**

---

## FORBIDDEN PATTERNS

### ❌ Executing Without Reading - BANNED

```markdown
❌ FORBIDDEN:
"Let me start on Task 1..."
(Without reviewing the whole plan)

✅ REQUIRED:
"I've reviewed the plan. 6 tasks total, focusing on password reset.
No concerns. Starting with Task 1..."
```

### ❌ No Checkpoints - BANNED

```markdown
❌ FORBIDDEN:
*Executes all 10 tasks without stopping*
"Done with all tasks!"

✅ REQUIRED:
*Executes 3 tasks*
"Batch 1 complete. Ready for feedback before continuing."
```

### ❌ Skipping Verification - BANNED

```markdown
❌ FORBIDDEN:
"Task 1 complete. Moving to Task 2..."
(No verification shown)

✅ REQUIRED:
"Task 1 complete. Verification:
$ npm test -- user.model
✓ User model has resetToken field
Moving to Task 2..."
```

### ❌ Deviating From Plan - BANNED

```markdown
❌ FORBIDDEN:
"The plan says X but I think Y is better, so I did Y."

✅ REQUIRED:
"The plan says X but I noticed a potential issue. 
Should we update the plan before proceeding?"
```

---

## HANDLING ISSUES

When something doesn't work as planned:

### 1. Stop and Report

```markdown
## Issue Found

**Task:** Task 3 - Create password reset endpoint
**Problem:** Email service not configured
**Plan said:** EmailService.sendResetEmail()
**Actual:** EmailService is undefined

**Options:**
1. Mock the email service for now
2. Configure email service first (not in plan)
3. Skip email, return token directly

Which approach should we take?
```

### 2. Wait for Guidance

Don't make significant deviations without approval.

### 3. Update Plan if Needed

If the plan needs changes:
1. Document the change
2. Update the plan file
3. Continue execution

---

## BATCH SIZE GUIDELINES

| Plan Size | Batch Size | Checkpoint Frequency |
|-----------|------------|---------------------|
| 1-3 tasks | All at once | Once at end |
| 4-6 tasks | 3 tasks | Every 3 |
| 7-12 tasks | 3-4 tasks | Every batch |
| 12+ tasks | 3 tasks | Every batch |

**Adjust based on:**
- Task complexity (complex = smaller batches)
- Risk level (risky = more checkpoints)
- User preference

---

## EXECUTION TEMPLATE

```markdown
# Executing Plan: [Name]

**Plan file:** docs/plans/YYYY-MM-DD-topic.md
**Total tasks:** N
**Batch size:** 3

---

## Plan Review

[Summary of plan]
[Any concerns]

---

## Batch 1

### Task 1: [Name]

**Status:** In Progress

[Work performed]

**Verification:**
$ command
output

**Status:** ✓ Complete

### Task 2: [Name]
...

### Task 3: [Name]
...

---

## Checkpoint 1

**Completed:** Tasks 1-3
**Verification:** All passing
**Issues:** None

Ready for feedback before Batch 2.

---

## Batch 2
...
```

---

## COMPLETION

When all tasks are done:

```markdown
## Plan Execution Complete

**Plan:** docs/plans/2024-01-15-password-reset.md
**Status:** ✓ All tasks complete

**Summary:**
- Tasks completed: 6/6
- Tests added: 4
- Files modified: 5

**Final Verification:**
$ npm test
All 24 tests passing

$ npm run build
Build successful

**Ready for code review.**
```

---

## ENFORCEMENT

This skill is MANDATORY for plan execution:

- **FORBIDDEN**: Execute without reading plan first
- **FORBIDDEN**: Skip checkpoints
- **FORBIDDEN**: Hide verification results
- **FORBIDDEN**: Deviate from plan without approval
- **FORBIDDEN**: Mark struct/trait/handler task complete when tests only check `is_ok()` or compilation
- **FORBIDDEN**: Skip writing test with design assertions before implementation (TDD violation)
- **REQUIRED**: Review plan before starting (including design assertion pre-flight)
- **REQUIRED**: Execute in batches
- **REQUIRED**: Write test with design assertions FIRST, see RED, then implement, see GREEN
- **REQUIRED**: Verify each task (design assertion check: structural, not just compilation)
- **REQUIRED**: Checkpoint between batches (including 30-second design assertion scan)
- **REQUIRED**: Wait for feedback

**Plans exist for a reason. Follow them. Design assertions exist because shortcuts are invisible at compile time.**

---

## Related Skills

- **writing-plans** - Create plans to execute
- **verification-before-completion** - Verify each task
- **requesting-code-review** - After plan execution
