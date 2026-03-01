---
name: finishing-a-development-branch
description: Use when your feature branch is ready to merge or when deciding between merge and PR. MANDATORY before merging. FORBIDDEN is merging without verification. REQUIRED is final checklist and clean merge.
---

# Finishing a Development Branch

## THE MANDATE

**A branch is only done when it's properly merged and cleaned up.**

Before finishing:
1. All work committed and pushed
2. Tests passing
3. Review complete (if required)
4. Merge strategy decided
5. Clean up after merge

---

## THE DECISION: MERGE vs PR

### When to Merge Directly

```markdown
Direct merge is appropriate when:
- Small, low-risk change
- You're the only maintainer
- Team agreement allows it
- Already reviewed in worktree
- Hot fix with urgency
```

### When to Create a PR

```markdown
PR is required when:
- Team uses PR workflow
- Change needs review
- CI/CD triggers needed
- Documentation of change needed
- Multiple stakeholders
```

---

## FORBIDDEN PATTERNS

### ❌ Merging Without Verification - BANNED

```bash
# ❌ FORBIDDEN
git checkout main
git merge feature/x
# (Without running tests, checking for conflicts)
```

```bash
# ✅ REQUIRED
# First verify everything
npm test
npm run lint
npm run build
# Then merge
git checkout main
git merge feature/x
```

### ❌ Force Pushing to Main - BANNED

```bash
# ❌ FORBIDDEN - NEVER
git push --force origin main
```

### ❌ Leaving Stale Branches - BANNED

```bash
# ❌ FORBIDDEN
# Branch merged but still exists locally and remotely
git branch
# * main
#   feature/old-feature  ← stale

# ✅ REQUIRED
# Clean up after merge
git branch -d feature/old-feature
git push origin --delete feature/old-feature
```

### ❌ Merge Commits Without Context - BANNED

```bash
# ❌ FORBIDDEN
git merge feature/x
# Merge branch 'feature/x'  ← no context

# ✅ REQUIRED
git merge feature/x -m "feat: add user authentication system

- Added login/logout endpoints
- JWT token generation
- Password hashing with bcrypt

Closes #123"
```

---

## PRE-MERGE CHECKLIST

```markdown
## Branch Completion Checklist

### Code Quality
- [ ] All tests passing
- [ ] No lint errors
- [ ] Build succeeds
- [ ] No debug code left

### Git Status
- [ ] All changes committed
- [ ] Pushed to remote
- [ ] Branch up to date with main
- [ ] No merge conflicts

### Review (if applicable)
- [ ] PR created
- [ ] Review requested
- [ ] Review approved
- [ ] All comments addressed

### Documentation
- [ ] README updated (if needed)
- [ ] CHANGELOG updated (if needed)
- [ ] API docs updated (if needed)
```

---

## WORKFLOW: DIRECT MERGE

```bash
# 1. Ensure feature branch is complete
cd ~/projects/project-feature
git status  # Nothing to commit
npm test    # All passing
npm run build  # Success

# 2. Update main
git checkout main
git pull origin main

# 3. Merge feature
git merge feature/user-auth -m "feat: add user authentication

- Login/logout endpoints
- JWT token handling
- Password security

Closes #123"

# 4. Push
git push origin main

# 5. Clean up
git branch -d feature/user-auth
git push origin --delete feature/user-auth

# 6. Remove worktree (if used)
cd ~/projects/project
git worktree remove ~/projects/project-feature
```

---

## WORKFLOW: PULL REQUEST

```bash
# 1. Ensure feature branch is complete
git status  # Nothing to commit
npm test    # All passing

# 2. Push feature branch
git push -u origin feature/user-auth

# 3. Create PR (via GitHub CLI or web)
gh pr create \
  --title "feat: add user authentication" \
  --body "## Summary
- Login/logout endpoints
- JWT token handling

## Testing
All tests passing

Closes #123"

# 4. Wait for review and CI

# 5. After approval, merge via GitHub

# 6. Clean up locally
git checkout main
git pull
git branch -d feature/user-auth

# 7. Remove worktree (if used)
git worktree remove ~/projects/project-feature
```

---

## HANDLING MERGE CONFLICTS

```bash
# When conflicts occur during merge

# 1. Don't panic
git merge feature/x
# CONFLICT in src/file.ts

# 2. Check what's conflicted
git status
# both modified: src/file.ts

# 3. Resolve conflicts
# Open file, fix conflicts manually
# Look for <<<<<<< HEAD and >>>>>>>

# 4. After fixing
git add src/file.ts
git commit -m "merge: resolve conflicts in src/file.ts"

# 5. Verify everything still works
npm test
npm run build
```

---

## MERGE STRATEGIES

### Merge Commit (Default)

```bash
git merge feature/x
# Creates merge commit, preserves history
```

Best for: Feature branches you want to track

### Squash Merge

```bash
git merge --squash feature/x
git commit -m "feat: complete feature description"
# Combines all commits into one
```

Best for: Messy branch history, small features

### Rebase and Merge

```bash
git checkout feature/x
git rebase main
git checkout main
git merge feature/x --ff-only
# Linear history
```

Best for: Clean, linear history requirement

---

## POST-MERGE CLEANUP

```bash
# 1. Delete local branch
git branch -d feature/x

# 2. Delete remote branch
git push origin --delete feature/x

# 3. Remove worktree (if used)
git worktree remove ../project-feature

# 4. Prune remote tracking branches
git fetch --prune

# 5. Verify
git branch -a  # Feature branch gone
```

---

## QUICK REFERENCE

| Action | Command |
|--------|---------|
| Merge with message | `git merge branch -m "message"` |
| Squash merge | `git merge --squash branch` |
| Delete local branch | `git branch -d branch` |
| Delete remote branch | `git push origin --delete branch` |
| Check for conflicts | `git merge --no-commit branch` |
| Abort merge | `git merge --abort` |

---

## BRANCH COMPLETION REPORT

After finishing:

```markdown
## Branch Completion Report

**Branch:** feature/user-auth
**Merged to:** main
**Merge type:** PR #45

### Summary
- Added user authentication system
- JWT token handling
- Password security with bcrypt

### Files Changed
- 8 files changed
- 342 insertions, 12 deletions

### Tests
- 12 new tests added
- All 156 tests passing

### Cleanup
- [x] Branch deleted locally
- [x] Branch deleted from remote
- [x] Worktree removed
- [x] PR closed
```

---

## ENFORCEMENT

This skill is MANDATORY when finishing branches:

- **FORBIDDEN**: Merge without verification
- **FORBIDDEN**: Force push to main
- **FORBIDDEN**: Leave stale branches
- **FORBIDDEN**: Merge commits without context
- **REQUIRED**: Complete pre-merge checklist
- **REQUIRED**: Meaningful merge message
- **REQUIRED**: Clean up after merge
- **REQUIRED**: Remove worktrees

**A branch isn't done until it's merged AND cleaned up.**

---

## Related Skills

- **requesting-code-review** - Before merge approval
- **using-git-worktrees** - Worktree cleanup
- **verification-before-completion** - Pre-merge verification
