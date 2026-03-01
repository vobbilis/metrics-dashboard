---
name: systematic-debugging
description: Use when encountering ANY bug, unexpected behavior, failing test, or error. MANDATORY for all debugging - do not guess. FORBIDDEN is random code changes hoping to fix issues. REQUIRED is the 4-phase process - reproduce, isolate, identify root cause, then fix.
---

# Systematic Debugging

## THE MANDATE

**Do not guess. Do not make random changes. Follow this process.**

If you change code without understanding WHY it will fix the problem, you have failed.

---

## USE THIS ESPECIALLY WHEN UNDER TIME PRESSURE

This sounds counterintuitive. When you're stressed and need a fix NOW, it feels wrong to slow down and follow a process.

**But this is exactly when you need it most.**

Why? Because when under pressure:
- You're more likely to make random changes
- You're more likely to fix symptoms instead of causes
- You're more likely to introduce NEW bugs
- Quick hacks become permanent, creating tech debt

**The systematic approach is FASTER than random guessing**, even when it feels slower.

```markdown
❌ PANICKED DEBUGGING:
- Try random fix #1 → Doesn't work (5 min)
- Try random fix #2 → Makes it worse (10 min)
- Revert, try fix #3 → Partial fix (15 min)
- Find new bug from fix #3 → More panic (20 min)
- Total: 50+ minutes, still broken

✅ SYSTEMATIC DEBUGGING:
- Reproduce: 5 min
- Isolate: 10 min
- Root cause: 10 min
- Fix + verify: 5 min
- Total: 30 minutes, actually fixed
```

---

## THE 4-PHASE PROCESS

```
┌─────────────────────────────────────────────────────────────┐
│  PHASE 1: REPRODUCE                                         │
│  Can you make the bug happen consistently?                  │
│         ↓                                                   │
│  PHASE 2: ISOLATE                                           │
│  What is the smallest case that shows the bug?              │
│         ↓                                                   │
│  PHASE 3: IDENTIFY ROOT CAUSE                               │
│  WHY does it fail? (Not just WHERE)                         │
│         ↓                                                   │
│  PHASE 4: FIX AND VERIFY                                    │
│  Fix the root cause. Verify with test.                      │
└─────────────────────────────────────────────────────────────┘
```

---

## FORBIDDEN PATTERNS

### ❌ Random Changes - BANNED

```typescript
// ❌ FORBIDDEN - Changing things hoping it helps
// "Maybe if I add a timeout..."
await new Promise(r => setTimeout(r, 1000));

// "Let me try wrapping in try/catch..."
try { thing() } catch (e) { }

// "What if I make this async..."
async function thing() { }
```

**If you don't know WHY a change will help, don't make it.**

### ❌ Fixing Symptoms - BANNED

```typescript
// Bug: User sees stale data after update
// ❌ FORBIDDEN - Fixing symptom
const forceRefresh = () => window.location.reload();

// ✅ REQUIRED - Finding root cause
// WHY is data stale? → Cache not invalidated → Fix cache invalidation
```

### ❌ Multiple Changes At Once - BANNED

```typescript
// ❌ FORBIDDEN - Changing 5 things at once
// Now you don't know which one fixed it (or broke something else)

// ✅ REQUIRED - One change at a time
// Change one thing → Test → Observe → Repeat
```

---

## PHASE 1: REPRODUCE

**Goal:** Make the bug happen consistently.

### Checklist

- [ ] Can you trigger the bug on demand?
- [ ] What exact steps reproduce it?
- [ ] What input causes it?
- [ ] What environment? (dev/staging/prod)
- [ ] Does it happen every time or intermittently?

### Questions to Answer

```markdown
1. STEPS TO REPRODUCE:
   - Step 1: ...
   - Step 2: ...
   - Step 3: Bug appears

2. EXPECTED: What should happen?

3. ACTUAL: What actually happens?

4. FREQUENCY: Always / Sometimes / Rarely

5. ENVIRONMENT: Node version, browser, OS
```

**If you can't reproduce it, you can't fix it.**

---

## PHASE 2: ISOLATE

**Goal:** Find the smallest case that shows the bug.

### Techniques

```typescript
// BINARY SEARCH - Comment out half the code
// Does bug still happen? 
// Yes → Bug is in remaining code
// No → Bug was in removed code
// Repeat until isolated

// MINIMAL REPRODUCTION
// Remove everything not needed to trigger bug
// What's the simplest case?

// INPUT REDUCTION  
// Large input causes bug → What's smallest input that fails?
```

### Checklist

- [ ] Removed unrelated code
- [ ] Simplified the input
- [ ] Found minimal reproduction
- [ ] Can explain WHAT fails (not yet WHY)

---

## PHASE 3: IDENTIFY ROOT CAUSE

**Goal:** Understand WHY it fails, not just WHERE.

### The 5 Whys

```markdown
Bug: User sees error on form submit

WHY? → API returns 500
WHY? → Database query fails  
WHY? → Column doesn't exist
WHY? → Migration wasn't run
WHY? → Deploy script skipped migrations

ROOT CAUSE: Deploy script skips migrations
FIX: Update deploy script to run migrations
```

### Investigation Tools

```typescript
// ADD LOGGING
console.log('Before operation:', { state, input });
await operation();
console.log('After operation:', { result });

// CHECK ASSUMPTIONS
console.log('Is user defined?', !!user);
console.log('User ID type:', typeof user?.id);

// TRACE DATA FLOW
// Where does the data come from?
// How does it transform?
// Where does it go wrong?
```

### Multi-Component Debugging

When data flows between components (frontend ↔ API, service ↔ database), **instrument both sides**:

```typescript
// ❌ FORBIDDEN - Only checking one side
// "The frontend is sending the right data" (but did you verify?)
// "The API is returning correct response" (but did you log it?)

// ✅ REQUIRED - Instrument both sides
// FRONTEND - Before sending
console.log('REQUEST →', { url, method, body: JSON.stringify(payload) });

// API - On receiving  
console.log('← RECEIVED', { path: req.path, body: req.body });

// API - Before responding
console.log('RESPONSE →', { status, body: JSON.stringify(result) });

// FRONTEND - On receiving
console.log('← RESPONSE', { status: res.status, data: res.data });
```

**Why both sides?** The request might transform in transit (middleware, serialization, headers). What frontend sends ≠ what API receives.

### Timestamp Your Logs

When debugging async or timing issues:

```typescript
const timestamp = () => new Date().toISOString().slice(11, 23);

console.log(`[${timestamp()}] Starting operation`);
await operation();
console.log(`[${timestamp()}] Operation complete`);
// Output: [14:32:15.123] Starting operation
//         [14:32:15.456] Operation complete
```

### Checklist

- [ ] Can explain WHY bug happens (not just where)
- [ ] Root cause is identified (not symptom)
- [ ] Fix addresses root cause
- [ ] Understand full data flow

---

## PHASE 4: FIX AND VERIFY

**Goal:** Fix root cause. Prove it's fixed.

### Process

```typescript
// 1. WRITE TEST THAT FAILS
it('should handle the edge case', () => {
    // This test reproduces the bug
    expect(buggyBehavior()).toBe(correct);
});
// RUN → See it FAIL

// 2. FIX ROOT CAUSE
// Make the minimal change to address root cause

// 3. RUN TEST
// RUN → See it PASS

// 4. RUN ALL TESTS
// Ensure fix didn't break anything else

// 5. VERIFY IN ORIGINAL CONTEXT
// Does the original bug reproduction pass now?
```

### Checklist

- [ ] Test written that catches the bug
- [ ] Test fails before fix
- [ ] Root cause fix implemented
- [ ] Test passes after fix
- [ ] All other tests still pass
- [ ] Original reproduction no longer shows bug

---

## Defense in Depth

After fixing, add protection:

```typescript
// 1. ADD VALIDATION
if (!user?.id) {
    throw new Error('User ID required');
}

// 2. ADD LOGGING
console.log('Processing user:', user.id);

// 3. ADD TEST
it('should throw if user ID missing', () => {
    expect(() => process(null)).toThrow();
});
```

---

## Anti-Patterns

| Anti-Pattern | Why It's Wrong |
|--------------|----------------|
| "Let me just try..." | Random changes waste time |
| "It works on my machine" | Environment is a variable |
| "I'll add a retry" | Hides the real problem |
| "Let me restart the server" | Doesn't fix root cause |
| "I changed 10 things and it works" | Don't know what fixed it |

---

## Quick Reference

| Phase | Question | Output |
|-------|----------|--------|
| Reproduce | Can I trigger it? | Steps to reproduce |
| Isolate | What's minimal case? | Smallest failing example |
| Root Cause | WHY does it fail? | Understanding of cause |
| Fix | Does test pass? | Verified fix with test |

---

## Enforcement

This skill is MANDATORY for all debugging:

- **FORBIDDEN**: Random changes
- **FORBIDDEN**: Fixing symptoms
- **REQUIRED**: Follow 4-phase process
- **REQUIRED**: Understand WHY before fixing
- **REQUIRED**: Test proves fix works

**If you make changes without understanding root cause, you're not debugging - you're guessing.**

---

## Related Skills

- **test-driven-development** - Write test for bug first
- **error-tracking** - Capture errors to Sentry
