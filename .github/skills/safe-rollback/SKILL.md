---
name: safe-rollback
description: Use when reverting changes, undoing modifications, rolling back features, or when something isn't working and you need to return to a known-good state. MANDATORY when any regression is detected. FORBIDDEN is manual partial reverts without git diff verification. REQUIRED is using git commands for complete rollback and verifying with diff before/after.
---

# Safe Rollback

## THE MANDATE

**Never manually revert changes. Use git.**

When you need to undo changes:
1. ALWAYS use `git diff` first to see ALL changes
2. ALWAYS use `git checkout -- <file>` for complete rollback
3. NEVER selectively edit code from memory
4. VERIFY the rollback is complete with `git diff` again

---

## WHY THIS SKILL EXISTS

### The Incident

A feature was added with changes to **multiple locations** in a file:
- Location 1: Import statements
- Location 2: `new()` method  
- Location 3: `create_fresh_context()` method

When reverting due to a performance regression:
- ❌ Manually edited to remove imports
- ❌ Manually edited one method
- ❌ **FORGOT** the other method
- ❌ Regression persisted for 30+ minutes of debugging

### The Fix

```bash
# This would have taken 5 seconds:
git checkout -- src/query/engine.rs
```

---

## FORBIDDEN PATTERNS

### ❌ Manual Selective Reverts - BANNED

```markdown
❌ FORBIDDEN:
"I'll manually remove the code I added"
*Edits file*
*Misses one location*
*Spends 30 minutes debugging*

✅ REQUIRED:
git diff src/query/engine.rs   # See ALL changes first
git checkout -- src/query/engine.rs  # Complete rollback
git diff src/query/engine.rs   # Verify: should be empty
```

### ❌ Reverting Without Seeing Full Diff - BANNED

```markdown
❌ FORBIDDEN:
"I remember I changed the imports and one function"
*Reverts those two things*
*Forgets the third change*

✅ REQUIRED:
git diff <file>  # ALWAYS run this first
# See the COMPLETE list of changes
# Then decide: full rollback or selective
```

### ❌ Relying on Memory - BANNED

```markdown
❌ FORBIDDEN:
"I think I changed these lines..."
"Let me revert what I remember adding..."

✅ REQUIRED:
"Let me check what actually changed:"
git diff --stat  # Overview of changed files
git diff <file>  # Exact line changes
```

### ❌ Partial Rollback Without Verification - BANNED

```markdown
❌ FORBIDDEN:
*Makes selective edits*
*Runs tests*
"Why is it still failing?"

✅ REQUIRED:
*Makes selective edits*
git diff <file>  # Verify: are ANY changes remaining?
# If diff is empty: rollback complete
# If diff shows changes: more to revert
```

---

## REQUIRED PATTERNS

### ✅ The Complete Rollback (Preferred)

When you need to fully undo changes to a file:

```bash
# Step 1: See what changed
git diff src/path/to/file.rs

# Step 2: Complete rollback
git checkout -- src/path/to/file.rs

# Step 3: Verify rollback is complete
git diff src/path/to/file.rs
# Should output nothing (empty diff)

# Step 4: Rebuild and test
cargo build && cargo test
```

### ✅ The Selective Rollback (When Needed)

When you need to keep some changes but revert others:

```bash
# Step 1: See ALL changes
git diff src/path/to/file.rs > /tmp/changes.diff
cat /tmp/changes.diff  # Review carefully

# Step 2: Use interactive restore
git checkout -p -- src/path/to/file.rs
# Git will ask about each hunk: y/n/e

# Step 3: Verify remaining changes are what you want
git diff src/path/to/file.rs
# Should only show changes you intended to keep
```

### ✅ Multi-File Rollback

When reverting a feature that touched multiple files:

```bash
# Step 1: See all modified files
git status --short

# Step 2: See changes per file
git diff --stat

# Step 3: Rollback all related files
git checkout -- src/query/engine.rs src/query/mod.rs src/catalog/cache.rs

# Step 4: Verify
git status --short  # Files should no longer appear as modified
```

### ✅ Rollback to Specific Commit

When current HEAD is also modified and you need a known-good state:

```bash
# Step 1: Find the good commit
git log --oneline -10

# Step 2: See what changed since that commit
git diff abc123..HEAD -- src/path/to/file.rs

# Step 3: Restore file from that commit
git checkout abc123 -- src/path/to/file.rs

# Step 4: Verify
git diff HEAD -- src/path/to/file.rs
```

---

## DECISION TREE

```
Need to undo changes?
        │
        ▼
┌───────────────────────┐
│ Run: git diff <file>  │
│ See ALL changes first │
└───────────┬───────────┘
            │
            ▼
    ┌───────────────┐
    │ Want to keep  │
    │ ANY changes?  │
    └───────┬───────┘
            │
     ┌──────┴──────┐
     │             │
    NO            YES
     │             │
     ▼             ▼
┌─────────┐  ┌─────────────┐
│ FULL    │  │ SELECTIVE   │
│ ROLLBACK│  │ ROLLBACK    │
└────┬────┘  └──────┬──────┘
     │              │
     ▼              ▼
git checkout   git checkout -p
-- <file>      -- <file>
     │              │
     ▼              ▼
┌─────────────────────────┐
│ VERIFY: git diff <file> │
│ Confirm rollback worked │
└─────────────────────────┘
```

---

## CHECKLIST

### Before Any Rollback

- [ ] Run `git status --short` to see all modified files
- [ ] Run `git diff <file>` to see EXACT changes
- [ ] Count the number of change locations (hunks)
- [ ] Decide: full rollback or selective?

### During Rollback

- [ ] Use `git checkout -- <file>` for full rollback
- [ ] Use `git checkout -p -- <file>` for selective rollback
- [ ] NEVER manually edit to "remove" code

### After Rollback

- [ ] Run `git diff <file>` to verify rollback
- [ ] For full rollback: diff should be empty
- [ ] For selective: diff should show only intended changes
- [ ] Rebuild: `cargo build` or equivalent
- [ ] Retest: run the test that showed the regression
- [ ] Confirm regression is fixed

---

## COMMON MISTAKES

### Mistake 1: "I'll Just Remove What I Added"

```markdown
❌ You think: "I added an import and one function call"
❌ Reality: You added imports, modified 2 functions, added logging
❌ Result: Partial revert, bug persists

✅ Solution: git diff FIRST, then decide
```

### Mistake 2: "The Diff Is Too Long, I'll Skim It"

```markdown
❌ Diff shows 50 lines changed
❌ You skim and miss the 3rd location
❌ Result: Incomplete rollback

✅ Solution: git checkout -- <file> for complete rollback
           Or use git diff --stat for summary first
```

### Mistake 3: "I'll Revert File by File"

```markdown
❌ You revert engine.rs
❌ You forget mod.rs also has changes
❌ Result: Build breaks or behavior inconsistent

✅ Solution: git status first, then revert all related files
```

---

## EMERGENCY ROLLBACK

When everything is broken and you need to get back to a working state:

```bash
# Nuclear option: discard ALL uncommitted changes
git checkout -- .
git clean -fd  # Remove untracked files (careful!)

# Safer: stash changes for later review
git stash push -m "broken-feature-attempt"
# Now you're at last commit
# Later: git stash pop to get changes back
```

---

## INTEGRATION WITH OTHER SKILLS

This skill connects with:

- **verification-before-completion**: After rollback, verify the regression is fixed
- **systematic-debugging**: Rollback is often part of isolating a bug
- **code-refactoring**: Large refactors may need partial rollback

When in doubt: **FULL ROLLBACK FIRST**, then re-add changes incrementally.
