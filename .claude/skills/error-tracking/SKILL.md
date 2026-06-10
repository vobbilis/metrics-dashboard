---
name: error-tracking
description: Use when writing ANY error handling, catch blocks, try/catch, async operations, controllers, or cron jobs. MANDATORY for all code that can fail. FORBIDDEN patterns include console.error without Sentry, catch blocks without Sentry.captureException, unhandled promise rejections. REQUIRED patterns are Sentry v8 integration, WorkflowSentryHelper, proper error context and tags.
---

# Error Tracking with Sentry

## THE MANDATE

**ALL ERRORS MUST BE CAPTURED TO SENTRY. No exceptions. Ever.**

If you write a catch block without `Sentry.captureException`, you have failed. If you use `console.error` alone, you have failed.

---

## FORBIDDEN PATTERNS (Never Generate These)

### ❌ console.error Without Sentry - BANNED

```typescript
// ❌ FORBIDDEN - console.error alone
catch (error) {
    console.error('Error:', error);
    throw error;
}

// ❌ FORBIDDEN - logging without Sentry
catch (error) {
    logger.error('Failed:', error);
    return null;
}

// ✅ REQUIRED - Always Sentry first
catch (error) {
    Sentry.captureException(error);
    console.error('Error:', error); // OK as secondary
    throw error;
}
```

**Every catch block MUST have Sentry.captureException.**

### ❌ Catch Without Sentry - BANNED

```typescript
// ❌ FORBIDDEN - Swallowing errors
try {
    await operation();
} catch (error) {
    // Silently ignored - NEVER DO THIS
}

// ❌ FORBIDDEN - Catch without Sentry
try {
    await operation();
} catch (error) {
    throw new Error('Operation failed');
}

// ✅ REQUIRED
try {
    await operation();
} catch (error) {
    Sentry.captureException(error);
    throw error;
}
```

### ❌ Uncontextualized Errors - BANNED

```typescript
// ❌ FORBIDDEN - No context
Sentry.captureException(error);

// ✅ REQUIRED - With context
Sentry.captureException(error, {
    tags: { 
        service: 'user-service',
        operation: 'create',
    },
    extra: { 
        userId: user.id,
        requestId: req.id,
    },
});
```

---

## REQUIRED PATTERNS (Always Use These)

### ✅ BaseController Error Handling

```typescript
import { BaseController } from '../controllers/BaseController';

export class MyController extends BaseController {
    async myMethod(req: Request, res: Response) {
        try {
            const result = await this.service.doSomething();
            this.handleSuccess(res, result);
        } catch (error) {
            // handleError automatically sends to Sentry
            this.handleError(error, res, 'myMethod');
        }
    }
}
```

### ✅ Route Error Handling (Without BaseController)

```typescript
import * as Sentry from '@sentry/node';

router.get('/route', async (req, res) => {
    try {
        const result = await service.getData();
        res.json(result);
    } catch (error) {
        Sentry.captureException(error, {
            tags: { 
                route: '/route', 
                method: 'GET',
                service: 'my-service',
            },
            extra: { 
                userId: req.user?.id,
                query: req.query,
            },
        });
        res.status(500).json({ error: 'Internal server error' });
    }
});
```

### ✅ Service/Repository Error Handling

```typescript
import * as Sentry from '@sentry/node';

class UserService {
    async findById(id: string) {
        try {
            return await this.repo.findById(id);
        } catch (error) {
            Sentry.captureException(error, {
                tags: { 
                    service: 'UserService',
                    method: 'findById',
                },
                extra: { userId: id },
            });
            throw error; // Re-throw after capturing
        }
    }
}
```

### ✅ Workflow Error Handling

```typescript
import { WorkflowSentryHelper } from '../workflow/utils/sentryHelper';

// For workflow-specific errors - REQUIRED
WorkflowSentryHelper.captureWorkflowError(error, {
    workflowCode: 'DHS_CLOSEOUT',
    instanceId: 123,
    stepId: 456,
    userId: 'user-123',
    operation: 'stepCompletion',
    metadata: { additionalInfo: 'value' },
});
```

### ✅ Cron Job Pattern (MANDATORY)

```typescript
#!/usr/bin/env node
// FIRST LINE after shebang - CRITICAL!
import '../instrument';
import * as Sentry from '@sentry/node';

async function main() {
    return await Sentry.startSpan({
        name: 'cron.job-name',
        op: 'cron',
        attributes: {
            'cron.job': 'job-name',
            'cron.startTime': new Date().toISOString(),
        },
    }, async () => {
        try {
            // Job logic here
            await processItems();
        } catch (error) {
            Sentry.captureException(error, {
                tags: {
                    'cron.job': 'job-name',
                    'error.type': 'execution_error',
                },
            });
            console.error('[Job] Error:', error);
            process.exit(1);
        }
    });
}

main()
    .then(() => {
        console.log('[Job] Completed successfully');
        process.exit(0);
    })
    .catch((error) => {
        Sentry.captureException(error);
        console.error('[Job] Fatal error:', error);
        process.exit(1);
    });
```

### ✅ Database Performance Monitoring

```typescript
import { DatabasePerformanceMonitor } from '../utils/databasePerformance';

// Wrap database operations for performance tracking
const result = await DatabasePerformanceMonitor.withPerformanceTracking(
    'findMany',
    'UserProfile',
    async () => {
        return await PrismaService.main.userProfile.findMany({
            take: 5,
        });
    }
);
```

### ✅ Async Operations with Spans

```typescript
import * as Sentry from '@sentry/node';

const result = await Sentry.startSpan({
    name: 'external-api.call',
    op: 'http.client',
    attributes: {
        'http.url': 'https://api.example.com',
        'http.method': 'POST',
    },
}, async () => {
    return await fetch('https://api.example.com/endpoint');
});
```

---

## Error Severity Levels

Use appropriate severity:

| Level | Use When |
|-------|----------|
| **fatal** | System unusable (database down, critical failure) |
| **error** | Operation failed, needs immediate attention |
| **warning** | Recoverable issues, degraded performance |
| **info** | Informational, successful operations |
| **debug** | Development only, detailed info |

```typescript
Sentry.captureException(error, { level: 'fatal' });
Sentry.captureMessage('Degraded performance', { level: 'warning' });
```

---

## Context Requirements

Every Sentry call MUST include:

```typescript
Sentry.captureException(error, {
    // REQUIRED tags
    tags: {
        service: 'service-name',      // Which microservice
        operation: 'method-name',      // What operation
    },
    // REQUIRED extra context
    extra: {
        userId: user?.id,              // Who was affected
        // Operation-specific data
    },
});
```

---

## Checklist

### Every Catch Block

- [ ] Has `Sentry.captureException(error)`
- [ ] Has `tags: { service, operation }`
- [ ] Has relevant `extra` context
- [ ] Re-throws or handles the error appropriately

### Every Cron Job

- [ ] `import '../instrument'` is FIRST LINE
- [ ] Wrapped in `Sentry.startSpan`
- [ ] Has cron-specific tags
- [ ] Handles exit codes properly

### Every Controller

- [ ] Extends BaseController OR
- [ ] Has manual Sentry.captureException in catch

---

## Enforcement

This skill uses MANDATORY language:

- **FORBIDDEN** = Never generate this code
- **REQUIRED** = Always use this pattern
- **MUST** = No exceptions

**Code with catch blocks missing Sentry will be rejected.**

---

## Related Skills

- **backend-dev-guidelines** - Uses these error patterns
- **frontend-dev-guidelines** - Frontend error handling patterns
