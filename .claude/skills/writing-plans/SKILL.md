---
name: writing-plans
description: Use when creating implementation plans for features, refactoring, or multi-step work. MANDATORY before complex implementations. FORBIDDEN is diving into code without a plan, single-line tasks, missing verification, vague observability sections, tasks without design assertions. REQUIRED is bite-sized tasks (≥50 words), design assertions per task (structural test assertions derived from design doc), section minimums (Core≥5, Observability≥5, Errors≥3), mandatory task template, terminal checklist, and self-audit with task counts. PREREQUISITE is brainstorming (and design-evaluation if multiple options).
---

# Writing Plans

## THE MANDATE

**Plan before you build.**

For any non-trivial work:
1. Write a detailed plan with bite-sized tasks
2. Include verification for each task
3. Save to `docs/plans/YYYY-MM-DD-<topic>.md`
4. Execute methodically

---

## PREREQUISITE CHECK - MANDATORY

**Before writing any plan, verify these steps were completed:**

```
┌─────────────────────────────────────────────────────────────┐
│  PREREQUISITE 1: BRAINSTORMING                              │
│  ────────────────────────────────────────────────────────── │
│  □ Were multiple approaches explored?                       │
│  □ Were requirements clarified through Q&A?                 │
│  □ Is there a clear direction chosen?                       │
│                                                             │
│  If NO → STOP. Use brainstorming skill first.               │
│                         ↓                                   │
│  PREREQUISITE 2: DESIGN EVALUATION (if applicable)          │
│  ────────────────────────────────────────────────────────── │
│  □ Were there multiple viable options?                      │
│  □ If yes: Were POCs built and compared?                    │
│  □ Is there a decision record with evidence?                │
│                                                             │
│  If multiple options existed but no POCs → STOP.            │
│  Use design-evaluation skill first.                         │
└─────────────────────────────────────────────────────────────┘
```

### Prerequisite Verification Script

Before writing a plan, ask yourself (and the user if needed):

1. **"What options did we consider?"**
   - If answer is "none" or "just this one" → Go back to brainstorming
   
2. **"Why did we choose this approach?"**
   - If answer is "it's obvious" or "I've used it before" → Go back to design-evaluation
   - If answer includes measurements/evidence → Proceed

3. **"Is there a decision record?"**
   - For significant choices, there should be documented rationale

### When Prerequisites Can Be Skipped

| Situation | Skip Allowed? |
|-----------|---------------|
| Bug fix (not a new feature) | ✅ Yes |
| Single obvious solution | ✅ Yes (document why) |
| User explicitly says "skip" | ✅ Yes (document they chose this) |
| Refactoring existing code | ✅ Yes (design already exists) |
| Time-critical hotfix | ✅ Yes (but create plan anyway) |

---

## WHEN TO USE

Use this skill when:

- Implementing a new feature
- Refactoring significant code
- Making architectural changes
- Any work spanning multiple files
- Work that will take more than 30 minutes

**Announce:** "I'm using the writing-plans skill to create an implementation plan."

---

## FORBIDDEN PATTERNS

```markdown
❌ FORBIDDEN (vague, no file, no verification):
- [ ] Add validation
- [ ] Fix the bug
- [ ] Update the service

✅ REQUIRED (specific, file path, verification):
- [ ] Add Zod schema for CreateUserInput in src/schemas/user.ts
  - Required: email (string, email format), name (string, min 1)
  - Verify: `npm run typecheck` passes
```

---

## PLAN STRUCTURE

### Plan Header

Every plan starts with this header:

```markdown
# [Feature Name] Implementation Plan

For AI: Execute this plan using the executing-plans skill.
Mark tasks complete as you go. Stop and verify after each task.

**Created:** YYYY-MM-DD
**Status:** Draft | In Progress | Complete
**Location:** docs/plans/YYYY-MM-DD-<feature>.md
```

The "For AI" line is critical - it ensures the AI executes methodically instead of speed-running.

### Required Plan Sections

Every plan must include: **Header** (above), **Overview** (2-3 sentences), **Prerequisites**, **Tasks** (using mandatory task template below), **Testing**, **Rollback Plan**, **Self-Audit**.

---

## TASK REQUIREMENTS

Each task MUST have:

| Element | Required | Example |
|---------|----------|---------|
| Clear title | ✅ | "Add email validation to UserService" |
| File path(s) | ✅ | `src/services/user.service.ts` |
| Specific changes | ✅ | "Add validateEmail() method" |
| Code (if applicable) | ✅ | Actual code to write |
| Verification command | ✅ | `npm test -- user.service` |
| Expected output | ✅ | "3 passing" |

---

## TASK SIZE

Tasks should be **atomic** - 2-5 minutes each:

```markdown
❌ TOO BIG (15-30 minutes):
"Implement user authentication"

❌ STILL TOO BIG (10-15 minutes):
"Create login endpoint with validation"

✅ RIGHT SIZE (2-5 minutes each):
- [ ] Create POST /auth/login route skeleton
- [ ] Add Zod schema for LoginInput  
- [ ] Add password comparison logic
- [ ] Add JWT token generation
- [ ] Add error responses for invalid credentials
```

### The "Too Big" Test

If a task requires:
- Understanding multiple functions → too big
- Modifying more than 1-2 files → too big  
- Writing more than ~20 lines → too big
- Thinking "I'll also need to..." → too big

**Split it.**

---

## DESIGN ASSERTIONS — THE ANTI-SHORTCUT GATE

**Why this exists:** Implementations drift from designs when verification stops at "it compiles." Placeholder types (EmptyTable), missing fields (bare DashMap instead of struct with 4 fields), and skipped tests all pass compilation. Design assertions are concrete test assertions extracted from the design doc and embedded directly in each plan task. They make shortcuts physically impossible — if the test asserts a downcast to `RemoteSchemaProvider`, an `EmptyTable` placeholder fails immediately.

### The Rule

**Every plan task that creates or modifies a struct, trait impl, or API handler MUST include a "Design Assertions" section** with 2-4 test assertions derived from the design doc. These assertions verify structural properties, not just compilation:

```markdown
❌ FORBIDDEN — assertion that only checks compilation:
assert!(result.is_ok())

✅ REQUIRED — assertion that checks structural design conformance:
assert!(provider.as_any().downcast_ref::<RemoteSchemaProvider>().is_some(),
    "Must be RemoteSchemaProvider, not a placeholder")
assert_eq!(catalog.capabilities.predicate_pushdown, true,
    "Capabilities must be stored per design doc §4.2")
assert!(response.signature.iter().any(|v| *v != 0.0),
    "Signature must contain non-zero values from real computation")
```

### What Design Assertions Check

| What | Assertion Pattern | Catches |
|------|-------------------|---------|
| Correct types | `downcast_ref::<ExpectedType>()` | Placeholder/stub types |
| Struct fields populated | `assert!(obj.field.is_some())` or field value checks | Missing wiring, None fields |
| Non-placeholder data | `!= 0`, `!is_empty()`, values match injected test data | Hardcoded zeros, empty vecs |
| Design-specified behavior | Specific values from design doc (e.g., "4 fields", "3 quantiles") | Partial implementations |

### How to Write Design Assertions

1. Find the relevant design doc section for the task
2. Extract 2-4 structural properties that distinguish correct implementation from a shortcut
3. Write them as concrete test assertion code in the plan task, citing the design doc section

### Tasks That REQUIRE Design Assertions

| Task Type | Required? | Example |
|-----------|-----------|---------|
| New struct/type | **YES** | Assert fields exist, correct types |
| Trait implementation | **YES** | Assert correct concrete type, method behavior |
| API handler/endpoint | **YES** | Assert response contains design-specified fields with real values |
| Wiring/integration | **YES** | Assert components connected (not None/placeholder) |
| Config/constants | NO | Simple values, compilation is sufficient |
| Import/re-export | NO | Structural, compilation catches errors |
| Documentation | NO | Not code |

---

## PRINCIPLES

- **DRY** - Don't repeat yourself
- **YAGNI** - Don't build what you don't need
- **TDD** - Write tests first
- **Small commits** - Commit after each task

---

## AFTER WRITING THE PLAN

Once the plan is complete:

1. **Save it:** `docs/plans/YYYY-MM-DD-<feature>.md`
2. **Review it:** Are tasks clear? Verifiable?
3. **Execute it:** Use the executing-plans skill

---

## ENFORCEMENT

This skill is MANDATORY for complex work:

- **FORBIDDEN**: Starting code without a plan
- **FORBIDDEN**: Vague task descriptions
- **FORBIDDEN**: Missing verification steps
- **FORBIDDEN**: Single-line tasks (< 50 words)
- **FORBIDDEN**: Vague observability (e.g., "Add metrics")
- **FORBIDDEN**: Struct/trait/handler/wiring tasks without design assertions
- **FORBIDDEN**: Design assertions that only check `is_ok()` or compilation (these catch nothing)
- **REQUIRED**: Bite-sized tasks (50-300 words each)
- **REQUIRED**: File paths for every change
- **REQUIRED**: Code examples where applicable
- **REQUIRED**: Verification command + expected output for every task
- **REQUIRED**: Design assertions (2-4 per struct/trait/handler/wiring task) citing design doc section
- **REQUIRED**: Design assertions that verify structural properties (downcasts, field values, non-placeholder data)
- **REQUIRED**: Self-audit section in output (including design assertion coverage count)

**A good plan makes execution mechanical.**

---

## MANDATORY SECTION MINIMUMS

Every plan MUST meet these quantified minimums:

| Section Category | Min Tasks | Required Elements Per Task |
|------------------|-----------|----------------------------|
| Core Feature | 5 | Test name, verification, expected output |
| Observability | **5** | Metric name, Prometheus query, threshold |
| Error Handling | 3 | Error type, recovery action, test case |
| Performance | 3 | Benchmark, baseline, regression gate |

**If a section has fewer tasks than the minimum, the plan is INCOMPLETE.**

### Section Detection

| If feature involves... | Required sections |
|------------------------|-------------------|
| Writing data | Core (5), Observability (5), Performance (3) |
| Reading data | Core (5), Observability (5), Performance (3) |
| Network/API | Core (5), Error Handling (3), Observability (5) |
| Background jobs | Core (5), Observability (5), Error Handling (3) |

---

## FORBIDDEN TASK PATTERNS

These patterns are AUTOMATIC VIOLATIONS:

| Pattern | Why Forbidden |
|---------|---------------|
| `Add observability` | Too vague - name specific metrics |
| `Implement metrics` | Which metrics? What values? |
| `Handle errors appropriately` | No test criteria |
| `Add proper logging` | What is "proper"? |
| `Add tests` | Which tests? What do they verify? |
| `Implement [struct]` with no design assertions | Placeholders/stubs will pass — assert on types, fields, real data |
| `assert!(result.is_ok())` as only design assertion | Compilation-level check — doesn't catch structural drift |

**Any task < 50 words is probably too vague.**
**Any struct/trait/handler task without design assertions is a shortcut waiting to happen.**

---

## MANDATORY TASK TEMPLATE

Every task MUST follow this exact structure:

```markdown
### Task X.Y: [Descriptive Name - 3-7 words]

**Description:** [REQUIRED - minimum 2 sentences explaining what and why]

**Design Assertions (from [design doc §section]):** [REQUIRED for struct/trait/handler/wiring tasks]
```[language]
// 2-4 concrete test assertions that verify structural conformance with the design doc.
// These assertions must distinguish the correct implementation from a shortcut/placeholder.
// Cite the design doc section they derive from.
assert!(provider.as_any().downcast_ref::<ExpectedType>().is_some(),
    "Must be ExpectedType per §X.Y, not a placeholder");
assert!(obj.field.is_some(), "Field must be wired per §X.Y");
```

**Test First:** [REQUIRED - exact test file and test name]
- File: `tests/[category]/test_[feature].rs`
- Test: `test_[specific_behavior]`
- Must include the Design Assertions above as test body

**Implementation:**
- File(s): [REQUIRED - exact paths]
- Changes: [REQUIRED - bullet list]

**Code:** [REQUIRED for non-trivial changes]
```[language]
// Actual code, not description
```

**Verification:** [REQUIRED - exact terminal command]
```bash
[command that proves task complete]
```

**Expected Output:** [REQUIRED - literal output]
```
[copy-pasteable success output]
```

**Performance Gate:** [IF touching hot paths]
- Baseline: [metric and value]
- Threshold: [max regression, e.g., "≤5%"]
```

### Template Violations - FORBIDDEN

```markdown
❌ Missing test:
### Task 1.1: Add metrics
**Description:** Add Prometheus metrics.
**Verification:** cargo build
(no Test First section!)

❌ Vague description:
### Task 2.1: Handle errors
**Description:** Add error handling.
(only 3 words!)

❌ No expected output:
### Task 3.1: Create endpoint
**Verification:** curl localhost:8080/health
(what should curl return?)

❌ Single-line task:
### Task 4.1: Add observability
(no structure at all!)

❌ Missing design assertions on struct/trait/handler task:
### Task 5.1: Implement RemoteCatalogProvider
**Description:** Create catalog provider backed by remote data source.
**Test First:** test_remote_catalog_basic
(no Design Assertions section! A bare DashMap wrapper would pass this.)

❌ Design assertions that only check compilation:
**Design Assertions:**
  assert!(result.is_ok())
  assert!(catalog.schema_names().len() > 0)
(These pass with placeholder types — they don't verify structural conformance.)
```

---

## MANDATORY TERMINAL CHECKLIST

**COPY THIS INTO EVERY PLAN:**

```markdown
## PLAN COMPLETION CHECKLIST

### Section Completeness
- [ ] Core feature section has ≥5 tasks
- [ ] Observability section has ≥5 tasks with specific metric names
- [ ] Error handling section has ≥3 tasks (if applicable)
- [ ] Performance section has ≥3 tasks with numeric thresholds (if applicable)

### Task Quality
- [ ] Every task has Description (≥2 sentences)
- [ ] Every struct/trait/handler/wiring task has Design Assertions (2-4 assertions citing design doc)
- [ ] Design assertions check structural properties (downcasts, field values, non-placeholder data) — NOT just `is_ok()`
- [ ] Every task has Test First with exact test name (test body includes design assertions)
- [ ] Every task has Verification command
- [ ] Every task has Expected Output (literal)
- [ ] No task contains forbidden patterns

### Self-Audit
1. Section with fewest tasks: ___________ Meets minimum? [ ]
2. Tasks missing verification: ___________
3. Did I treat observability with equal rigor as features? [ ]
```

---

## MANDATORY SELF-AUDIT

Before completing ANY plan, include this in your output:

```markdown
## Self-Audit Results

| Section | Count | Min | Status |
|---------|-------|-----|--------|
| Core Feature | X | 5 | ✅/❌ |
| Observability | X | 5 | ✅/❌ |
| Error Handling | X | 3 | ✅/❌ |
| Performance | X | 3 | ✅/❌ |

- Shortest task: X words (min 50)
- Tasks missing verification: [list or "none"]
- Tasks requiring design assertions (struct/trait/handler/wiring): [count]
- Tasks WITH design assertions: [count] — must equal above
- Design assertions that only check `is_ok()` or compilation: [list or "none" — must be "none"]
- Did I treat observability with equal rigor as features? [Yes/No]
```

**If self-audit shows violations, FIX THEM before presenting the plan.**

---

## REFERENCE

For complete example plans, see:
- [examples.md](examples.md) - Full example with all sections

---

## Related Skills

- **brainstorming** - Design BEFORE writing plans
- **executing-plans** - Execute plans methodically
- **test-driven-development** - TDD for each task
