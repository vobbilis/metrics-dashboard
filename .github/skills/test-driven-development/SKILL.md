---
name: test-driven-development
description: Use when implementing ANY feature, bugfix, or code change. MANDATORY before writing implementation code. FORBIDDEN is writing implementation before tests. REQUIRED is RED-GREEN-REFACTOR cycle - write failing test first, then minimal code to pass, then refactor.
---

# Test-Driven Development

## The Iron Law

```
NO PRODUCTION CODE WITHOUT A FAILING TEST FIRST
```

Write code before the test? **Delete it.** Start over.

**No exceptions:**
- Don't keep it as "reference"
- Don't "adapt" it while writing tests
- Don't look at it
- Delete means delete

Implement fresh from tests. Period.

**Violating the letter of the rules is violating the spirit of the rules.**

---

## When to Use

**Always:**
- New features
- Bug fixes
- Refactoring
- Behavior changes

**Exceptions (ask your human partner):**
- Throwaway prototypes
- Generated code
- Configuration files

Thinking "skip TDD just this once"? Stop. That's rationalization.

---

## THE CYCLE: RED → GREEN → REFACTOR

```
┌─────────────────────────────────────────────────────────────┐
│  1. RED: Write a failing test                               │
│         ↓                                                   │
│  2. RUN: Watch it fail (MUST see red)                       │
│         ↓                                                   │
│  3. GREEN: Write MINIMAL code to pass                       │
│         ↓                                                   │
│  4. RUN: Watch it pass (MUST see green)                     │
│         ↓                                                   │
│  5. REFACTOR: Clean up (tests still pass)                   │
│         ↓                                                   │
│  6. COMMIT: Small, focused commit                           │
│         ↓                                                   │
│  REPEAT for next behavior                                   │
└─────────────────────────────────────────────────────────────┘
```

---

## FORBIDDEN PATTERNS

### ❌ Implementation Before Test - BANNED

```typescript
// ❌ FORBIDDEN - Writing implementation first
function calculateTotal(items) {
    return items.reduce((sum, item) => sum + item.price, 0);
}

// Then writing test after... TOO LATE
```

**If implementation exists without a failing test, DELETE IT.**

### ❌ Multiple Behaviors Per Test - BANNED

```typescript
// ❌ FORBIDDEN - Testing too much
it('should handle user registration', () => {
    // validates email AND creates user AND sends email AND logs event
});

// ✅ REQUIRED - One behavior per test
it('should reject invalid email format', () => { });
it('should create user with valid data', () => { });
it('should send welcome email after creation', () => { });
```

### ❌ Skipping the Fail Step - BANNED

```typescript
// ❌ FORBIDDEN - Never seeing red
// Writing test and implementation together

// ✅ REQUIRED - See the failure first
// 1. Write test
// 2. Run it - SEE IT FAIL
// 3. Then write implementation
```

### ❌ Placeholder Tests - BANNED (CRITICAL)

```rust
// ❌ FORBIDDEN - Fake tests that always pass
#[test]
fn test_feature_x() {
    assert!(true, "Placeholder - implement later");
}

#[test]
fn test_feature_y() {
    let _unused = setup_data();
    // TODO: add assertions
    assert!(true);
}

#[test]
fn test_feature_z() {
    // Will be implemented with actual function
    assert!(true, "Placeholder");
}
```

**A test without real assertions is NOT A TEST. It's a lie.**

**DETECTION:** If a test contains ANY of these patterns, DELETE IT:
- `assert!(true)` or `assert!(true, "...")`
- `// TODO` or `// PLACEHOLDER` in test body
- Variables prefixed with `_` that are never asserted on
- Empty test bodies or tests with only setup code
- Comments like "will be implemented later"

**ENFORCEMENT:** After writing ANY test:
1. Run it with `cargo test <test_name>`
2. You MUST see a **FAILURE** message
3. If it passes, it's not testing new functionality — rewrite it
4. Paste the failure output to prove RED phase complete

**NO EXCEPTIONS. NO "I'll fill it in later." DELETE AND REWRITE.**

---

## REQUIRED PATTERNS

### ✅ The RED Phase

Write one minimal test showing what should happen.

**Good test:**
```typescript
// Clear name, tests real behavior, one thing
it('should retry failed operations 3 times', async () => {
    let attempts = 0;
    const operation = () => {
        attempts++;
        if (attempts < 3) throw new Error('fail');
        return 'success';
    };

    const result = await retryOperation(operation);

    expect(result).toBe('success');
    expect(attempts).toBe(3);
});
```

**Bad test:**
```typescript
// Vague name, tests mock not code
it('retry works', async () => {
    const mock = jest.fn()
        .mockRejectedValueOnce(new Error())
        .mockResolvedValueOnce('success');
    await retryOperation(mock);
    expect(mock).toHaveBeenCalledTimes(2);
});
```

**Requirements:**
- One behavior per test
- Clear, descriptive name
- Real code (no mocks unless unavoidable)

### Verify RED - Watch It Fail

**MANDATORY. Never skip.**

```bash
npm test path/to/test.test.ts
```

Confirm:
- Test fails (not errors)
- Failure message is expected
- Fails because feature missing (not typos)

**Test passes?** You're testing existing behavior. Fix the test.

**Test errors?** Fix error, re-run until it fails correctly.

### ✅ The GREEN Phase

Write the **simplest** code to pass. Not elegant. Not complete. Just passing.

**Good - just enough:**
```typescript
async function retryOperation<T>(fn: () => Promise<T>): Promise<T> {
    for (let i = 0; i < 3; i++) {
        try {
            return await fn();
        } catch (e) {
            if (i === 2) throw e;
        }
    }
    throw new Error('unreachable');
}
```

**Bad - over-engineering:**
```typescript
// Adding configurable retries, backoff, logging...
// when test only asked for 3 retries
async function retryOperation<T>(
    fn: () => Promise<T>,
    options: RetryOptions = {}
): Promise<T> {
    const { maxRetries = 3, backoff = 'exponential' } = options;
    // ... 50 more lines
}
```

**YAGNI:** You Aren't Gonna Need It. Write minimal code.

### ✅ The REFACTOR Phase

```typescript
// STEP 5: Clean up while keeping tests green
function calculateTotal(items: CartItem[]): number {
    return items.reduce((sum, item) => sum + item.price, 0);
}

// STEP 6: Run tests again
// $ npm test
// ✅ PASS

// STEP 7: Commit
// $ git commit -m "feat: add calculateTotal function"
```

---

## Test Structure

### Arrange-Act-Assert

```typescript
it('should calculate total correctly', () => {
    // ARRANGE - Set up test data
    const items = [{ price: 10 }, { price: 20 }];
    
    // ACT - Perform the action
    const result = calculateTotal(items);
    
    // ASSERT - Verify the outcome
    expect(result).toBe(30);
});
```

### Describe Blocks

```typescript
describe('UserService', () => {
    describe('create', () => {
        it('should create user with valid data', () => { });
        it('should reject duplicate email', () => { });
        it('should hash password before saving', () => { });
    });

    describe('findById', () => {
        it('should return user when exists', () => { });
        it('should return null when not found', () => { });
    });
});
```

---

## Commit Rhythm

**Commit after each GREEN-REFACTOR cycle:**

```bash
# After first test passes
git commit -m "feat: add basic calculateTotal"

# After second test passes  
git commit -m "feat: handle empty array in calculateTotal"

# After third test passes
git commit -m "feat: handle negative prices in calculateTotal"
```

**Small commits = easy rollback = safety.**

---

## Checklist

### Before Writing ANY Code

- [ ] Test file exists or created
- [ ] Test is written
- [ ] Test has been run
- [ ] Test FAILED (saw red)

### After Test Fails

- [ ] Write MINIMAL implementation
- [ ] Run test
- [ ] Test PASSED (saw green)
- [ ] Refactor if needed
- [ ] Tests still pass
- [ ] Commit

### For Each Feature

- [ ] Break into small behaviors
- [ ] One test per behavior
- [ ] RED-GREEN-REFACTOR each
- [ ] Commit after each cycle

---

## Anti-Patterns to Avoid

| Anti-Pattern | Why It's Wrong |
|--------------|----------------|
| "I'll write tests later" | Tests never get written |
| "This is too simple to test" | Simple code breaks too |
| "I'll test multiple things" | Hard to debug failures |
| "I know it works" | Prove it with a test |
| "Tests slow me down" | Bugs slow you down more |

---

## MANDATORY TEST QUALITY CATEGORIES (CRITICAL)

**Tests must HUNT FOR BUGS, not just verify happy paths.**

Writing only "given valid input, expect valid output" tests is **FORBIDDEN**. Every feature must have tests in ALL these categories:

### 1. Happy Path Tests (MINIMUM BAR)
```rust
#[test]
fn test_basic_functionality() {
    assert_eq!(humanize(1234.0), "1.234k");
}
```

### 2. Edge Case Tests (REQUIRED)
```rust
#[test]
fn test_boundary_values() {
    assert_eq!(humanize(0.0), "0");
    assert_eq!(humanize(-0.0), "0");
    assert_eq!(humanize(f64::MIN), "..."); // smallest value
    assert_eq!(humanize(f64::MAX), "..."); // largest value
}
```

### 3. Invalid Input Tests (REQUIRED)
```rust
#[test]
fn test_invalid_inputs() {
    assert_eq!(humanize(f64::NAN), "NaN");
    assert_eq!(humanize(f64::INFINITY), "+Inf");
    assert_eq!(humanize(f64::NEG_INFINITY), "-Inf");
}

#[test]
fn test_wrong_type_inputs() {
    // If function expects number, what happens with string?
    // If function expects string, what happens with null/empty?
    let result = function_under_test("not_a_number");
    assert!(result.is_err() || result == expected_fallback);
}
```

### 4. Unicode/Encoding Tests (REQUIRED for string functions)
```rust
#[test]
fn test_unicode_handling() {
    assert_eq!(title("héllo wörld"), "Héllo Wörld");
    assert_eq!(title("日本語"), "日本語");
    assert_eq!(title("emoji 🎉 test"), "Emoji 🎉 Test");
    assert_eq!(title(""), "");  // empty string
    assert_eq!(title("   "), "   ");  // whitespace only
}
```

### 5. Overflow/Underflow Tests (REQUIRED for numeric functions)
```rust
#[test]
fn test_numeric_extremes() {
    // Test values that might overflow internal calculations
    assert!(humanize(1e308).len() > 0);  // near f64::MAX
    assert!(humanize(1e-308).len() > 0); // near f64::MIN_POSITIVE
    assert!(humanize(-1e308).len() > 0); // negative extreme
}
```

### 6. Format String / Injection Tests (REQUIRED for format functions)
```rust
#[test]
fn test_format_injection() {
    // Ensure format specifiers don't cause crashes or injection
    let result = printf("%s %s %s", &["only_one"]);
    assert!(result.contains("only_one") || result.contains("MISSING"));
    
    let result = printf("%n%n%n", &[]);  // %n is dangerous in C
    assert!(!result.is_empty());  // Should not crash
}
```

### 7. Comparison Tests (HIGHLY RECOMMENDED)
```rust
#[test]
fn test_matches_reference_implementation() {
    // Compare against known-good reference (e.g., actual Prometheus)
    // Or use golden files with expected outputs
    let prometheus_output = include_str!("golden/humanize_1000.txt");
    assert_eq!(humanize(1000.0), prometheus_output.trim());
}
```

### THE TEST QUALITY CHECKLIST

Before marking any test suite complete:

- [ ] **Happy path** - Basic functionality works
- [ ] **Empty/null/zero** - Handles empty inputs gracefully  
- [ ] **Boundaries** - Min/max/overflow values don't crash
- [ ] **Invalid types** - Wrong input types handled
- [ ] **Unicode** - Non-ASCII characters work (if applicable)
- [ ] **Injection** - Format strings/special chars can't break it
- [ ] **Negative values** - Negative inputs handled correctly
- [ ] **NaN/Infinity** - Special float values handled (if numeric)
- [ ] **Reference comparison** - Matches known-good implementation

**FORBIDDEN: "The tests pass" without covering ALL applicable categories above.**

The goal of testing is to **find bugs before production**, not to achieve a green checkmark.

---

## Enforcement

This skill is MANDATORY for all implementation work:

- **FORBIDDEN**: Implementation before failing test
- **FORBIDDEN**: `assert!(true)` or any placeholder assertion
- **FORBIDDEN**: Proceeding without showing actual test failure output
- **REQUIRED**: See RED before writing code (paste failure output as proof)
- **REQUIRED**: See GREEN before refactoring
- **REQUIRED**: Commit after each cycle

**If you write code without a failing test first, delete it and start over.**
**If you write a test that passes immediately, delete it and write a real test.**

---

## Related Skills

- **systematic-debugging** - When tests reveal bugs
- **backend-dev-guidelines** - Backend testing patterns
- **frontend-dev-guidelines** - Frontend testing patterns
