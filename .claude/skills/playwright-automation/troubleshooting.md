# Playwright Troubleshooting Guide

Quick reference for diagnosing and fixing common Playwright issues in React micro frontend testing.

---

## Flaky Test Diagnosis

### Decision Tree

```
Test fails intermittently?
│
├─► Does it fail locally?
│   ├─► YES → Likely timing/race condition issue
│   └─► NO, only in CI → Environment difference or resource constraint
│
├─► Does it fail on specific browser?
│   ├─► Chrome only → Check Chrome DevTools Protocol specific behavior
│   ├─► Firefox only → Check Firefox-specific CSS/JS behavior
│   └─► All browsers → Likely application or test logic issue
│
├─► Does it fail when run in parallel?
│   ├─► YES → Test state isolation issue
│   └─► NO → Likely test-specific timing issue
│
└─► Does it fail on specific viewport size?
    ├─► YES → Responsive design or mobile interaction issue
    └─► NO → Proceed to timing analysis
```

---

## Common Issues & Solutions

### 1. Element Not Found / Timeout

**Symptom:**
```
Error: locator.click: Timeout 30000ms exceeded.
=========================== logs ===========================
waiting for getByTestId('button')
============================================================
```

**Diagnosis:**
```typescript
// Add debugging
console.log('Looking for button...');
const exists = await page.getByTestId('button').count();
console.log(`Found ${exists} elements`);

// Screenshot to see current state
await page.screenshot({ path: 'debug-before-click.png' });
```

**Solutions:**

| Cause | Solution |
|-------|----------|
| Element not rendered yet | Add explicit wait for page state |
| Wrong testId | Verify testId in browser DevTools |
| Element in iframe | Use `frame.getByTestId()` |
| Element in Shadow DOM | Use piercing selector `>>` |
| Element conditionally rendered | Check business logic |

```typescript
// ✅ Wait for specific application state first
await expect(page.getByTestId('page-loaded-indicator')).toBeVisible();
await page.getByTestId('button').click();
```

---

### 2. Element Not Visible

**Symptom:**
```
Error: locator.click: Element is not visible
```

**Diagnosis:**
```typescript
const element = page.getByTestId('button');
const box = await element.boundingBox();
console.log('Bounding box:', box); // null if not visible

const isVisible = await element.isVisible();
console.log('Is visible:', isVisible);
```

**Solutions:**

| Cause | Solution |
|-------|----------|
| Behind modal/overlay | Close modal first |
| Scrolled out of view | Let Playwright auto-scroll or manual scroll |
| `display: none` | Wait for element to become visible |
| Zero dimensions | Check CSS, may be collapsed |
| Outside viewport | Set larger viewport size |

```typescript
// ✅ Wait for visibility explicitly
await expect(page.getByTestId('button')).toBeVisible();
await page.getByTestId('button').click();
```

---

### 3. Stale Element / Detached from DOM

**Symptom:**
```
Error: locator.click: Element is detached from the DOM
```

**Cause:** React re-rendered the component between finding and clicking.

**Solution:**
```typescript
// ❌ Don't store locator and use later
const button = page.getByTestId('button');
await page.getByTestId('trigger').click(); // Causes re-render
await button.click(); // Stale!

// ✅ Use fresh locator or wait for stable state
await page.getByTestId('trigger').click();
await expect(page.getByTestId('new-state')).toBeVisible();
await page.getByTestId('button').click();
```

---

### 4. Click Intercepted

**Symptom:**
```
Error: locator.click: Element click intercepted
```

**Cause:** Another element is covering the target element.

**Diagnosis:**
```typescript
await page.screenshot({ path: 'click-intercepted.png' });

// Check what's covering it
const overlays = await page.evaluate(() => {
  const target = document.querySelector('[data-testid="button"]');
  const rect = target?.getBoundingClientRect();
  if (!rect) return null;
  return document.elementFromPoint(rect.x + rect.width/2, rect.y + rect.height/2);
});
console.log('Covering element:', overlays);
```

**Solutions:**

| Cause | Solution |
|-------|----------|
| Loading overlay | Wait for loading to complete |
| Modal backdrop | Close modal |
| Tooltip/dropdown | Wait for animation, or click { force: true } |
| Fixed header/footer | Scroll element into view |

```typescript
// ✅ Wait for overlay to disappear
await expect(page.getByTestId('loading-overlay')).not.toBeVisible();
await page.getByTestId('button').click();

// ✅ Or force click (use sparingly)
await page.getByTestId('button').click({ force: true });
```

---

### 5. Assertion Timeout

**Symptom:**
```
Error: expect(locator).toHaveText: Timeout 5000ms exceeded.
Expected: "Expected Text"
Received: "Loading..."
```

**Cause:** Application state hasn't updated yet.

**Solution:**
```typescript
// ❌ Asserting too early
await page.getByTestId('submit').click();
await expect(page.getByTestId('result')).toHaveText('Success');

// ✅ Wait for network or state change
await Promise.all([
  page.waitForResponse(resp => resp.url().includes('/api/submit')),
  page.getByTestId('submit').click()
]);
await expect(page.getByTestId('result')).toHaveText('Success');
```

---

### 6. Test Works Locally, Fails in CI

**Common Causes & Solutions:**

| Cause | Diagnosis | Solution |
|-------|-----------|----------|
| Slower CI machines | Add explicit waits | Use assertions, not waitForTimeout |
| Missing fonts | Text rendering different | Install fonts in CI or use screenshot masking |
| Different screen size | Responsive breakpoints | Set explicit viewport in config |
| Network timing | API responses slower | Mock APIs or wait for network |
| Timezone differences | Date/time displays | Mock dates or use relative assertions |
| Missing env vars | Undefined config | Check CI secrets configuration |

```typescript
// playwright.config.ts - CI-specific settings
export default defineConfig({
  timeout: process.env.CI ? 60000 : 30000,
  expect: {
    timeout: process.env.CI ? 10000 : 5000,
  },
  retries: process.env.CI ? 2 : 0,
});
```

---

### 7. Tests Fail When Run in Parallel

**Cause:** Tests share state (database, cookies, localStorage).

**Diagnosis:**
```bash
# Run sequentially to confirm
npx playwright test --workers=1
```

**Solutions:**

```typescript
// ✅ Isolate test data per worker
test.beforeEach(async ({ page }, testInfo) => {
  const uniqueId = `${testInfo.workerIndex}-${Date.now()}`;
  // Use uniqueId for test data
});

// ✅ Use unique users per test
const testUser = {
  email: `test-${Date.now()}@example.com`,
  // ...
};
```

---

### 8. Fill/Type Not Working

**Symptom:** Input remains empty or has wrong value.

**Diagnosis:**
```typescript
const input = page.getByTestId('input');
await input.fill('test');
const value = await input.inputValue();
console.log('Actual value:', value);
```

**Solutions:**

| Cause | Solution |
|-------|----------|
| Controlled input with validation | Use `type()` instead of `fill()` |
| Input masked/formatted | Fill unformatted value |
| Readonly/disabled | Wait for enabled state |
| Hidden input (file) | Use `setInputFiles()` |

```typescript
// ✅ For complex inputs, use type() with delays
await page.getByTestId('phone-input').type('5551234567', { delay: 50 });

// ✅ Clear before filling
await page.getByTestId('input').clear();
await page.getByTestId('input').fill('new value');
```

---

### 9. Select/Dropdown Not Working

**Symptom:** Value doesn't change or dropdown doesn't open.

**Solutions:**

```typescript
// Native <select>
await page.getByTestId('country-select').selectOption('US');
await page.getByTestId('country-select').selectOption({ label: 'United States' });

// Custom dropdown (MUI, etc.)
await page.getByTestId('dropdown-trigger').click();
await expect(page.getByTestId('dropdown-menu')).toBeVisible();
await page.getByTestId('option-us').click();
await expect(page.getByTestId('dropdown-menu')).not.toBeVisible();
```

---

### 10. Navigation Issues

**Symptom:** Page doesn't navigate or URL is wrong.

**Solutions:**

```typescript
// ✅ Wait for navigation to complete
await Promise.all([
  page.waitForURL('**/dashboard'),
  page.getByTestId('dashboard-link').click()
]);

// ✅ For SPA navigation
await page.getByTestId('nav-link').click();
await expect(page).toHaveURL('/expected-path');

// ✅ Handle redirects
await page.goto('/login');
await page.fill('[data-testid="email"]', 'user@example.com');
await page.fill('[data-testid="password"]', 'password');
await Promise.all([
  page.waitForURL('**/dashboard'), // Expect redirect after login
  page.getByTestId('submit').click()
]);
```

---

## Debugging Commands

### Interactive Debug Mode

```bash
# Run with inspector
npx playwright test --debug

# Run specific test in debug mode
npx playwright test my-test.spec.ts --debug

# Pause at specific point (add to test)
await page.pause();
```

### Trace Viewer

```bash
# Run with trace
npx playwright test --trace on

# View trace file
npx playwright show-trace trace.zip
```

### UI Mode

```bash
# Interactive test runner
npx playwright test --ui
```

### Screenshot Debugging

```typescript
// Add at failure points
await page.screenshot({ path: `debug-${Date.now()}.png`, fullPage: true });

// Screenshot specific element
await page.getByTestId('component').screenshot({ path: 'component.png' });
```

### Console & Network Logging

```typescript
// Log all console messages
page.on('console', msg => console.log('BROWSER:', msg.text()));

// Log all requests
page.on('request', request => console.log('REQ:', request.method(), request.url()));

// Log all responses
page.on('response', response => console.log('RES:', response.status(), response.url()));
```

---

## React-Specific Issues

### 1. State Not Updated After Action

```typescript
// ❌ Checking immediately after click
await page.getByTestId('increment').click();
const count = await page.getByTestId('count').textContent();
// count might still be old value

// ✅ Use assertion that auto-waits
await page.getByTestId('increment').click();
await expect(page.getByTestId('count')).toHaveText('1');
```

### 2. Suspense Boundaries

```typescript
// ✅ Wait for Suspense to resolve
await page.goto('/lazy-loaded-page');
await expect(page.getByTestId('loading-fallback')).not.toBeVisible({ timeout: 10000 });
await expect(page.getByTestId('actual-content')).toBeVisible();
```

### 3. React Query Refetch

```typescript
// ✅ When mutation causes refetch
await page.getByTestId('save-button').click();

// Wait for the refetch
await page.waitForResponse(resp => 
  resp.url().includes('/api/data') && resp.request().method() === 'GET'
);

await expect(page.getByTestId('updated-data')).toBeVisible();
```

### 4. Error Boundaries

```typescript
test('error boundary shows fallback', async ({ page }) => {
  // Force an error
  await page.route('**/api/critical', route => route.abort());
  
  await page.goto('/page-with-error-boundary');
  
  await expect(page.getByTestId('error-fallback')).toBeVisible();
  await expect(page.getByTestId('error-fallback')).toContainText('Something went wrong');
});
```

---

## Performance Debugging

### Slow Test Identification

```bash
# Run with timing
npx playwright test --reporter=list

# Output shows timing per test
✓ [chromium] › test.spec.ts:5:1 › fast test (1.2s)
✓ [chromium] › test.spec.ts:10:1 › slow test (45.3s) ← investigate this
```

### Identify Slow Operations

```typescript
test('profile test timing', async ({ page }) => {
  const start = Date.now();
  
  await page.goto('/');
  console.log(`goto: ${Date.now() - start}ms`);
  
  const t1 = Date.now();
  await page.getByTestId('button').click();
  console.log(`click: ${Date.now() - t1}ms`);
  
  const t2 = Date.now();
  await expect(page.getByTestId('result')).toBeVisible();
  console.log(`assertion: ${Date.now() - t2}ms`);
});
```

---

## Quick Reference: Error → Solution

| Error Message | Most Likely Solution |
|--------------|---------------------|
| `Timeout exceeded` | Add explicit wait for page state |
| `Element not visible` | Wait for element visibility |
| `Click intercepted` | Wait for overlay to disappear |
| `Element detached` | Don't store locators across re-renders |
| `strict mode violation` | Make selector more specific |
| `net::ERR_FAILED` | Check if server is running |
| `Page closed` | Don't navigate away mid-test |
| `browserContext.close: Target closed` | Increase timeout |

---

## Getting Help

1. **Check the trace** - 90% of issues are obvious in trace viewer
2. **Add screenshots** - Visual debugging is fastest
3. **Simplify the test** - Remove steps until you find the culprit
4. **Check browser console** - JavaScript errors often explain failures
5. **Run in headed mode** - Watch what happens: `npx playwright test --headed`
