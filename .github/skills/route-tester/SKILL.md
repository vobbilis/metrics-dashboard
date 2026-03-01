---
name: route-tester
description: Use when testing ANY API endpoint, debugging authentication issues (401/403 errors, cookie problems, JWT issues), validating route functionality, verifying request/response data, or when routes return 'not found' despite being defined. MANDATORY before marking any route work as complete. Includes debugging workflow, PM2 log inspection, route registration checks, and curl command generation.
---

# Route Testing

## THE MANDATE

**Every route MUST be tested before work is complete.** Don't assume a route works - verify it.

---

## Testing Methods

### Method 1: test-auth-route.js (RECOMMENDED)

The script handles all authentication complexity automatically.

**Location:** `/root/git/your project_pre/scripts/test-auth-route.js`

```bash
# GET request
node scripts/test-auth-route.js http://localhost:3000/blog-api/api/endpoint

# POST request with JSON
node scripts/test-auth-route.js \
    http://localhost:3000/blog-api/777/submit \
    POST \
    '{"responses":{"4577":"13295"},"submissionID":5}'

# PUT request
node scripts/test-auth-route.js \
    http://localhost:3000/blog-api/users/123 \
    PUT \
    '{"name":"Updated Name"}'
```

**What it does:**
1. Gets refresh token from Keycloak
2. Signs token with JWT secret
3. Creates cookie header
4. Makes authenticated request
5. Shows curl command for manual reproduction

### Method 2: Mock Authentication (Development)

For local development - bypasses Keycloak entirely.

**Setup (.env):**
```bash
MOCK_AUTH=true
MOCK_USER_ID=test-user
MOCK_USER_ROLES=admin,operations
```

**Usage:**
```bash
curl -H "X-Mock-Auth: true" \
     -H "X-Mock-User: test-user" \
     -H "X-Mock-Roles: admin,operations" \
     http://localhost:3002/api/protected
```

**Requirements:**
- `NODE_ENV` must be `development` or `test`
- `mockAuth` middleware must be enabled
- NEVER works in production

### Method 3: Manual curl

Copy the curl command from test-auth-route.js output:

```bash
curl -X POST http://localhost:3000/blog-api/777/submit \
  -H "Content-Type: application/json" \
  -b "refresh_token=<TOKEN_FROM_SCRIPT>" \
  -d '{"your": "data"}'
```

---

## Service Ports

| Service | Port | Base URL |
|---------|------|----------|
| Users | 3000 | http://localhost:3000 |
| Projects | 3001 | http://localhost:3001 |
| Form | 3002 | http://localhost:3002 |
| Email | 3003 | http://localhost:3003 |
| Uploads | 5000 | http://localhost:5000 |

---

## Common Testing Patterns

### Test Form Submission

```bash
node scripts/test-auth-route.js \
    http://localhost:3000/blog-api/777/submit \
    POST \
    '{"responses":{"4577":"13295"},"submissionID":5,"stepInstanceId":"11"}'
```

### Test Workflow Start

```bash
node scripts/test-auth-route.js \
    http://localhost:3002/api/workflow/start \
    POST \
    '{"workflowCode":"DHS_CLOSEOUT","entityType":"Submission","entityID":123}'
```

### Test GET with Query Params

```bash
node scripts/test-auth-route.js \
    "http://localhost:3002/api/workflows?status=active&limit=10"
```

### Test File Upload

```bash
# Get token first, then:
curl -X POST http://localhost:5000/upload \
  -H "Content-Type: multipart/form-data" \
  -b "refresh_token=<TOKEN>" \
  -F "file=@/path/to/file.pdf"
```

---

## Route URL Construction

**Full URL = Base URL + Prefix + Route Path**

Check `/src/app.ts` for prefixes:

```typescript
// Example from blog-api/src/app.ts
app.use('/blog-api/api', formRoutes);      // Prefix: /blog-api/api
app.use('/api/workflow', workflowRoutes);  // Prefix: /api/workflow
```

**Example:**
- Base: `http://localhost:3002`
- Prefix: `/form`
- Route: `/777/submit`
- **Full:** `http://localhost:3000/blog-api/777/submit`

---

## Testing Checklist

### Before Testing

- [ ] Service is running (`npm run dev`)
- [ ] Database is accessible
- [ ] Mock auth enabled (if using Method 2)
- [ ] Correct port identified

### After Route Implementation

- [ ] Test happy path (valid request)
- [ ] Test validation errors (invalid data)
- [ ] Test auth errors (no token)
- [ ] Test not found (invalid ID)
- [ ] Document curl command that works

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| 401 Unauthorized | Check token, try mock auth |
| 404 Not Found | Verify full URL with prefix |
| 500 Error | Check service logs |
| Connection refused | Service not running |

---

## DEBUGGING WORKFLOW

When a route doesn't work, follow this systematic process:

### Step 1: Check Service Logs (PM2)

```bash
# Real-time monitoring
pm2 logs form          # or users, email, projects

# Recent errors with more context
pm2 logs form --lines 200

# Error-specific log files
tail -f form/logs/form-error.log

# Check service status
pm2 list
```

### Step 2: Route Registration Checks

Routes can fail silently if registration is wrong:

```typescript
// In app.ts - Check registration ORDER matters!
app.use('/api/:id', genericHandler);    // ❌ This catches everything!
app.use('/api/specific', specificHandler); // Never reached

// Correct order:
app.use('/api/specific', specificHandler); // ✅ Specific first
app.use('/api/:id', genericHandler);       // Generic last
```

**Common registration issues:**
- Route registered AFTER a catch-all route
- Typo in route path or HTTP method
- Missing router export/import
- Middleware blocking before route

### Step 3: Authentication Debugging

```bash
# Test WITHOUT auth to isolate the issue
node scripts/test-auth-route.js http://localhost:3002/api/endpoint --no-auth

# If works without auth but fails with auth:
# - Check cookie configuration (httpOnly, secure, sameSite)
# - Verify JWT secret in config
# - Check token expiration
# - Verify role/permission requirements
```

### Step 4: Common Issues Checklist

| Error | Likely Cause | Fix |
|-------|--------------|-----|
| 404 despite route exists | Wrong prefix or registration order | Check app.ts, fix order |
| 401 on valid token | Token expired or wrong secret | Check Keycloak lifetime, verify secret |
| 403 on authenticated user | Missing role/permission | Check middleware requirements |
| 500 on POST/PUT | Validation or DB error | Check logs, verify payload |

---

## Enforcement

**Every route task MUST include:**
1. The test command used
2. The response received
3. Confirmation it works

Don't say "route created" without testing it.
