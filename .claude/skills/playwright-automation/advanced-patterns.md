# Playwright Advanced Patterns

This document contains advanced patterns for complex testing scenarios. Reference this when dealing with sophisticated micro frontend architectures.

---

## Authentication Patterns

### Persistent Auth State

```typescript
// auth.setup.ts - Run once before all tests
import { test as setup, expect } from '@playwright/test';
import path from 'path';

const authFile = path.join(__dirname, '../.auth/user.json');

setup('authenticate', async ({ page }) => {
  await page.goto('/login');
  await page.getByTestId('login-email-input').fill(process.env.TEST_USER_EMAIL!);
  await page.getByTestId('login-password-input').fill(process.env.TEST_USER_PASSWORD!);
  await page.getByTestId('login-submit-button').click();
  
  // Wait for auth to complete
  await expect(page).toHaveURL('/dashboard');
  
  // Store auth state
  await page.context().storageState({ path: authFile });
});
```

```typescript
// playwright.config.ts
export default defineConfig({
  projects: [
    // Setup project - runs first
    { name: 'setup', testMatch: /.*\.setup\.ts/ },
    
    // Tests that need auth
    {
      name: 'chromium',
      dependencies: ['setup'],
      use: {
        storageState: '.auth/user.json',
      },
    },
    
    // Tests that don't need auth (login tests)
    {
      name: 'chromium-no-auth',
      testMatch: /.*auth.*\.spec\.ts/,
      use: {
        storageState: undefined,
      },
    },
  ],
});
```

### Role-Based Testing

```typescript
// fixtures/roles.ts
import { test as base } from '@playwright/test';
import { LoginPage } from '../pages/LoginPage';

type Roles = 'admin' | 'user' | 'viewer';

interface RoleCredentials {
  email: string;
  password: string;
}

const roleCredentials: Record<Roles, RoleCredentials> = {
  admin: { 
    email: process.env.TEST_ADMIN_EMAIL!, 
    password: process.env.TEST_ADMIN_PASSWORD! 
  },
  user: { 
    email: process.env.TEST_USER_EMAIL!, 
    password: process.env.TEST_USER_PASSWORD! 
  },
  viewer: { 
    email: process.env.TEST_VIEWER_EMAIL!, 
    password: process.env.TEST_VIEWER_PASSWORD! 
  },
};

export const test = base.extend<{ loginAs: (role: Roles) => Promise<void> }>({
  loginAs: async ({ page }, use) => {
    const loginAs = async (role: Roles) => {
      const creds = roleCredentials[role];
      const loginPage = new LoginPage(page);
      await loginPage.goto();
      await loginPage.login(creds.email, creds.password);
      await loginPage.expectLoginSuccess();
    };
    await use(loginAs);
  },
});

export { expect } from '@playwright/test';
```

```typescript
// tests/admin.spec.ts
import { test, expect } from '../fixtures/roles';

test('admin can access admin panel', async ({ page, loginAs }) => {
  await loginAs('admin');
  await page.goto('/admin');
  await expect(page.getByTestId('admin-dashboard')).toBeVisible();
});

test('viewer cannot access admin panel', async ({ page, loginAs }) => {
  await loginAs('viewer');
  await page.goto('/admin');
  await expect(page.getByTestId('access-denied-message')).toBeVisible();
});
```

---

## API Mocking Patterns

### GraphQL Mocking

```typescript
test('handles GraphQL queries', async ({ page }) => {
  await page.route('**/graphql', async (route, request) => {
    const body = request.postDataJSON();
    
    if (body.operationName === 'GetUser') {
      return route.fulfill({
        status: 200,
        json: {
          data: {
            user: {
              id: '123',
              name: 'Test User',
              email: 'test@example.com'
            }
          }
        }
      });
    }
    
    if (body.operationName === 'GetOrders') {
      return route.fulfill({
        status: 200,
        json: {
          data: {
            orders: [
              { id: '1', total: 100, status: 'completed' },
              { id: '2', total: 200, status: 'pending' }
            ]
          }
        }
      });
    }
    
    // Pass through other queries
    return route.continue();
  });
  
  await page.goto('/dashboard');
  await expect(page.getByTestId('user-name')).toContainText('Test User');
});
```

### Delayed Response Simulation

```typescript
test('shows loading state during slow API', async ({ page }) => {
  await page.route('**/api/heavy-data', async route => {
    // Simulate slow API
    await new Promise(resolve => setTimeout(resolve, 2000));
    return route.fulfill({
      status: 200,
      json: { items: [] }
    });
  });
  
  await page.goto('/heavy-data-page');
  
  // Loading state should be visible
  await expect(page.getByTestId('loading-skeleton')).toBeVisible();
  
  // Eventually data loads
  await expect(page.getByTestId('data-container')).toBeVisible({ timeout: 5000 });
  await expect(page.getByTestId('loading-skeleton')).not.toBeVisible();
});
```

### Network Failure Simulation

```typescript
test('handles network failure gracefully', async ({ page }) => {
  await page.route('**/api/critical-data', route => {
    route.abort('failed');
  });
  
  await page.goto('/data-page');
  
  await expect(page.getByTestId('error-boundary')).toBeVisible();
  await expect(page.getByTestId('retry-button')).toBeVisible();
});

test('retries on network failure', async ({ page }) => {
  let requestCount = 0;
  
  await page.route('**/api/data', route => {
    requestCount++;
    if (requestCount < 3) {
      return route.abort('failed');
    }
    return route.fulfill({ status: 200, json: { success: true } });
  });
  
  await page.goto('/data-page');
  await page.getByTestId('load-button').click();
  
  // Should succeed after retries
  await expect(page.getByTestId('success-message')).toBeVisible();
  expect(requestCount).toBe(3);
});
```

---

## Complex Component Patterns

### Drag and Drop

```typescript
test('can reorder items via drag and drop', async ({ page }) => {
  await page.goto('/kanban-board');
  
  const sourceCard = page.getByTestId('card-task-1');
  const targetColumn = page.getByTestId('column-done');
  
  // Perform drag and drop
  await sourceCard.dragTo(targetColumn);
  
  // Verify card moved
  await expect(targetColumn.getByTestId('card-task-1')).toBeVisible();
});

// Alternative approach with manual drag
test('drag with coordinates', async ({ page }) => {
  await page.goto('/sortable-list');
  
  const item = page.getByTestId('list-item-1');
  const targetItem = page.getByTestId('list-item-3');
  
  // Get bounding boxes
  const itemBox = await item.boundingBox();
  const targetBox = await targetItem.boundingBox();
  
  if (itemBox && targetBox) {
    await page.mouse.move(
      itemBox.x + itemBox.width / 2, 
      itemBox.y + itemBox.height / 2
    );
    await page.mouse.down();
    await page.mouse.move(
      targetBox.x + targetBox.width / 2, 
      targetBox.y + targetBox.height / 2,
      { steps: 10 }
    );
    await page.mouse.up();
  }
  
  // Verify new order
  const items = page.getByTestId('list-item');
  await expect(items.nth(2)).toHaveAttribute('data-id', '1');
});
```

### File Upload

```typescript
test('uploads file successfully', async ({ page }) => {
  await page.goto('/upload-page');
  
  // Set file for upload
  const fileInput = page.getByTestId('file-input');
  await fileInput.setInputFiles('./test-files/document.pdf');
  
  // Verify file selected
  await expect(page.getByTestId('selected-filename')).toContainText('document.pdf');
  
  // Submit upload
  await page.getByTestId('upload-button').click();
  
  // Wait for upload completion
  await page.waitForResponse(resp => 
    resp.url().includes('/api/upload') && resp.status() === 200
  );
  
  await expect(page.getByTestId('upload-success')).toBeVisible();
});

test('handles multiple file upload', async ({ page }) => {
  await page.goto('/multi-upload');
  
  await page.getByTestId('file-input').setInputFiles([
    './test-files/doc1.pdf',
    './test-files/doc2.pdf',
    './test-files/image.png',
  ]);
  
  await expect(page.getByTestId('file-list').getByTestId('file-item')).toHaveCount(3);
});

test('drag and drop file upload', async ({ page }) => {
  await page.goto('/dropzone-upload');
  
  // Create a file buffer
  const buffer = Buffer.from('test file content');
  
  // Create DataTransfer with file
  const dataTransfer = await page.evaluateHandle((data) => {
    const dt = new DataTransfer();
    const file = new File([new Uint8Array(data)], 'test.txt', { type: 'text/plain' });
    dt.items.add(file);
    return dt;
  }, [...buffer]);
  
  // Dispatch drop event
  await page.getByTestId('drop-zone').dispatchEvent('drop', { dataTransfer });
  
  await expect(page.getByTestId('uploaded-file')).toContainText('test.txt');
});
```

### Date Pickers

```typescript
test('selects date from date picker', async ({ page }) => {
  await page.goto('/booking-form');
  
  // Open date picker
  await page.getByTestId('date-picker-trigger').click();
  
  // Wait for calendar to be visible
  await expect(page.getByTestId('date-picker-calendar')).toBeVisible();
  
  // Navigate to next month
  await page.getByTestId('calendar-next-month').click();
  
  // Select specific date
  await page.getByTestId('calendar-day-15').click();
  
  // Verify selection
  await expect(page.getByTestId('date-input')).toHaveValue(/\/15\//);
  await expect(page.getByTestId('date-picker-calendar')).not.toBeVisible();
});
```

### Rich Text Editors

```typescript
test('interacts with rich text editor', async ({ page }) => {
  await page.goto('/content-editor');
  
  // Focus the editor
  const editor = page.getByTestId('rich-text-editor');
  await editor.click();
  
  // Type content
  await page.keyboard.type('Hello, this is a test');
  
  // Select text and make bold
  await page.keyboard.press('Control+A');
  await page.getByTestId('toolbar-bold').click();
  
  // Verify bold applied
  await expect(editor.locator('strong')).toContainText('Hello, this is a test');
  
  // Or check via content
  const content = await editor.innerHTML();
  expect(content).toContain('<strong>');
});
```

---

## Visual Regression Testing

### Screenshot Comparison

```typescript
test('landing page visual regression', async ({ page }) => {
  await page.goto('/');
  
  // Wait for all images and fonts to load
  await page.waitForLoadState('networkidle');
  
  // Disable animations for consistent screenshots
  await page.addStyleTag({
    content: `
      *, *::before, *::after {
        animation-duration: 0s !important;
        transition-duration: 0s !important;
      }
    `
  });
  
  // Full page screenshot
  await expect(page).toHaveScreenshot('landing-page.png', {
    fullPage: true,
    maxDiffPixelRatio: 0.01,
  });
});

test('component visual regression', async ({ page }) => {
  await page.goto('/components/button-showcase');
  
  // Screenshot specific component
  const buttonGroup = page.getByTestId('primary-buttons');
  await expect(buttonGroup).toHaveScreenshot('primary-buttons.png');
});

test('responsive visual regression', async ({ page }) => {
  await page.goto('/dashboard');
  
  // Desktop
  await page.setViewportSize({ width: 1920, height: 1080 });
  await expect(page).toHaveScreenshot('dashboard-desktop.png');
  
  // Tablet
  await page.setViewportSize({ width: 768, height: 1024 });
  await expect(page).toHaveScreenshot('dashboard-tablet.png');
  
  // Mobile
  await page.setViewportSize({ width: 375, height: 667 });
  await expect(page).toHaveScreenshot('dashboard-mobile.png');
});
```

### Masking Dynamic Content

```typescript
test('screenshot with masked dynamic content', async ({ page }) => {
  await page.goto('/profile');
  
  await expect(page).toHaveScreenshot('profile-page.png', {
    mask: [
      page.getByTestId('user-avatar'),     // Avatar changes
      page.getByTestId('timestamp'),        // Time changes
      page.getByTestId('random-banner'),    // Random ad
    ],
    maskColor: '#FF00FF', // Magenta for visibility
  });
});
```

---

## Accessibility Testing

### Automated A11y Checks

```typescript
import AxeBuilder from '@axe-core/playwright';

test('page has no accessibility violations', async ({ page }) => {
  await page.goto('/');
  
  const accessibilityScanResults = await new AxeBuilder({ page })
    .withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa'])
    .analyze();
  
  expect(accessibilityScanResults.violations).toEqual([]);
});

test('form is accessible', async ({ page }) => {
  await page.goto('/contact-form');
  
  const accessibilityScanResults = await new AxeBuilder({ page })
    .include('[data-testid="contact-form"]')
    .analyze();
  
  expect(accessibilityScanResults.violations).toEqual([]);
});

test('modal accessibility', async ({ page }) => {
  await page.goto('/page-with-modal');
  await page.getByTestId('open-modal').click();
  
  // Wait for modal
  await expect(page.getByTestId('modal')).toBeVisible();
  
  const results = await new AxeBuilder({ page })
    .include('[data-testid="modal"]')
    .analyze();
  
  expect(results.violations).toEqual([]);
});
```

### Keyboard Navigation Testing

```typescript
test('form is keyboard navigable', async ({ page }) => {
  await page.goto('/form-page');
  
  // Tab through form fields
  await page.keyboard.press('Tab');
  await expect(page.getByTestId('first-name-input')).toBeFocused();
  
  await page.keyboard.press('Tab');
  await expect(page.getByTestId('last-name-input')).toBeFocused();
  
  await page.keyboard.press('Tab');
  await expect(page.getByTestId('email-input')).toBeFocused();
  
  await page.keyboard.press('Tab');
  await expect(page.getByTestId('submit-button')).toBeFocused();
  
  // Can submit with Enter
  await page.keyboard.press('Enter');
  await expect(page.getByTestId('success-message')).toBeVisible();
});

test('modal traps focus', async ({ page }) => {
  await page.goto('/modal-page');
  await page.getByTestId('open-modal').click();
  
  // Modal should have focus
  await expect(page.getByTestId('modal')).toBeFocused();
  
  // Tab should stay within modal
  await page.keyboard.press('Tab');
  const focusedId1 = await page.evaluate(() => document.activeElement?.getAttribute('data-testid'));
  expect(focusedId1).toMatch(/modal-.*/);
  
  // Escape closes modal
  await page.keyboard.press('Escape');
  await expect(page.getByTestId('modal')).not.toBeVisible();
});
```

---

## Performance Testing

### Core Web Vitals

```typescript
test('page meets performance thresholds', async ({ page }) => {
  await page.goto('/');
  
  // Measure performance metrics
  const metrics = await page.evaluate(() => {
    return new Promise((resolve) => {
      new PerformanceObserver((list) => {
        const entries = list.getEntries();
        const lcp = entries.find(e => e.entryType === 'largest-contentful-paint');
        resolve({
          lcp: lcp?.startTime,
          fcp: performance.getEntriesByName('first-contentful-paint')[0]?.startTime,
          domContentLoaded: performance.timing.domContentLoadedEventEnd - performance.timing.navigationStart,
          load: performance.timing.loadEventEnd - performance.timing.navigationStart,
        });
      }).observe({ entryTypes: ['largest-contentful-paint', 'paint'] });
      
      // Wait a bit for LCP
      setTimeout(() => resolve(null), 5000);
    });
  });
  
  // Assert thresholds
  expect(metrics.lcp).toBeLessThan(2500); // LCP < 2.5s
  expect(metrics.fcp).toBeLessThan(1800); // FCP < 1.8s
});
```

### Bundle Size Check

```typescript
test('JavaScript bundle size is acceptable', async ({ page }) => {
  let totalJsSize = 0;
  
  page.on('response', async (response) => {
    if (response.url().endsWith('.js')) {
      const headers = await response.allHeaders();
      const size = parseInt(headers['content-length'] || '0', 10);
      totalJsSize += size;
    }
  });
  
  await page.goto('/');
  await page.waitForLoadState('networkidle');
  
  const totalMB = totalJsSize / (1024 * 1024);
  console.log(`Total JS size: ${totalMB.toFixed(2)} MB`);
  
  expect(totalMB).toBeLessThan(2); // Max 2MB of JS
});
```

---

## Parallel Test Fixtures

### Database Isolation

```typescript
import { test as base } from '@playwright/test';
import { TestDatabase } from '../utils/testDatabase';

export const test = base.extend<{
  db: TestDatabase;
}>({
  db: async ({}, use, testInfo) => {
    // Create isolated database for this test
    const dbName = `test_${testInfo.parallelIndex}_${Date.now()}`;
    const db = await TestDatabase.create(dbName);
    
    await use(db);
    
    // Cleanup after test
    await db.drop();
  },
});
```

### Worker-Scoped Fixtures

```typescript
import { test as base } from '@playwright/test';

export const test = base.extend<{}, { apiServer: string }>({
  // Worker-scoped: one per parallel worker
  apiServer: [async ({}, use) => {
    // Start a mock API server for this worker
    const server = await startMockServer();
    await use(server.url);
    await server.close();
  }, { scope: 'worker' }],
});
```

---

## CI/CD Integration

### GitHub Actions Example

```yaml
# .github/workflows/e2e.yml
name: E2E Tests

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v4
      
      - uses: actions/setup-node@v4
        with:
          node-version: 20
          cache: 'npm'
      
      - name: Install dependencies
        run: npm ci
      
      - name: Install Playwright browsers
        run: npx playwright install --with-deps
      
      - name: Run Playwright tests
        run: npx playwright test
        env:
          BASE_URL: http://localhost:3000
          TEST_USER_EMAIL: ${{ secrets.TEST_USER_EMAIL }}
          TEST_USER_PASSWORD: ${{ secrets.TEST_USER_PASSWORD }}
      
      - uses: actions/upload-artifact@v4
        if: always()
        with:
          name: playwright-report
          path: playwright-report/
          retention-days: 30
      
      - uses: actions/upload-artifact@v4
        if: failure()
        with:
          name: test-traces
          path: test-results/
          retention-days: 7
```

### Sharding for Large Test Suites

```yaml
jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        shard: [1, 2, 3, 4]
    
    steps:
      # ... setup steps ...
      
      - name: Run tests (shard ${{ matrix.shard }}/4)
        run: npx playwright test --shard=${{ matrix.shard }}/4
```
