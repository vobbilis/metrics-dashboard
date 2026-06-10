---
name: using-git-worktrees
description: Use when working on multiple features simultaneously or when you need isolated development environments. MANDATORY for parallel development. FORBIDDEN is branch switching with uncommitted work. REQUIRED is worktree per feature.
---

# Using Git Worktrees

## THE MANDATE

**One worktree per feature. Never switch branches with uncommitted work.**

Git worktrees let you have multiple branches checked out simultaneously in different directories. Use them for:
- Parallel feature development
- Code reviews while working
- Hot fixes without losing context
- Comparing implementations

---

## WHAT ARE WORKTREES?

```
Traditional Git:
  repo/
    └── (only one branch at a time)
    
With Worktrees:
  repo/                    ← main branch
  repo-feature-auth/       ← feature/auth branch  
  repo-feature-search/     ← feature/search branch
  repo-hotfix/             ← hotfix/bug-123 branch
```

Each worktree is a separate directory with its own branch checked out.

---

## WHEN TO USE WORKTREES

### ✅ Use Worktrees When:

- Starting a new feature
- Need to review code while mid-feature
- Emergency hotfix needed
- Comparing two approaches
- Running long tests in background

### ❌ Don't Use Worktrees When:

- Quick, single-file change
- Already on the right branch
- Just reading code

---

## FORBIDDEN PATTERNS

### ❌ Branch Switching With Uncommitted Work - BANNED

```bash
# ❌ FORBIDDEN
$ git status
On branch feature/auth
Changes not staged for commit:
  modified: src/auth.ts

$ git checkout main  # DANGER: losing work or carrying changes
```

```bash
# ✅ REQUIRED - Use worktree instead
$ git worktree add ../project-main main
$ cd ../project-main
# Now safely on main without losing feature work
```

### ❌ Stashing for Branch Switches - BANNED

```bash
# ❌ FORBIDDEN
$ git stash
$ git checkout other-branch
# ... do work ...
$ git checkout original-branch
$ git stash pop  # What if there are conflicts?
```

```bash
# ✅ REQUIRED - Use worktree
$ git worktree add ../project-other other-branch
# No stashing needed, original work untouched
```

---

## BASIC COMMANDS

### Create a Worktree

```bash
# From existing branch
git worktree add ../project-feature-name feature/feature-name

# Create new branch and worktree
git worktree add -b feature/new-feature ../project-new-feature main
```

### List Worktrees

```bash
git worktree list
# /path/to/project          abc1234 [main]
# /path/to/project-auth     def5678 [feature/auth]
# /path/to/project-search   ghi9012 [feature/search]
```

### Remove a Worktree

```bash
# After merging/completing work
git worktree remove ../project-feature-name

# Force remove (if branch deleted)
git worktree remove --force ../project-feature-name
```

### Prune Stale Worktrees

```bash
# Clean up worktrees for deleted directories
git worktree prune
```

---

## WORKFLOW: NEW FEATURE

```bash
# 1. Start from main
cd ~/projects/myproject
git checkout main
git pull

# 2. Create worktree for feature
git worktree add -b feature/user-auth ../myproject-user-auth main

# 3. Work in new worktree
cd ../myproject-user-auth

# 4. Do your work...
# ... commits ...

# 5. When done, clean up
cd ../myproject
git worktree remove ../myproject-user-auth
```

---

## WORKFLOW: EMERGENCY HOTFIX

```bash
# You're mid-feature, but need to hotfix main

# 1. Create hotfix worktree (don't touch current work)
git worktree add -b hotfix/critical-bug ../myproject-hotfix main

# 2. Fix in hotfix worktree
cd ../myproject-hotfix
# ... make fix ...
git commit -m "fix: critical bug"
git push

# 3. Create PR, get merged

# 4. Clean up
cd ../myproject
git worktree remove ../myproject-hotfix

# 5. Continue feature work (never left!)
```

---

## WORKFLOW: CODE REVIEW

```bash
# You're working on feature A, need to review feature B

# 1. Create worktree for review
git fetch origin
git worktree add ../myproject-review origin/feature/feature-b

# 2. Review in that worktree
cd ../myproject-review
npm test
# ... review code ...

# 3. Clean up after review
cd ../myproject
git worktree remove ../myproject-review

# 4. Continue your work
```

---

## DIRECTORY NAMING CONVENTION

```
project/                    # Main worktree (main branch)
project-feature-auth/       # Feature branch
project-feature-search/     # Another feature
project-hotfix-123/         # Hotfix branch
project-review-pr-45/       # For reviewing PR
```

Pattern: `<project>-<type>-<name>`

---

## WORKTREE CHECKLIST

Before creating a worktree:

- [ ] Am I on the right base branch?
- [ ] Is my base branch up to date? (`git pull`)
- [ ] Is the branch name correct?
- [ ] Is the directory path correct?

Before removing a worktree:

- [ ] Is all work committed?
- [ ] Is work pushed to remote?
- [ ] Is PR merged (if applicable)?
- [ ] No uncommitted changes?

---

## COMMON ISSUES

### "Branch already checked out"

```bash
# Error: 'feature/auth' is already checked out at '/path/to/other'

# Solution: You already have a worktree for this branch
git worktree list  # Find it
cd /path/to/other  # Use it
```

### "Worktree locked"

```bash
# Error: worktree is locked

# Solution: Unlock it
git worktree unlock ../project-feature
git worktree remove ../project-feature
```

### Worktree directory deleted manually

```bash
# You deleted the directory but git still tracks it

# Solution: Prune
git worktree prune
```

---

## INTEGRATION WITH OTHER SKILLS

### With brainstorming

```markdown
After brainstorming decides on approach:
1. Create worktree: git worktree add -b feature/x ../project-x main
2. Write plan in worktree
3. Execute plan in worktree
```

### With writing-plans

```markdown
Plans are written in the worktree:
docs/plans/YYYY-MM-DD-feature.md
```

### With code review

```markdown
Create review worktree to test PR locally before approving.
```

---

## QUICK REFERENCE

| Action | Command |
|--------|---------|
| Create from existing branch | `git worktree add <path> <branch>` |
| Create with new branch | `git worktree add -b <branch> <path> <base>` |
| List all | `git worktree list` |
| Remove | `git worktree remove <path>` |
| Force remove | `git worktree remove --force <path>` |
| Clean up stale | `git worktree prune` |

---

## ENFORCEMENT

This skill is MANDATORY for parallel development:

- **FORBIDDEN**: Branch switching with uncommitted work
- **FORBIDDEN**: Stashing for branch switches
- **FORBIDDEN**: Multiple features in one worktree
- **REQUIRED**: One worktree per feature
- **REQUIRED**: Clean up after merge
- **REQUIRED**: Meaningful directory names

**Worktrees eliminate context switching pain.**

---

## Related Skills

- **brainstorming** - Creates worktree for new features
- **finishing-a-development-branch** - Before removing worktree
- **writing-plans** - Plans live in feature worktree
