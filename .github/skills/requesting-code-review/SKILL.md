---
name: requesting-code-review
description: Use when your code is ready for review by a teammate or before merging. MANDATORY before merge requests. FORBIDDEN is requesting review without self-review. REQUIRED is pre-review checklist and clear review request.
---

# Requesting Code Review

## THE MANDATE

**Review your own code before asking others to review it.**

Before requesting a code review:
1. Complete self-review checklist
2. Run all verifications
3. Write clear review request
4. Make reviewer's job easy

---

## BEFORE REQUESTING REVIEW

Complete this checklist FIRST:

### Self-Review Checklist

```markdown
## Pre-Review Checklist

### Code Quality
- [ ] Code compiles without errors
- [ ] No linting errors or warnings
- [ ] All tests pass
- [ ] New code has tests
- [ ] No console.log/debugging left behind
- [ ] No commented-out code
- [ ] No TODO comments without tickets

### Functionality
- [ ] Feature works as specified
- [ ] Edge cases handled
- [ ] Error handling in place
- [ ] Verified manually

### Documentation
- [ ] Code is self-documenting OR has comments
- [ ] README updated if needed
- [ ] API docs updated if needed

### Git Hygiene
- [ ] Commits are atomic and meaningful
- [ ] Branch is up to date with main
- [ ] No merge conflicts
- [ ] Commit messages follow convention
```

---

## FORBIDDEN PATTERNS

### ❌ Review Without Self-Check - BANNED

```markdown
❌ FORBIDDEN:
"Code is ready for review!"
(Without running tests, linting, self-reviewing)

✅ REQUIRED:
"I've completed the pre-review checklist:
- ✓ All tests passing (24/24)
- ✓ No lint errors
- ✓ Self-reviewed, no issues
- ✓ Verified feature works

Ready for review."
```

### ❌ Huge Reviews - BANNED

```markdown
❌ FORBIDDEN:
"Please review my 50 file, 3000 line change"

✅ REQUIRED:
Split into smaller, reviewable chunks:
- PR 1: Database schema changes (3 files)
- PR 2: Service layer (5 files)
- PR 3: API endpoints (4 files)
```

### ❌ Vague Review Requests - BANNED

```markdown
❌ FORBIDDEN:
"LGTM? Review plz"

✅ REQUIRED:
Clear context:
- What changed
- Why it changed
- What to focus on
- Any concerns
```

---

## THE REVIEW REQUEST TEMPLATE

```markdown
## Code Review Request

### Summary
[One-line description of change]

### Context
[Why this change is needed - link to ticket/issue]

### Changes
- [Change 1]
- [Change 2]
- [Change 3]

### Files Changed
- `path/to/file1.ts` - [brief description]
- `path/to/file2.ts` - [brief description]

### Testing
- [ ] Unit tests added/updated
- [ ] Integration tests pass
- [ ] Manual testing performed

**Test command:** `npm test -- feature-name`

### Areas to Focus
- [Specific area needing attention]
- [Any concerns or questions]

### Screenshots (if UI)
[Before/After screenshots]

### Checklist
- [x] Self-reviewed
- [x] Tests passing
- [x] No lint errors
- [x] Documentation updated
```

---

## MAKING REVIEWS EASIER

### 1. Small, Focused Changes

```markdown
✅ GOOD:
"This PR adds email validation to the user service"
(~100 lines, 3 files)

❌ BAD:
"This PR adds user management, email system, and admin panel"
(~2000 lines, 40 files)
```

### 2. Clear Commit History

```markdown
✅ GOOD:
- feat: add email validation schema
- feat: integrate validation in user service
- test: add email validation tests
- docs: update API documentation

❌ BAD:
- WIP
- fix stuff
- more fixes
- final final
- actually final
```

### 3. Annotate Complex Changes

```markdown
In your PR description:

**Note on UserService.ts line 45:**
I refactored the validation to use Zod instead of manual checks.
This changes the error format from string to structured object.
```

---

## WHEN TO REQUEST REVIEW

### DO Request Review When:

- Feature is complete and tested
- Self-review is done
- You need a second opinion
- Changes affect shared code
- Before merging to main

### DON'T Request Review When:

- Code doesn't compile
- Tests are failing
- You haven't self-reviewed
- It's a WIP you're still changing
- You're just looking for rubber-stamp

---

## REVIEW REQUEST EXAMPLES

### Good Request

```markdown
## PR: Add rate limiting to auth endpoints

### Summary
Adds rate limiting to prevent brute force attacks on login/reset endpoints.

### Context
Security audit identified lack of rate limiting. Ticket: SEC-123

### Changes
- Added rate-limiter-flexible package
- Created RateLimitMiddleware
- Applied to POST /auth/* routes
- Added tests for rate limit behavior

### Files
- `src/middleware/rate-limit.ts` - New middleware
- `src/routes/auth.ts` - Applied middleware
- `tests/auth.test.ts` - Added rate limit tests

### Testing
```bash
npm test -- auth
# 12 tests passing
```

### Focus Areas
- Is the rate limit (5 attempts/minute) appropriate?
- Should we add Redis for distributed rate limiting?

### Checklist
- [x] Self-reviewed
- [x] Tests passing (12/12)
- [x] No lint errors
- [x] Security implications considered
```

### Bad Request

```markdown
Review please

Changed some auth stuff
```

---

## RESPONDING TO REVIEW REQUESTS

When someone asks you to review:

1. Check if pre-review checklist is done
2. If not, ask them to complete it first
3. If yes, proceed with review

```markdown
"Before I review, can you confirm:
- [ ] All tests pass?
- [ ] You've self-reviewed?
- [ ] No lint errors?"
```

---

## ENFORCEMENT

This skill is MANDATORY before code review:

- **FORBIDDEN**: Request review without self-review
- **FORBIDDEN**: Leave tests failing
- **FORBIDDEN**: Vague review requests
- **FORBIDDEN**: Massive PRs without splitting
- **REQUIRED**: Complete pre-review checklist
- **REQUIRED**: Clear review request template
- **REQUIRED**: Focused, small changes
- **REQUIRED**: Context for reviewers

**Respect the reviewer's time.**

---

## Related Skills

- **receiving-code-review** - When you get feedback
- **verification-before-completion** - Verify before review
- **finishing-a-development-branch** - After review approval
