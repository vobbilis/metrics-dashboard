# Data-TestId Catalog & Naming Standards

This document defines the canonical naming conventions for `data-testid` attributes. Use this as a reference when requesting testIds from frontend developers or when writing tests.

---

## Naming Convention

```
data-testid="{context}-{element}-{type}"
```

**Format:**
- **context**: Feature/section name (kebab-case)
- **element**: What the element represents (kebab-case)
- **type**: Element type suffix (from standard list)

**Examples:**
```
login-email-input
user-profile-avatar
checkout-submit-button
orders-data-table
settings-theme-toggle
```

---

## Standard Type Suffixes

| Suffix | Element Type | HTML/Component |
|--------|--------------|----------------|
| `-input` | Text input, textarea | `<input type="text">`, `<textarea>` |
| `-password` | Password field | `<input type="password">` |
| `-email` | Email field | `<input type="email">` |
| `-number` | Number input | `<input type="number">` |
| `-button` | Clickable button | `<button>`, `<Button>` |
| `-link` | Navigation link | `<a>`, `<Link>` |
| `-checkbox` | Checkbox | `<input type="checkbox">` |
| `-radio` | Radio button | `<input type="radio">` |
| `-select` | Dropdown select | `<select>`, custom dropdown |
| `-option` | Dropdown option | `<option>`, menu item |
| `-toggle` | Toggle switch | Switch component |
| `-form` | Form container | `<form>` |
| `-modal` | Modal/dialog | Dialog component |
| `-table` | Data table | `<table>`, DataGrid |
| `-row` | Table row | `<tr>`, row component |
| `-cell` | Table cell | `<td>`, cell component |
| `-list` | List container | `<ul>`, `<ol>` |
| `-item` | List item | `<li>`, list item component |
| `-card` | Card component | Card container |
| `-section` | Page section | `<section>`, container |
| `-header` | Header area | `<header>`, page header |
| `-footer` | Footer area | `<footer>`, page footer |
| `-sidebar` | Sidebar navigation | Sidebar component |
| `-nav` | Navigation container | `<nav>` |
| `-menu` | Menu container | Menu component |
| `-tab` | Tab button | Tab component |
| `-panel` | Tab panel content | TabPanel component |
| `-alert` | Alert message | Alert component |
| `-error` | Error message | Error text |
| `-success` | Success message | Success indicator |
| `-loading` | Loading indicator | Spinner, skeleton |
| `-avatar` | User avatar | Avatar component |
| `-badge` | Badge/chip | Badge component |
| `-tooltip` | Tooltip content | Tooltip component |
| `-icon` | Icon element | Icon component |
| `-image` | Image | `<img>` |
| `-video` | Video player | `<video>` |
| `-text` | Text display | Static text element |
| `-label` | Form label | `<label>` |
| `-heading` | Heading | `<h1>`-`<h6>` |
| `-container` | Generic container | `<div>` wrapper |
| `-wrapper` | Outer wrapper | Top-level wrapper |
| `-trigger` | Dropdown/modal trigger | Trigger button |
| `-content` | Content area | Main content |
| `-actions` | Action buttons area | Button group |
| `-empty` | Empty state | No data state |
| `-skeleton` | Loading skeleton | Skeleton placeholder |

---

## Context-Based Catalog

### Authentication

```typescript
// Login Page
data-testid="login-email-input"
data-testid="login-password-input"
data-testid="login-submit-button"
data-testid="login-forgot-link"
data-testid="login-register-link"
data-testid="login-error-alert"
data-testid="login-form"
data-testid="login-remember-checkbox"
data-testid="login-loading-indicator"

// Register Page
data-testid="register-email-input"
data-testid="register-password-input"
data-testid="register-confirm-input"
data-testid="register-name-input"
data-testid="register-submit-button"
data-testid="register-terms-checkbox"
data-testid="register-form"

// Password Reset
data-testid="reset-email-input"
data-testid="reset-submit-button"
data-testid="reset-back-link"
data-testid="reset-success-alert"
```

### Navigation

```typescript
// Global Header
data-testid="header-container"
data-testid="header-logo-link"
data-testid="header-search-input"
data-testid="header-search-button"
data-testid="header-user-menu-trigger"
data-testid="header-user-avatar"
data-testid="header-notification-button"
data-testid="header-notification-badge"
data-testid="header-logout-button"
data-testid="header-profile-link"
data-testid="header-settings-link"

// Sidebar
data-testid="sidebar-container"
data-testid="sidebar-dashboard-link"
data-testid="sidebar-users-link"
data-testid="sidebar-orders-link"
data-testid="sidebar-settings-link"
data-testid="sidebar-collapse-button"

// Breadcrumbs
data-testid="breadcrumb-container"
data-testid="breadcrumb-home-link"
data-testid="breadcrumb-current-text"
```

### Dashboard

```typescript
data-testid="dashboard-container"
data-testid="dashboard-welcome-heading"
data-testid="dashboard-stats-section"
data-testid="dashboard-revenue-card"
data-testid="dashboard-users-card"
data-testid="dashboard-orders-card"
data-testid="dashboard-chart-section"
data-testid="dashboard-activity-list"
data-testid="dashboard-activity-item"
```

### User Management

```typescript
// User List
data-testid="users-table"
data-testid="users-row"
data-testid="users-name-cell"
data-testid="users-email-cell"
data-testid="users-role-cell"
data-testid="users-status-cell"
data-testid="users-actions-cell"
data-testid="users-edit-button"
data-testid="users-delete-button"
data-testid="users-add-button"
data-testid="users-search-input"
data-testid="users-filter-select"
data-testid="users-empty-state"
data-testid="users-loading-skeleton"
data-testid="users-pagination"

// User Form
data-testid="user-form"
data-testid="user-name-input"
data-testid="user-email-input"
data-testid="user-role-select"
data-testid="user-status-toggle"
data-testid="user-avatar-upload"
data-testid="user-save-button"
data-testid="user-cancel-button"
data-testid="user-delete-button"

// User Profile
data-testid="profile-avatar"
data-testid="profile-name-text"
data-testid="profile-email-text"
data-testid="profile-role-badge"
data-testid="profile-edit-button"
data-testid="profile-activity-section"
```

### Orders / Transactions

```typescript
// Order List
data-testid="orders-table"
data-testid="orders-row"
data-testid="orders-id-cell"
data-testid="orders-date-cell"
data-testid="orders-status-badge"
data-testid="orders-total-cell"
data-testid="orders-view-button"
data-testid="orders-filter-status-select"
data-testid="orders-filter-date-input"
data-testid="orders-search-input"
data-testid="orders-export-button"

// Order Details
data-testid="order-details-container"
data-testid="order-id-text"
data-testid="order-status-badge"
data-testid="order-customer-section"
data-testid="order-items-table"
data-testid="order-item-row"
data-testid="order-subtotal-text"
data-testid="order-tax-text"
data-testid="order-total-text"
data-testid="order-cancel-button"
data-testid="order-refund-button"
```

### Forms (Generic)

```typescript
// Common Form Patterns
data-testid="{feature}-form"
data-testid="{feature}-{field}-input"
data-testid="{feature}-{field}-error"
data-testid="{feature}-{field}-helper"
data-testid="{feature}-submit-button"
data-testid="{feature}-cancel-button"
data-testid="{feature}-reset-button"
data-testid="{feature}-success-alert"
data-testid="{feature}-error-alert"
```

### Modals / Dialogs

```typescript
// Generic Modal Pattern
data-testid="{purpose}-modal"
data-testid="{purpose}-modal-header"
data-testid="{purpose}-modal-title"
data-testid="{purpose}-modal-close-button"
data-testid="{purpose}-modal-content"
data-testid="{purpose}-modal-footer"
data-testid="{purpose}-modal-confirm-button"
data-testid="{purpose}-modal-cancel-button"

// Examples
data-testid="delete-confirm-modal"
data-testid="delete-confirm-modal-confirm-button"
data-testid="edit-user-modal"
data-testid="create-order-modal"
```

### Data Tables

```typescript
// Table Components
data-testid="{entity}-table"
data-testid="{entity}-table-header"
data-testid="{entity}-table-body"
data-testid="{entity}-row"  // Also add data-row-id="{id}"
data-testid="{entity}-{column}-header"
data-testid="{entity}-{column}-cell"
data-testid="{entity}-select-checkbox"
data-testid="{entity}-select-all-checkbox"
data-testid="{entity}-sort-{column}-button"
data-testid="{entity}-action-{action}-button"
data-testid="{entity}-empty-state"
data-testid="{entity}-loading-skeleton"
data-testid="{entity}-pagination"
data-testid="{entity}-page-size-select"
data-testid="{entity}-page-{n}-button"
data-testid="{entity}-prev-page-button"
data-testid="{entity}-next-page-button"
```

### Notifications / Alerts

```typescript
data-testid="toast-container"
data-testid="toast-{type}-alert"  // success, error, warning, info
data-testid="toast-message-text"
data-testid="toast-close-button"
data-testid="notification-bell-button"
data-testid="notification-badge"
data-testid="notification-dropdown"
data-testid="notification-item"
data-testid="notification-mark-read-button"
data-testid="notification-clear-all-button"
```

---

## Dynamic TestIds

For repeated elements, add dynamic identifiers:

```typescript
// Lists/Tables - Use index or unique ID
data-testid="users-row"         // Generic (nth selector needed)
data-testid="users-row-123"     // With ID (preferred)

// In React:
<tr data-testid={`users-row-${user.id}`}>

// In test:
await page.getByTestId('users-row-123').click();
// Or
await page.getByTestId('users-row').filter({ hasText: 'John Doe' }).click();
```

---

## Requesting TestIds from Frontend

### Template Message

```markdown
## TestId Request for [Feature Name]

We need the following data-testid attributes added for E2E testing:

### Page: [Page Name]

| Element | TestId | Purpose |
|---------|--------|---------|
| Email input | `login-email-input` | Enter user email |
| Password input | `login-password-input` | Enter password |
| Submit button | `login-submit-button` | Submit login form |
| Error message | `login-error-alert` | Display login errors |

### Naming Convention
- Format: `{context}-{element}-{type}`
- Use kebab-case
- See full catalog: [link to this document]

### Priority: [High/Medium/Low]
### Target Sprint: [Sprint X]
```

---

## Anti-Patterns to Avoid

### ❌ Generic Names
```typescript
// Bad
data-testid="button"
data-testid="input"
data-testid="modal"

// Good
data-testid="login-submit-button"
data-testid="user-email-input"
data-testid="delete-confirm-modal"
```

### ❌ Implementation Details
```typescript
// Bad - Exposes internal structure
data-testid="mui-button-123"
data-testid="styled-div-wrapper"
data-testid="react-query-loader"

// Good - Describes purpose
data-testid="checkout-submit-button"
data-testid="user-profile-container"
data-testid="orders-loading-indicator"
```

### ❌ Positional Names
```typescript
// Bad - Fragile if order changes
data-testid="first-button"
data-testid="second-input"
data-testid="top-section"

// Good - Semantic meaning
data-testid="profile-primary-action-button"
data-testid="settings-backup-email-input"
data-testid="dashboard-stats-section"
```

### ❌ Duplicate Names
```typescript
// Bad - Can't distinguish elements
<Button data-testid="save-button">Save</Button>
<Button data-testid="save-button">Save Draft</Button>

// Good - Unique identifiers
<Button data-testid="profile-save-button">Save</Button>
<Button data-testid="profile-save-draft-button">Save Draft</Button>
```
