---
name: backend-dev-guidelines
description: Use when creating ANY backend code - routes, controllers, services, repositories, middleware, Express APIs, Prisma queries, or Node.js/TypeScript server code. MANDATORY for all backend development. FORBIDDEN patterns include business logic in routes, direct process.env usage, missing error handling. REQUIRED patterns are layered architecture, BaseController, Zod validation, Sentry error tracking, unifiedConfig.
---

# Backend Development Guidelines

## THE MANDATE

This skill is **MANDATORY** for any backend code. If you write Node.js/Express/TypeScript without following these guidelines, your code will be rejected.

---

## FORBIDDEN PATTERNS (Never Generate These)

### ❌ Business Logic in Routes - BANNED

```typescript
// ❌ FORBIDDEN - Logic in route
router.post('/submit', async (req, res) => {
    const user = await prisma.user.findUnique({ where: { id: req.body.userId } });
    const validated = schema.parse(req.body);
    await prisma.submission.create({ data: validated });
    await sendEmail(user.email, 'Submitted!');
    res.json({ success: true });
});

// ✅ REQUIRED - Delegate to controller
router.post('/submit', (req, res) => controller.submit(req, res));
```

**If you put business logic in a route file, you have failed.**

### ❌ Direct process.env Usage - BANNED

```typescript
// ❌ FORBIDDEN
const timeout = process.env.TIMEOUT_MS;
const dbUrl = process.env.DATABASE_URL;
if (process.env.NODE_ENV === 'production') { }

// ✅ REQUIRED - Use unifiedConfig
import { config } from './config/unifiedConfig';
const timeout = config.timeouts.default;
const dbUrl = config.database.url;
if (config.isProduction) { }
```

**If you use `process.env` directly, you have failed.**

### ❌ Missing Error Handling - BANNED

```typescript
// ❌ FORBIDDEN - No error handling
async function getData() {
    const result = await prisma.user.findMany();
    return result;
}

// ❌ FORBIDDEN - console.error without Sentry
catch (error) {
    console.error('Error:', error);
    throw error;
}

// ✅ REQUIRED - Always capture to Sentry
import * as Sentry from '@sentry/node';

catch (error) {
    Sentry.captureException(error);
    throw error;
}
```

**If you have a catch block without Sentry.captureException, you have failed.**

### ❌ Other Forbidden Patterns

```typescript
// ❌ FORBIDDEN
console.log('Debug:', data);           // Use proper logging
res.send(result);                       // Use res.json()
throw new Error('Something failed');   // Use custom error classes
await prisma.user.findMany();          // Use repository pattern for complex queries
```

---

## REQUIRED PATTERNS (Always Use These)

### ✅ Layered Architecture

```
HTTP Request
    ↓
Routes (routing ONLY - no logic)
    ↓
Controllers (extend BaseController)
    ↓
Services (business logic)
    ↓
Repositories (data access)
    ↓
Database (Prisma)
```

**Each layer has ONE responsibility. Violating this structure is forbidden.**

### ✅ Route Definition

```typescript
// routes/userRoutes.ts
import { Router } from 'express';
import { userController } from '../controllers/UserController';
import { asyncErrorWrapper } from '../middleware/errorBoundary';
import { validateBody } from '../middleware/validation';
import { createUserSchema } from '../validators/userSchemas';

const router = Router();

// REQUIRED: Routes only route - no logic
router.get('/:id', asyncErrorWrapper((req, res) => userController.getById(req, res)));
router.post('/', validateBody(createUserSchema), asyncErrorWrapper((req, res) => userController.create(req, res)));

export default router;
```

### ✅ Controller Pattern (BaseController)

```typescript
// controllers/UserController.ts
import { Request, Response } from 'express';
import { BaseController } from './BaseController';
import { userService } from '../services/userService';
import * as Sentry from '@sentry/node';

export class UserController extends BaseController {
    async getById(req: Request, res: Response): Promise<void> {
        try {
            const user = await userService.findById(req.params.id);
            this.handleSuccess(res, user);
        } catch (error) {
            this.handleError(error, res, 'getById');
        }
    }

    async create(req: Request, res: Response): Promise<void> {
        try {
            const user = await userService.create(req.body);
            this.handleSuccess(res, user, 201);
        } catch (error) {
            this.handleError(error, res, 'create');
        }
    }
}

export const userController = new UserController();
```

### ✅ Service Pattern

```typescript
// services/userService.ts
import { UserRepository } from '../repositories/UserRepository';
import * as Sentry from '@sentry/node';

class UserService {
    constructor(private userRepo: UserRepository) {}

    async findById(id: string) {
        return await this.userRepo.findById(id);
    }

    async create(data: CreateUserDto) {
        // Business logic goes HERE
        const validated = this.validateBusinessRules(data);
        return await this.userRepo.create(validated);
    }
}

export const userService = new UserService(new UserRepository());
```

### ✅ Repository Pattern

```typescript
// repositories/UserRepository.ts
import { PrismaService } from '../utils/PrismaService';
import * as Sentry from '@sentry/node';

export class UserRepository {
    async findById(id: string) {
        try {
            return await PrismaService.main.user.findUnique({
                where: { id },
            });
        } catch (error) {
            Sentry.captureException(error);
            throw error;
        }
    }

    async create(data: CreateUserData) {
        try {
            return await PrismaService.main.user.create({ data });
        } catch (error) {
            Sentry.captureException(error);
            throw error;
        }
    }
}
```

### ✅ Zod Validation

```typescript
// validators/userSchemas.ts
import { z } from 'zod';

export const createUserSchema = z.object({
    email: z.string().email(),
    name: z.string().min(1).max(100),
    role: z.enum(['admin', 'user']).default('user'),
});

export type CreateUserDto = z.infer<typeof createUserSchema>;

// Usage in middleware
const validated = createUserSchema.parse(req.body);
```

### ✅ Error Handling with Sentry

```typescript
// REQUIRED: Every catch block must have Sentry
import * as Sentry from '@sentry/node';

try {
    await operation();
} catch (error) {
    Sentry.captureException(error, {
        tags: { 
            service: 'user-service',
            operation: 'create',
        },
        extra: { userId: req.user?.id },
    });
    throw error;
}
```

---

## Directory Structure

```
service/src/
├── config/              # unifiedConfig (REQUIRED)
├── controllers/         # Extend BaseController (REQUIRED)
├── services/            # Business logic (REQUIRED)
├── repositories/        # Data access (REQUIRED for complex queries)
├── routes/              # Route definitions (REQUIRED)
├── middleware/          # Express middleware
├── validators/          # Zod schemas (REQUIRED)
├── types/               # TypeScript types
├── utils/               # Utilities
├── instrument.ts        # Sentry - MUST BE FIRST IMPORT
├── app.ts               # Express setup
└── server.ts            # HTTP server
```

---

## Checklists

### New Route Checklist

- [ ] Route file only contains route definitions
- [ ] All routes delegate to controller methods
- [ ] Validation middleware with Zod schema
- [ ] asyncErrorWrapper on all async routes
- [ ] No business logic in route file

### New Controller Checklist

- [ ] Extends BaseController
- [ ] Uses try/catch in all methods
- [ ] Calls this.handleError in catch blocks
- [ ] Delegates to service for business logic
- [ ] No direct Prisma calls

### New Service Checklist

- [ ] Contains business logic
- [ ] Uses repository for data access
- [ ] Has Sentry.captureException in catch blocks
- [ ] Uses dependency injection pattern
- [ ] No req/res objects

---

## Quick Reference

| Layer | Responsibility | Contains |
|-------|----------------|----------|
| Routes | URL mapping | Route definitions ONLY |
| Controllers | Request handling | Validation, delegation |
| Services | Business logic | Rules, orchestration |
| Repositories | Data access | Prisma queries |

| HTTP Status | Use Case |
|-------------|----------|
| 200 | Success |
| 201 | Created |
| 400 | Bad Request (validation) |
| 401 | Unauthorized |
| 403 | Forbidden |
| 404 | Not Found |
| 500 | Server Error |

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
- **frontend-dev-guidelines** - For frontend that consumes these APIs
- **route-tester** - For testing the routes you create
- **test-driven-development** - For implementing features
