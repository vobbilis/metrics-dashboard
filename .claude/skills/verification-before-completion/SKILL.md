---
name: verification-before-completion
description: Use when finishing ANY task, bug fix, feature, or change. MANDATORY before declaring work complete. FORBIDDEN is saying "done" without proof. REQUIRED is running verification and showing output.
---

# Verification Before Completion

## THE MANDATE

**Never say "done" without proof.**

Before declaring ANY work complete:
1. Run the verification
2. Show the output
3. Confirm it proves success

---

## FORBIDDEN PATTERNS

### ❌ Claiming Done Without Evidence - BANNED

```markdown
❌ FORBIDDEN:
"I've fixed the bug."
"The feature is implemented."
"Done! The tests should pass now."

✅ REQUIRED:
"I've fixed the bug. Here's the verification:
$ npm test -- --grep "user login"
✓ should authenticate valid users (45ms)
✓ should reject invalid passwords (12ms)
2 passing"
```

### ❌ Assuming It Works - BANNED

```markdown
❌ FORBIDDEN:
"This should work now."
"The code looks correct."
"I believe this fixes the issue."

✅ REQUIRED:
"Let me verify this works:"
*runs actual command*
*shows actual output*
"Confirmed working."
```

### ❌ Partial Verification - BANNED

```markdown
❌ FORBIDDEN:
"The new code compiles."
(But did it pass tests? Does it work?)

✅ REQUIRED:
1. Code compiles ✓
2. Tests pass ✓
3. Manual verification ✓
```

---

## THE VERIFICATION CHECKLIST

Before saying "complete," check ALL that apply:

### For Bug Fixes

- [ ] Wrote test that reproduces the bug
- [ ] Test failed before fix
- [ ] Test passes after fix
- [ ] All other tests still pass
- [ ] Showed test output

### For New Features

- [ ] Feature works as specified
- [ ] Tests written and passing
- [ ] Edge cases handled
- [ ] Showed working output

### TEST QUALITY VERIFICATION (MANDATORY)

Before declaring feature tests "complete", verify test coverage across ALL applicable categories:

```bash
# Audit your test file for quality categories
grep -c "test.*empty\|test.*null\|test.*zero" tests/feature_test.rs
grep -c "test.*unicode\|test.*UTF\|test.*emoji" tests/feature_test.rs  
grep -c "test.*overflow\|test.*max\|test.*min" tests/feature_test.rs
grep -c "test.*invalid\|test.*error\|test.*wrong" tests/feature_test.rs
grep -c "test.*NaN\|test.*Inf\|test.*negative" tests/feature_test.rs
```

**FORBIDDEN**: Marking tests complete if ANY of these return 0 for applicable functions.

| Category | Applicable To | Example |
|----------|---------------|---------|
| Empty/null/zero | All functions | `test_handles_empty_string` |
| Unicode | String functions | `test_title_with_japanese` |
| Overflow/min/max | Numeric functions | `test_humanize_max_f64` |
| Invalid type | All functions | `test_wrong_type_returns_error` |
| NaN/Infinity | Float functions | `test_humanize_nan` |
| Injection | Format functions | `test_printf_extra_specifiers` |

**ASK YOURSELF: "Would these tests catch a bug, or just confirm happy paths?"**

If tests only verify "valid input → valid output", they are INCOMPLETE.

### For Refactoring

- [ ] All existing tests pass
- [ ] Behavior unchanged
- [ ] Showed test output

### For Configuration Changes

- [ ] Config is valid (syntax check)
- [ ] Application starts
- [ ] Feature works with new config
- [ ] Showed verification

---

## ENFORCEMENT

This skill is MANDATORY for all completions:

- **FORBIDDEN**: "Done" without proof
- **FORBIDDEN**: "Should work" without verification
- **FORBIDDEN**: Assuming tests pass
- **REQUIRED**: Run verification command
- **REQUIRED**: Show actual output
- **REQUIRED**: Confirm success explicitly

**"Done" means "verified done."**

---

## Related Skills

- **test-driven-development** - Write tests first
- **systematic-debugging** - When verification reveals bugs

---

## NEXUS-DB SPECIFIC VERIFICATION

### E2E Test Commands (MEMORIZE THESE)

The correct tests to verify query functionality:

```bash
# Default run (crawl phase, preserves data)
./scripts/run_e2e.sh

# Run specific phases
./scripts/run_e2e.sh crawl      # Basic tests
./scripts/run_e2e.sh walk       # Component pair tests
./scripts/run_e2e.sh run        # Full pipeline tests
./scripts/run_e2e.sh scale      # Scale tests
./scripts/run_e2e.sh extreme    # Extreme load tests (93 PromQL queries)
./scripts/run_e2e.sh all        # Run all phases

# Clean mode (WIPES DATA - use for fresh start)
./scripts/run_e2e.sh extreme --clean

# The binary that actually runs the 93 PromQL query tests
./target/release/blackbox-e2e
```

### Key Files

| File | Purpose |
|------|---------|
| `scripts/run_e2e.sh` | E2E test orchestrator |
| `src/bin/blackbox-e2e.rs` | 93 PromQL query test binary |

### Test Phases

- **crawl**: Basic unit integration (fast)
- **walk**: Component pair tests
- **run**: Full E2E pipeline
- **scale**: Scale/load tests
- **extreme**: All 93 PromQL queries (THIS IS THE ONE FOR QUERY FIXES)
- **health**: Health check only

### MANDATORY for Query Changes

When fixing query issues (like label hydration), ALWAYS run:

```bash
./scripts/run_e2e.sh extreme --clean
```

This runs all 93 queries and gives the pass/fail count (target: 93/93).
