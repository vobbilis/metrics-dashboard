# Plan Examples

Reference examples for the writing-plans skill.

---

## EXAMPLE: Password Reset Feature

```markdown
# Implementation Plan: Password Reset Feature

**Date:** 2024-01-15
**Status:** Draft

## Overview

Add password reset functionality allowing users to reset their
password via email link. Includes rate limiting to prevent abuse.

## Prerequisites

- [ ] Email service configured (SMTP settings in .env)
- [ ] User model has email field

## Tasks

### Task 1: Add resetToken field to User model

**Description:** Add two new fields to the User model to support password reset tokens. The resetToken stores a cryptographically random string, and resetTokenExpiry ensures tokens can't be used indefinitely.

**Test First:**
- File: `tests/models/user.test.ts`
- Test: `test_user_has_reset_token_fields`

**File:** `src/models/user.ts`

**Changes:**
- Add resetToken: string | null
- Add resetTokenExpiry: Date | null

**Code:**
```typescript
// Add to User interface
resetToken: string | null;
resetTokenExpiry: Date | null;
```

**Verification:**
```bash
npm run typecheck
```

**Expected Output:**
```
No errors found.
```

---

### Task 2: Create password reset request endpoint

**Description:** Create the endpoint that initiates password reset flow. This endpoint generates a secure token, stores it on the user, and sends an email with the reset link. Security note: always return the same message whether email exists or not.

**Test First:**
- File: `tests/routes/auth.test.ts`
- Test: `test_reset_request_generates_token`

**File:** `src/routes/auth.ts`

**Changes:**
- Add POST /auth/reset-password-request
- Generate token, save to user, send email

**Code:**
```typescript
router.post('/reset-password-request', async (req, res) => {
  const { email } = req.body;
  const user = await UserService.findByEmail(email);
  if (!user) {
    // Don't reveal if email exists
    return res.json({ message: 'If email exists, reset link sent' });
  }
  
  const token = crypto.randomBytes(32).toString('hex');
  await UserService.setResetToken(user.id, token);
  await EmailService.sendResetEmail(email, token);
  
  res.json({ message: 'If email exists, reset link sent' });
});
```

**Verification:**
```bash
curl -X POST localhost:3000/auth/reset-password-request \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com"}'
```

**Expected Output:**
```json
{"message": "If email exists, reset link sent"}
```

---

### Task 3: Create password reset endpoint

(... continues with same structure ...)

## Testing

- [ ] Unit test: token generation
- [ ] Unit test: token expiry validation
- [ ] Integration: full reset flow
- [ ] Manual: check email received

## Rollback Plan

1. Revert migration: `npm run migrate:rollback`
2. Remove new routes from auth.ts
3. Deploy previous version

## Self-Audit Results

| Section | Count | Min | Status |
|---------|-------|-----|--------|
| Core Feature | 5 | 5 | ✅ |
| Observability | 5 | 5 | ✅ |
| Error Handling | 3 | 3 | ✅ |
| Performance | 3 | 3 | ✅ |

- Shortest task: 52 words (min 50) ✅
- Tasks missing verification: none
- Did I treat observability with equal rigor? Yes
```
