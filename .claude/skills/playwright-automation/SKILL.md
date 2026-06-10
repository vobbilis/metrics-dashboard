---
name: playwright-automation
description: Use when creating, editing, or debugging ANY Playwright test for React micro frontend UIs. MANDATORY for all E2E test automation. FORBIDDEN patterns include flaky selectors (nth-child, class-based), hard-coded waits (setTimeout), test interdependence. REQUIRED patterns are data-testid selectors, auto-waiting assertions, Page Object Model, isolated test state.
---

# Playwright Automation for React Micro Frontend Testing

## THE MANDATE

This skill is **MANDATORY** for all Playwright E2E test automation. If you write Playwright tests without following these guidelines, your tests WILL be flaky and WILL fail in CI.

**The goal:** Tests that are **stable**, **fast**, **maintainable**, and **deterministic**.

---

## GOLDEN RULES

```
1. NEVER use fragile selectors - Use data-testid ONLY
2. NEVER use hard waits - Use auto-waiting assertions
3. NEVER share state between tests - Each test is isolated
4. NEVER test implementation - Test user behavior
5. ALWAYS use Page Object Model - Encapsulate page logic
6. ALWAYS wait for network - Don't race with async operations
```

---

## FORBIDDEN PATTERNS (Never Generate These)

### ❌ Fragile Selectors - ABSOLUTELY BANNED

```typescript
// ❌ FORBIDDEN - Will break with ANY UI change
await page.click('.btn-primary');
await page.click('#submit-button');
await page.click('button.MuiButton-root');
await page.locator('div > span > button').click();
await page.locator(':nth-child(3)').click();
await page.locator('//div[@class="container"]/button[1]').click();
await page.getByText('Submit').click(); // Breaks with i18n

// ✅ REQUIRED - Stable data-testid selectors
await page.getByTestId('submit-button').click();
await page.getByTestId('login-form').getByTestId('email-input').fill('test@example.com');
```

**If you generate a CSS class selector, XPath, or nth-child, you have FAILED.**

### ❌ Hard-Coded Waits - ABSOLUTELY BANNED

```typescript
// ❌ FORBIDDEN - Flaky and slow
await page.click('[data-testid="submit"]');
await page.waitForTimeout(2000);  // BANNED
await new Promise(r => setTimeout(r, 1000));  // BANNED
await page.waitForTimeout(5000);  // "Just to be safe" - BANNED

// ✅ REQUIRED - Auto-waiting assertions
await page.getByTestId('submit-button').click();
await expect(page.getByTestId('success-message')).toBeVisible();
await expect(page.getByTestId('data-table')).toContainText('Record saved');
```

**If you generate `waitForTimeout` or `setTimeout`, you have FAILED.**

### ❌ Test Interdependence - BANNED

```typescript
// ❌ FORBIDDEN - Tests depend on each other
test('create user', async ({ page }) => {
  // Creates user that next test depends on
});

test('edit user', async ({ page }) => {
  // Assumes previous test created user - WILL FAIL if run alone
});

// ✅ REQUIRED - Each test is independent
test('edit user', async ({ page }) => {
  // Setup: Create user via API (not UI)
  const user = await apiContext.post('/api/users', { data: testUser });
  
  // Test: Edit user via UI
  await page.goto(`/users/${user.id}/edit`);
  // ... test edit functionality
});
```

### ❌ Testing Implementation Details - BANNED

```typescript
// ❌ FORBIDDEN - Testing React internals
await expect(page.locator('[data-reactroot]')).toBeVisible();
await page.evaluate(() => window.__REACT_DEVTOOLS_GLOBAL_HOOK__);
await expect(page.locator('.MuiCircularProgress-root')).not.toBeVisible();

// ✅ REQUIRED - Test what USER sees
await expect(page.getByTestId('user-profile')).toContainText('John Doe');
await expect(page.getByTestId('loading-indicator')).not.toBeVisible();
```

### ❌ Ignoring Network State - BANNED

```typescript
// ❌ FORBIDDEN - Racing with network
await page.getByTestId('submit').click();
await expect(page.getByTestId('result')).toBeVisible(); // May fail if API slow

// ✅ REQUIRED - Wait for network to settle
await page.getByTestId('submit').click();
await page.waitForResponse(resp => resp.url().includes('/api/submit') && resp.status() === 200);
await expect(page.getByTestId('result')).toBeVisible();

// OR use route interception for deterministic tests
await page.route('**/api/submit', route => {
  route.fulfill({ status: 200, json: { success: true } });
});
```

### ❌ Ambiguous Locators - BANNED

```typescript
// ❌ FORBIDDEN - Multiple elements could match
await page.getByRole('button').click();  // Which button?
await page.getByText('Save').click();    // Multiple "Save" on page

// ✅ REQUIRED - Unique, specific locators
await page.getByTestId('user-form-save-button').click();
await page.getByTestId('settings-modal').getByTestId('save-button').click();
```

---

## REQUIRED PATTERNS (Always Use These)

### ✅ Data-TestId Strategy

**Frontend developers MUST add data-testid attributes. QA engineers MUST use them.**

```typescript
// Component (React)
<Button data-testid="checkout-submit-button" onClick={handleSubmit}>
  Complete Purchase
</Button>

<TextField
  data-testid="checkout-email-input"
  value={email}
  onChange={handleChange}
/>

<DataGrid data-testid="orders-table" rows={orders} />
```

```typescript
// Test (Playwright)
await page.getByTestId('checkout-submit-button').click();
await page.getByTestId('checkout-email-input').fill('test@example.com');
await expect(page.getByTestId('orders-table')).toBeVisible();
```

**Naming Convention:**
```
data-testid="{context}-{element}-{type}"

Examples:
- login-email-input
- login-password-input  
- login-submit-button
- user-profile-avatar
- nav-dashboard-link
- modal-confirm-button
- table-user-row
- form-validation-error
```

### ✅ Page Object Model (POM) - MANDATORY

**Every page/component MUST have a Page Object.**

```typescript
// pages/LoginPage.ts
import { Page, Locator, expect } from '@playwright/test';

export class LoginPage {
  readonly page: Page;
  readonly emailInput: Locator;
  readonly passwordInput: Locator;
  readonly submitButton: Locator;
  readonly errorMessage: Locator;
  readonly successRedirect: string = '/dashboard';

  constructor(page: Page) {
    this.page = page;
    this.emailInput = page.getByTestId('login-email-input');
    this.passwordInput = page.getByTestId('login-password-input');
    this.submitButton = page.getByTestId('login-submit-button');
    this.errorMessage = page.getByTestId('login-error-message');
  }

  async goto() {
    await this.page.goto('/login');
    await expect(this.emailInput).toBeVisible();
  }

  async login(email: string, password: string) {
    await this.emailInput.fill(email);
    await this.passwordInput.fill(password);
    await this.submitButton.click();
  }

  async expectLoginSuccess() {
    await expect(this.page).toHaveURL(this.successRedirect);
  }

  async expectLoginError(message: string) {
    await expect(this.errorMessage).toContainText(message);
  }
}
```

```typescript
// tests/login.spec.ts
import { test, expect } from '@playwright/test';
import { LoginPage } from '../pages/LoginPage';

test.describe('Login', () => {
  let loginPage: LoginPage;

  test.beforeEach(async ({ page }) => {
    loginPage = new LoginPage(page);
    await loginPage.goto();
  });

  test('successful login redirects to dashboard', async () => {
    await loginPage.login('valid@example.com', 'validPassword123');
    await loginPage.expectLoginSuccess();
  });

  test('invalid credentials shows error', async () => {
    await loginPage.login('invalid@example.com', 'wrongPassword');
    await loginPage.expectLoginError('Invalid email or password');
  });
});
```

### ✅ Component Page Objects for Micro Frontends

**For micro frontend architecture, create component-level page objects:**

```typescript
// components/HeaderComponent.ts
export class HeaderComponent {
  readonly page: Page;
  readonly root: Locator;
  readonly userMenu: Locator;
  readonly logoutButton: Locator;
  readonly notificationBell: Locator;

  constructor(page: Page) {
    this.page = page;
    this.root = page.getByTestId('app-header');
    this.userMenu = this.root.getByTestId('user-menu-trigger');
    this.logoutButton = this.root.getByTestId('logout-button');
    this.notificationBell = this.root.getByTestId('notification-bell');
  }

  async openUserMenu() {
    await this.userMenu.click();
    await expect(this.logoutButton).toBeVisible();
  }

  async logout() {
    await this.openUserMenu();
    await this.logoutButton.click();
  }

  async getNotificationCount(): Promise<number> {
    const badge = this.notificationBell.getByTestId('notification-count');
    const text = await badge.textContent();
    return parseInt(text || '0', 10);
  }
}
```

```typescript
// components/DataTableComponent.ts
export class DataTableComponent {
  readonly page: Page;
  readonly root: Locator;

  constructor(page: Page, testId: string) {
    this.page = page;
    this.root = page.getByTestId(testId);
  }

  async getRowCount(): Promise<number> {
    const rows = this.root.getByTestId('table-row');
    return await rows.count();
  }

  async getRow(index: number): Promise<Locator> {
    return this.root.getByTestId('table-row').nth(index);
  }

  async clickRowAction(rowIndex: number, action: string) {
    const row = await this.getRow(rowIndex);
    await row.getByTestId(`action-${action}`).click();
  }

  async expectRowContains(index: number, text: string) {
    const row = await this.getRow(index);
    await expect(row).toContainText(text);
  }

  async waitForData() {
    await expect(this.root.getByTestId('table-row').first()).toBeVisible();
  }

  async expectEmpty() {
    await expect(this.root.getByTestId('empty-state')).toBeVisible();
  }
}
```

### ✅ Auto-Waiting Assertions - MANDATORY

```typescript
// ✅ REQUIRED - Playwright auto-waits for these
await expect(page.getByTestId('modal')).toBeVisible();
await expect(page.getByTestId('modal')).not.toBeVisible();
await expect(page.getByTestId('input')).toHaveValue('expected');
await expect(page.getByTestId('message')).toContainText('Success');
await expect(page.getByTestId('button')).toBeEnabled();
await expect(page.getByTestId('checkbox')).toBeChecked();
await expect(page).toHaveURL('/dashboard');
await expect(page).toHaveTitle('Dashboard');

// For lists/tables
await expect(page.getByTestId('list-item')).toHaveCount(5);
```

### ✅ Network Interception for Deterministic Tests

```typescript
test('displays user data from API', async ({ page }) => {
  // Mock API response for deterministic test
  await page.route('**/api/users/123', route => {
    route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        id: 123,
        name: 'Test User',
        email: 'test@example.com'
      })
    });
  });

  await page.goto('/users/123');
  await expect(page.getByTestId('user-name')).toContainText('Test User');
  await expect(page.getByTestId('user-email')).toContainText('test@example.com');
});

test('handles API errors gracefully', async ({ page }) => {
  await page.route('**/api/users/123', route => {
    route.fulfill({ status: 500, body: 'Internal Server Error' });
  });

  await page.goto('/users/123');
  await expect(page.getByTestId('error-message')).toContainText('Failed to load user');
});
```

### ✅ Test Data Setup via API (Not UI)

```typescript
// fixtures/testData.ts
import { APIRequestContext } from '@playwright/test';

export class TestDataFactory {
  constructor(private apiContext: APIRequestContext) {}

  async createUser(overrides: Partial<User> = {}): Promise<User> {
    const userData = {
      email: `test-${Date.now()}@example.com`,
      name: 'Test User',
      role: 'user',
      ...overrides
    };
    
    const response = await this.apiContext.post('/api/users', { data: userData });
    return response.json();
  }

  async deleteUser(id: string): Promise<void> {
    await this.apiContext.delete(`/api/users/${id}`);
  }

  async createOrder(userId: string, items: OrderItem[]): Promise<Order> {
    const response = await this.apiContext.post('/api/orders', {
      data: { userId, items }
    });
    return response.json();
  }
}
```

```typescript
// tests/orders.spec.ts
import { test, expect } from '@playwright/test';
import { TestDataFactory } from '../fixtures/testData';
import { OrdersPage } from '../pages/OrdersPage';

test.describe('Orders', () => {
  let testData: TestDataFactory;
  let testUser: User;

  test.beforeAll(async ({ request }) => {
    testData = new TestDataFactory(request);
    testUser = await testData.createUser();
  });

  test.afterAll(async () => {
    await testData.deleteUser(testUser.id);
  });

  test('user can view their orders', async ({ page }) => {
    // Setup via API (fast)
    await testData.createOrder(testUser.id, [{ productId: '1', quantity: 2 }]);
    
    // Test via UI
    const ordersPage = new OrdersPage(page);
    await ordersPage.goto();
    await ordersPage.expectOrderCount(1);
  });
});
```

---

## TEST STRUCTURE TEMPLATE

### File Organization

```
e2e/
  fixtures/
    testData.ts           # Test data factory
    auth.ts               # Authentication fixtures
  pages/
    BasePage.ts           # Base page object
    LoginPage.ts
    DashboardPage.ts
    UserProfilePage.ts
  components/
    HeaderComponent.ts
    SidebarComponent.ts
    DataTableComponent.ts
    ModalComponent.ts
  tests/
    auth/
      login.spec.ts
      logout.spec.ts
      password-reset.spec.ts
    users/
      user-crud.spec.ts
      user-profile.spec.ts
    orders/
      order-creation.spec.ts
      order-management.spec.ts
  utils/
    helpers.ts
    constants.ts
  playwright.config.ts
```

### Base Page Object

```typescript
// pages/BasePage.ts
import { Page, Locator, expect } from '@playwright/test';
import { HeaderComponent } from '../components/HeaderComponent';

export abstract class BasePage {
  readonly page: Page;
  readonly header: HeaderComponent;

  constructor(page: Page) {
    this.page = page;
    this.header = new HeaderComponent(page);
  }

  abstract readonly url: string;

  async goto() {
    await this.page.goto(this.url);
    await this.waitForPageLoad();
  }

  async waitForPageLoad() {
    // Override in subclass if needed
    await this.page.waitForLoadState('networkidle');
  }

  async expectUrl() {
    await expect(this.page).toHaveURL(new RegExp(this.url));
  }

  getByTestId(testId: string): Locator {
    return this.page.getByTestId(testId);
  }

  async takeScreenshot(name: string) {
    await this.page.screenshot({ path: `screenshots/${name}.png` });
  }
}
```

### Test Template

```typescript
// tests/feature/feature-name.spec.ts
import { test, expect } from '@playwright/test';
import { FeaturePage } from '../../pages/FeaturePage';
import { TestDataFactory } from '../../fixtures/testData';

test.describe('Feature Name', () => {
  let featurePage: FeaturePage;
  let testData: TestDataFactory;

  test.beforeAll(async ({ request }) => {
    testData = new TestDataFactory(request);
    // Global setup for this test suite
  });

  test.beforeEach(async ({ page }) => {
    featurePage = new FeaturePage(page);
    await featurePage.goto();
  });

  test.afterEach(async ({ page }, testInfo) => {
    // Screenshot on failure
    if (testInfo.status !== 'passed') {
      await page.screenshot({ 
        path: `screenshots/${testInfo.title}-failure.png` 
      });
    }
  });

  test.afterAll(async () => {
    // Cleanup test data
  });

  test('should do expected behavior', async ({ page }) => {
    // Arrange
    const expectedValue = 'expected';
    
    // Act
    await featurePage.performAction();
    
    // Assert
    await featurePage.expectResult(expectedValue);
  });
});
```

---

## REACT MICRO FRONTEND SPECIFIC PATTERNS

### ✅ Handling Dynamic Loading / Code Splitting

```typescript
// React micro frontends often lazy-load components
test('micro frontend loads successfully', async ({ page }) => {
  await page.goto('/dashboard');
  
  // Wait for the micro frontend container to be visible
  await expect(page.getByTestId('mfe-dashboard-container')).toBeVisible();
  
  // Wait for the actual content (not loading state)
  await expect(page.getByTestId('dashboard-content')).toBeVisible();
  
  // Ensure loading indicator is gone
  await expect(page.getByTestId('mfe-loading-indicator')).not.toBeVisible();
});
```

### ✅ Handling Shadow DOM (Web Components)

```typescript
// If micro frontends use Shadow DOM
test('interacts with shadow DOM content', async ({ page }) => {
  // Playwright can pierce shadow DOM with >> syntax
  const shadowButton = page.locator('my-component >> [data-testid="shadow-button"]');
  await shadowButton.click();
  
  // Or use page.locator with piercing
  const shadowInput = page.locator('my-component').locator('[data-testid="shadow-input"]');
  await shadowInput.fill('test value');
});
```

### ✅ Cross-Origin Micro Frontend Testing

```typescript
// playwright.config.ts
export default defineConfig({
  use: {
    // Allow testing across micro frontend origins
    ignoreHTTPSErrors: true,
    bypassCSP: true,
  },
  webServer: [
    {
      command: 'npm run start:shell',
      port: 3000,
      reuseExistingServer: !process.env.CI,
    },
    {
      command: 'npm run start:mfe-dashboard',
      port: 3001,
      reuseExistingServer: !process.env.CI,
    },
    {
      command: 'npm run start:mfe-settings',
      port: 3002,
      reuseExistingServer: !process.env.CI,
    },
  ],
});
```

### ✅ Testing Module Federation Boundaries

```typescript
test('navigates between micro frontends', async ({ page }) => {
  // Start in shell application
  await page.goto('/');
  await expect(page.getByTestId('shell-header')).toBeVisible();
  
  // Navigate to dashboard MFE
  await page.getByTestId('nav-dashboard').click();
  await expect(page.getByTestId('mfe-dashboard-root')).toBeVisible();
  
  // Navigate to settings MFE  
  await page.getByTestId('nav-settings').click();
  await expect(page.getByTestId('mfe-settings-root')).toBeVisible();
  
  // Verify shared state persists (e.g., user context)
  await expect(page.getByTestId('user-display-name')).toContainText('Test User');
});
```

---

## HANDLING COMMON REACT PATTERNS

### ✅ React Query / Data Fetching

```typescript
test('handles React Query data loading', async ({ page }) => {
  // Mock the API response
  await page.route('**/api/data', route => {
    route.fulfill({
      status: 200,
      json: { items: [{ id: 1, name: 'Item 1' }] }
    });
  });

  await page.goto('/data-page');
  
  // Wait for data to load (not the loading state)
  await expect(page.getByTestId('data-list')).toBeVisible();
  await expect(page.getByTestId('data-item')).toHaveCount(1);
});
```

### ✅ React Forms with Validation

```typescript
test('form validation shows errors', async ({ page }) => {
  const formPage = new FormPage(page);
  await formPage.goto();
  
  // Submit empty form
  await formPage.submit();
  
  // Check validation errors appear
  await expect(page.getByTestId('email-error')).toContainText('Email is required');
  await expect(page.getByTestId('password-error')).toContainText('Password is required');
  
  // Fill invalid data
  await formPage.fillEmail('invalid-email');
  await formPage.submit();
  await expect(page.getByTestId('email-error')).toContainText('Invalid email format');
  
  // Fill valid data - errors clear
  await formPage.fillEmail('valid@example.com');
  await formPage.fillPassword('ValidPassword123!');
  await expect(page.getByTestId('email-error')).not.toBeVisible();
});
```

### ✅ React Context / Global State

```typescript
test('theme context changes apply globally', async ({ page }) => {
  await page.goto('/settings');
  
  // Check initial theme
  await expect(page.locator('body')).toHaveAttribute('data-theme', 'light');
  
  // Change theme
  await page.getByTestId('theme-toggle').click();
  await page.getByTestId('theme-dark-option').click();
  
  // Verify theme applied to body
  await expect(page.locator('body')).toHaveAttribute('data-theme', 'dark');
  
  // Navigate to different page - theme persists
  await page.getByTestId('nav-dashboard').click();
  await expect(page.locator('body')).toHaveAttribute('data-theme', 'dark');
});
```

### ✅ React Portals (Modals, Tooltips, Dropdowns)

```typescript
test('modal renders in portal', async ({ page }) => {
  await page.goto('/page-with-modal');
  
  // Click trigger
  await page.getByTestId('open-modal-button').click();
  
  // Modal renders in portal (outside normal DOM hierarchy)
  // But data-testid still works!
  await expect(page.getByTestId('modal-container')).toBeVisible();
  await expect(page.getByTestId('modal-title')).toContainText('Confirm Action');
  
  // Interact with modal content
  await page.getByTestId('modal-confirm-button').click();
  
  // Modal closes
  await expect(page.getByTestId('modal-container')).not.toBeVisible();
});
```

---

## DEBUGGING FLAKY TESTS

### Investigation Checklist

When a test is flaky, check in this order:

1. **Selector Stability**
   ```typescript
   // Is the selector unique and stable?
   // Add logging to see what's found:
   const elements = await page.getByTestId('my-element').count();
   console.log(`Found ${elements} elements with testId`);
   ```

2. **Race Conditions**
   ```typescript
   // Are you waiting for the right thing?
   // Add explicit network wait:
   await Promise.all([
     page.waitForResponse('**/api/data'),
     page.getByTestId('load-button').click()
   ]);
   ```

3. **Animation/Transition Issues**
   ```typescript
   // Disable animations in test:
   await page.addStyleTag({
     content: `*, *::before, *::after { 
       animation-duration: 0s !important; 
       transition-duration: 0s !important; 
     }`
   });
   ```

4. **Viewport/Responsive Issues**
   ```typescript
   // Set consistent viewport:
   await page.setViewportSize({ width: 1280, height: 720 });
   ```

### Trace Viewer for Debugging

```typescript
// playwright.config.ts
export default defineConfig({
  use: {
    trace: 'on-first-retry', // Capture trace on failure
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',
  },
});
```

```bash
# View trace after failure
npx playwright show-trace trace.zip
```

---

## CHECKLIST

### Before Writing Tests

- [ ] Identify all data-testid attributes needed
- [ ] Request missing data-testids from frontend devs
- [ ] Create Page Objects for all pages involved
- [ ] Create Component Objects for reusable components
- [ ] Plan test data setup (via API, not UI)

### Writing Each Test

- [ ] Test has descriptive name explaining behavior
- [ ] Uses only data-testid selectors
- [ ] No waitForTimeout or setTimeout
- [ ] Test is independent (can run in isolation)
- [ ] Uses auto-waiting assertions
- [ ] Mocks external APIs for determinism
- [ ] Follows Arrange-Act-Assert pattern

### After Writing Tests

- [ ] Run test 10 times consecutively - all pass?
- [ ] Run test in CI environment - passes?
- [ ] Run test in parallel with others - passes?
- [ ] Test cleans up its data
- [ ] Page Objects updated if needed

---

## PLAYWRIGHT CONFIG TEMPLATE

```typescript
// playwright.config.ts
import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  testDir: './e2e/tests',
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 4 : undefined,
  reporter: [
    ['html', { open: 'never' }],
    ['junit', { outputFile: 'test-results/junit.xml' }],
  ],
  use: {
    baseURL: process.env.BASE_URL || 'http://localhost:3000',
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',
    actionTimeout: 10000,
    navigationTimeout: 30000,
  },
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
    {
      name: 'firefox',
      use: { ...devices['Desktop Firefox'] },
    },
    {
      name: 'webkit',
      use: { ...devices['Desktop Safari'] },
    },
    {
      name: 'mobile-chrome',
      use: { ...devices['Pixel 5'] },
    },
  ],
  webServer: {
    command: 'npm run start',
    port: 3000,
    reuseExistingServer: !process.env.CI,
    timeout: 120000,
  },
});
```

---

## QUICK REFERENCE

### Selector Priority (Best to Worst)

| Priority | Selector Type | Example | Stability |
|----------|--------------|---------|-----------|
| 1️⃣ | data-testid | `getByTestId('submit')` | ⭐⭐⭐⭐⭐ |
| 2️⃣ | Role + Name | `getByRole('button', { name: 'Submit' })` | ⭐⭐⭐⭐ |
| 3️⃣ | Label | `getByLabel('Email')` | ⭐⭐⭐ |
| ❌ | CSS class | `.btn-primary` | ⭐ (BANNED) |
| ❌ | XPath | `//button[1]` | ⭐ (BANNED) |

### Common Actions

```typescript
// Click
await page.getByTestId('button').click();
await page.getByTestId('button').dblclick();

// Fill
await page.getByTestId('input').fill('value');
await page.getByTestId('input').clear();

// Select
await page.getByTestId('select').selectOption('value');
await page.getByTestId('select').selectOption({ label: 'Option Text' });

// Check
await page.getByTestId('checkbox').check();
await page.getByTestId('checkbox').uncheck();

// Hover
await page.getByTestId('menu').hover();

// Focus
await page.getByTestId('input').focus();

// Press key
await page.getByTestId('input').press('Enter');

// Upload file
await page.getByTestId('file-input').setInputFiles('path/to/file.pdf');
```

### Common Assertions

```typescript
// Visibility
await expect(locator).toBeVisible();
await expect(locator).not.toBeVisible();
await expect(locator).toBeHidden();

// Text
await expect(locator).toHaveText('exact text');
await expect(locator).toContainText('partial');

// Value
await expect(locator).toHaveValue('input value');

// State
await expect(locator).toBeEnabled();
await expect(locator).toBeDisabled();
await expect(locator).toBeChecked();
await expect(locator).toBeFocused();

// Count
await expect(locator).toHaveCount(5);

// Attribute
await expect(locator).toHaveAttribute('href', '/path');

// Page
await expect(page).toHaveURL('/path');
await expect(page).toHaveTitle('Title');
```

---

## REMEMBER

```
🎯 data-testid is your ONLY friend for selectors
⏱️ Let Playwright wait - never use setTimeout
🏠 Page Object Model keeps tests maintainable  
🔄 API setup, UI test - fast and reliable
🎭 Mock external services for determinism
```

**When in doubt: Is this test stable? Can it run 100 times without failing?**

If not, you're not done yet.
