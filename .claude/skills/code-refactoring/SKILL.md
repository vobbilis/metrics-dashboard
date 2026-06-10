---
name: code-refactoring
description: Use when refactoring code for better organization, cleaner architecture, or improved maintainability. MANDATORY for file moves, component extraction, or fixing anti-patterns. FORBIDDEN is moving files without tracking imports. REQUIRED is the 4-phase process - discover, plan, execute, verify.
---

# Code Refactoring

## THE MANDATE

**Never move a file without tracking every import.**

Refactoring is surgery. One broken import can cascade into build failures across the codebase. Follow this process systematically.

---

## WHEN TO USE THIS SKILL

This skill is MANDATORY for:

- Moving or renaming files
- Breaking large components into smaller ones
- Reorganizing directory structures
- Fixing anti-patterns across codebase
- Updating import paths after file moves

---

## THE 4-PHASE PROCESS

```
┌─────────────────────────────────────────────────────────────┐
│  PHASE 1: DISCOVER                                          │
│  Map all dependencies and anti-patterns                     │
│         ↓                                                   │
│  PHASE 2: PLAN                                              │
│  Design new structure, create migration matrix              │
│         ↓                                                   │
│  PHASE 3: EXECUTE                                           │
│  Move files, update imports atomically                      │
│         ↓                                                   │
│  PHASE 4: VERIFY                                            │
│  Confirm no broken imports, all patterns fixed              │
└─────────────────────────────────────────────────────────────┘
```

---

## FORBIDDEN PATTERNS

### ❌ Moving Files Without Tracking - BANNED

```bash
# ❌ FORBIDDEN - Just moving a file
mv src/components/Dashboard.tsx src/features/dashboard/Dashboard.tsx
# Now 15 files have broken imports!

# ✅ REQUIRED - Track first, then move
# 1. Find all importers:
grep -r "from.*Dashboard" --include="*.tsx" src/
# 2. Document them
# 3. Move file
# 4. Update ALL imports immediately
```

### ❌ Moving Multiple Files At Once - BANNED

```markdown
❌ FORBIDDEN:
"I'll move all 10 files to the new structure"
*Moves everything at once*
*Build explodes with 50 import errors*

✅ REQUIRED:
"Moving Dashboard.tsx first"
*Move one file*
*Update all its imports*
*Verify build passes*
*Repeat for next file*
```

### ❌ Leaving "I'll Fix It Later" Imports - BANNED

```typescript
// ❌ FORBIDDEN - Temporary broken import
// TODO: Fix this import after refactor
// @ts-ignore
import { Dashboard } from '../../../old/path/Dashboard';

// ✅ REQUIRED - Fix immediately or don't move
import { Dashboard } from '@/features/dashboard';
```

---

## PHASE 1: DISCOVER

### Map Dependencies

Before moving ANY file, document every importer:

```bash
# Find all files that import Dashboard
grep -rn "from.*Dashboard" --include="*.tsx" --include="*.ts" src/

# Output example:
# src/pages/Home.tsx:5: import { Dashboard } from '../components/Dashboard'
# src/pages/Admin.tsx:8: import { Dashboard } from '../components/Dashboard'
# src/layouts/Main.tsx:12: import { Dashboard } from '../../components/Dashboard'
```

### Document Current Structure

```markdown
## Current Structure Analysis

**Target file:** src/components/Dashboard.tsx

**Imported by:**
1. src/pages/Home.tsx (line 5)
2. src/pages/Admin.tsx (line 8)
3. src/layouts/Main.tsx (line 12)

**Dependencies of Dashboard:**
- src/components/Chart.tsx
- src/hooks/useDashboardData.ts
- src/types/dashboard.ts
```

### Identify Anti-Patterns

Common patterns to fix during refactoring:

| Anti-Pattern | Fix |
|--------------|-----|
| Component > 300 lines | Extract sub-components |
| 5+ levels of nesting | Flatten or extract |
| Repeated code blocks | Extract to utility |
| Early return loading | Use LoadingOverlay/Suspense |
| Prop drilling 3+ levels | Use context or composition |

---

## PHASE 2: PLAN

### Design New Structure

```markdown
## Proposed Structure

**Current:**
```
src/components/
  Dashboard.tsx (800 lines)
  DashboardChart.tsx
  DashboardHeader.tsx
```

**Proposed:**
```
src/features/dashboard/
  index.ts (barrel export)
  Dashboard.tsx (main component, 150 lines)
  components/
    Chart.tsx
    Header.tsx
    Metrics.tsx (extracted from Dashboard)
    RecentActivity.tsx (extracted from Dashboard)
  hooks/
    useDashboardData.ts
  types.ts
```
```

### Create Migration Matrix

```markdown
## Import Update Matrix

| File to Move | Current Path | New Path | Files to Update |
|--------------|--------------|----------|-----------------|
| Dashboard.tsx | src/components/Dashboard | src/features/dashboard | Home.tsx, Admin.tsx, Main.tsx |
| DashboardChart.tsx | src/components/DashboardChart | src/features/dashboard/components/Chart | Dashboard.tsx |
```

---

## PHASE 3: EXECUTE

### One File At A Time

```markdown
### Step 1: Move Dashboard.tsx

1. **Create destination:** mkdir -p src/features/dashboard
2. **Move file:** mv src/components/Dashboard.tsx src/features/dashboard/
3. **Update imports in:**
   - src/pages/Home.tsx: change '../components/Dashboard' → '@/features/dashboard'
   - src/pages/Admin.tsx: change '../components/Dashboard' → '@/features/dashboard'
   - src/layouts/Main.tsx: change '../../components/Dashboard' → '@/features/dashboard'
4. **Create barrel:** Add export to src/features/dashboard/index.ts
5. **Verify:** npm run build

### Step 2: Move DashboardChart.tsx
...
```

### Atomic Updates

```typescript
// BEFORE moving file - these imports exist:
import { Dashboard } from '../components/Dashboard';  // Home.tsx
import { Dashboard } from '../components/Dashboard';  // Admin.tsx
import { Dashboard } from '../../components/Dashboard';  // Main.tsx

// AFTER moving + updating ALL at once:
import { Dashboard } from '@/features/dashboard';  // Home.tsx ✓
import { Dashboard } from '@/features/dashboard';  // Admin.tsx ✓
import { Dashboard } from '@/features/dashboard';  // Main.tsx ✓
```

---

## PHASE 4: VERIFY

### Build Check

```bash
# Must pass before moving to next file
npm run build
npm run typecheck
```

### Import Verification

```bash
# Search for any remaining old imports
grep -r "from.*components/Dashboard" --include="*.tsx" src/
# Should return: nothing

# Search for any broken imports
npm run build 2>&1 | grep "Cannot find module"
# Should return: nothing
```

### Checklist

- [ ] All files moved to new locations
- [ ] All imports updated (grep confirms no old paths)
- [ ] Build passes
- [ ] Type check passes
- [ ] No @ts-ignore added
- [ ] Barrel exports created for feature directories

---

## COMPONENT SIZE GUIDELINES

| Metric | Threshold | Action |
|--------|-----------|--------|
| Lines of code | > 300 | Extract sub-components |
| Number of props | > 8 | Consider composition |
| Nesting depth | > 5 | Flatten structure |
| useEffect hooks | > 3 | Extract to custom hook |
| Repeated JSX | 2+ times | Extract component |

### Extraction Example

```tsx
// BEFORE: 800-line Dashboard.tsx
function Dashboard() {
  // 200 lines of hooks and state
  // 600 lines of JSX with metrics, charts, activity
}

// AFTER: Split into focused components
function Dashboard() {
  return (
    <DashboardLayout>
      <DashboardHeader />
      <MetricsGrid />
      <ChartsSection />
      <RecentActivity />
    </DashboardLayout>
  );
}
// Dashboard.tsx is now 50 lines
// Each sub-component is 100-150 lines
```

---

## ENFORCEMENT

This skill is MANDATORY for refactoring:

- **FORBIDDEN**: Moving files without tracking imports
- **FORBIDDEN**: Moving multiple files at once
- **FORBIDDEN**: Leaving broken imports "for later"
- **REQUIRED**: Document all importers before moving
- **REQUIRED**: One file at a time
- **REQUIRED**: Verify build after each move
- **REQUIRED**: Update ALL imports immediately

**If you move a file and break the build, you haven't refactored - you've damaged the codebase.**

---

## Related Skills

- **writing-plans** - Plan large refactoring efforts
- **executing-plans** - Execute refactoring systematically
- **verification-before-completion** - Verify after refactoring
