---
name: frontend-dev-guidelines
description: Use when creating ANY React component, UI element, button, form, modal, page, or styled element. MANDATORY for all frontend/TypeScript/TSX code. FORBIDDEN patterns include inline styles (style={{}}), early loading returns, old MUI Grid syntax. REQUIRED patterns are MUI sx prop, SuspenseLoader, useSuspenseQuery, feature directory structure.
---

# Frontend Development Guidelines

## THE MANDATE

This skill is **MANDATORY** for any frontend code. If you write React/TypeScript without following these guidelines, your code will be rejected.

---

## FORBIDDEN PATTERNS (Never Generate These)

### ❌ Inline Styles - ABSOLUTELY BANNED

```typescript
// ❌ FORBIDDEN - Never generate this
<button style={{ backgroundColor: 'red' }}>Click</button>
<div style="color: blue;">Text</div>
<Box style={{ padding: 10 }}>Content</Box>

// ✅ REQUIRED - Always use sx prop
<Button sx={{ backgroundColor: 'red' }}>Click</Button>
<Box sx={{ color: 'blue' }}>Text</Box>
<Box sx={{ p: 2 }}>Content</Box>
```

**If you generate `style={{` or `style="`, you have failed.**

### ❌ Early Loading Returns - BANNED

```typescript
// ❌ FORBIDDEN - Causes layout shift
if (isLoading) {
    return <LoadingSpinner />;
}
if (isLoading) return <CircularProgress />;

// ✅ REQUIRED - Use SuspenseLoader
<SuspenseLoader>
    <Content />
</SuspenseLoader>
```

**If you generate `if (isLoading) return`, you have failed.**

### ❌ Old MUI Grid Syntax - BANNED

```typescript
// ❌ FORBIDDEN - MUI v6 syntax
<Grid xs={12} md={6}>
<Grid item xs={12}>

// ✅ REQUIRED - MUI v7 syntax
<Grid size={{ xs: 12, md: 6 }}>
```

### ❌ Other Forbidden Patterns

```typescript
// ❌ FORBIDDEN
import { makeStyles } from '@material-ui/core';  // Old MUI
import { toast } from 'react-toastify';          // Wrong toast library
const [loading, setLoading] = useState(true);    // Manual loading state
```

---

## REQUIRED PATTERNS (Always Use These)

### ✅ Component Structure

```typescript
import React, { useState, useCallback } from 'react';
import { Box, Paper, Button } from '@mui/material';
import type { SxProps, Theme } from '@mui/material';
import { useSuspenseQuery } from '@tanstack/react-query';
import { SuspenseLoader } from '~components/SuspenseLoader';
import type { MyData } from '~types/myData';

interface MyComponentProps {
    id: number;
    onAction?: () => void;
}

const styles: Record<string, SxProps<Theme>> = {
    container: { p: 2 },
    button: { 
        backgroundColor: 'primary.main',
        '&:hover': { backgroundColor: 'primary.dark' },
    },
};

export const MyComponent: React.FC<MyComponentProps> = ({ id, onAction }) => {
    const [state, setState] = useState<string>('');

    const { data } = useSuspenseQuery({
        queryKey: ['myData', id],
        queryFn: () => api.getData(id),
    });

    const handleClick = useCallback(() => {
        onAction?.();
    }, [onAction]);

    return (
        <Box sx={styles.container}>
            <Button sx={styles.button} onClick={handleClick}>
                Click Me
            </Button>
        </Box>
    );
};

export default MyComponent;
```

### ✅ Styling with sx Prop

```typescript
import type { SxProps, Theme } from '@mui/material';

// For <100 lines of styles - inline object
const styles: Record<string, SxProps<Theme>> = {
    container: {
        p: 2,
        backgroundColor: 'background.paper',
    },
    title: {
        color: 'text.primary',
        fontSize: '1.5rem',
    },
    button: (theme) => ({
        backgroundColor: theme.palette.primary.main,
        '&:hover': {
            backgroundColor: theme.palette.primary.dark,
        },
    }),
};

// Usage
<Box sx={styles.container}>
    <Typography sx={styles.title}>Title</Typography>
    <Button sx={styles.button}>Click</Button>
</Box>
```

### ✅ Data Fetching with useSuspenseQuery

```typescript
import { useSuspenseQuery } from '@tanstack/react-query';
import { SuspenseLoader } from '~components/SuspenseLoader';

// In parent component - wrap with SuspenseLoader
<SuspenseLoader>
    <DataComponent id={123} />
</SuspenseLoader>

// In DataComponent - use useSuspenseQuery
const { data } = useSuspenseQuery({
    queryKey: ['entity', id],
    queryFn: () => entityApi.getById(id),
});
// No loading check needed - Suspense handles it
```

### ✅ Feature Directory Structure

```
features/
  my-feature/
    api/
      myFeatureApi.ts       # REQUIRED: API service layer
    components/
      MyFeature.tsx         # Main component
      SubComponent.tsx      # Related components
    hooks/
      useMyFeature.ts       # Custom hooks
    helpers/
      myFeatureHelpers.ts   # Utility functions
    types/
      index.ts              # TypeScript types
    index.ts                # Public exports
```

### ✅ Import Aliases

```typescript
// REQUIRED - Use these aliases
import { apiClient } from '@/lib/apiClient';
import type { User } from '~types/user';
import { SuspenseLoader } from '~components/SuspenseLoader';
import { authApi } from '~features/auth';

// FORBIDDEN - Relative imports for these paths
import { User } from '../../../types/user';  // ❌
```

### ✅ Notifications

```typescript
// REQUIRED - Use useMuiSnackbar
import { useMuiSnackbar } from '@/hooks/useMuiSnackbar';

const { showSuccess, showError } = useMuiSnackbar();
showSuccess('Item created successfully');
showError('Failed to create item');

// FORBIDDEN - react-toastify
import { toast } from 'react-toastify';  // ❌ NEVER
```

---

## Checklists

### New Component Checklist

- [ ] Use `React.FC<Props>` with TypeScript interface
- [ ] Use `useSuspenseQuery` for data (NOT useState + useEffect)
- [ ] Wrap in `<SuspenseLoader>` at parent level
- [ ] Use `sx` prop for ALL styling (NO style={{}})
- [ ] Use import aliases (`@/`, `~types`, `~components`)
- [ ] Use `useCallback` for handlers passed to children
- [ ] Use `useMuiSnackbar` for notifications
- [ ] Lazy load if heavy: `React.lazy(() => import())`
- [ ] Default export at bottom

### New Feature Checklist

- [ ] Create `features/{name}/` directory
- [ ] Create subdirs: `api/`, `components/`, `hooks/`, `types/`
- [ ] Create API service: `api/{name}Api.ts`
- [ ] Create types in `types/index.ts`
- [ ] Create route: `routes/{name}/index.tsx`
- [ ] Lazy load main component
- [ ] Export public API from `index.ts`

---

## Quick Reference

| Need to... | Pattern |
|------------|---------|
| Style a component | `sx={{ color: 'red' }}` or `sx={styles.name}` |
| Fetch data | `useSuspenseQuery` + `<SuspenseLoader>` |
| Show notification | `useMuiSnackbar().showSuccess()` |
| Create feature | `features/{name}/api,components,hooks,types/` |
| Use Grid | `<Grid size={{ xs: 12, md: 6 }}>` |
| Import types | `import type { X } from '~types/x'` |

---

## Enforcement

This skill uses MANDATORY language:

- **FORBIDDEN** = Never generate this code
- **REQUIRED** = Always use this pattern
- **BANNED** = Absolute prohibition

**Code that contains FORBIDDEN patterns will be rejected.**

---

## Related Skills

- **error-tracking** - MUST use for all error handling
- **backend-dev-guidelines** - For API routes frontend consumes
- **test-driven-development** - For implementing features
