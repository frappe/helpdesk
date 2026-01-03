# End-to-End Tests with Playwright

This directory contains end-to-end tests for the Helpdesk React application using Playwright.

## Test Suites

### 1. Smoke Tests (`smoke.spec.ts`)
Basic tests to ensure the application loads and functions correctly:
- Application loads successfully
- Valid HTML structure
- No JavaScript errors
- Mobile responsiveness
- Critical resources load

### 2. Authentication Tests (`auth.spec.ts`)
Tests for user authentication flows:
- Login page display
- Form validation
- Invalid credentials handling
- Protected route redirection
- Registration page
- Navigation between login/register
- Password visibility toggle

### 3. Home Page Tests (`home.spec.ts`)
Tests for the home page:
- Page loading
- Navigation menu
- Logo/brand display
- Responsive design
- Console error checking

### 4. UI Components Tests (`ui-components.spec.ts`)
Tests for UI component functionality:
- Button interactions
- Input field functionality
- Form labels
- Keyboard navigation
- Loading states
- Focus styles

### 5. Accessibility Tests (`accessibility.spec.ts`)
Tests for accessibility compliance:
- Page structure
- Form labels
- Heading hierarchy
- Image alt text
- Button roles and labels
- Keyboard navigation
- Color contrast
- Focus management
- HTML lang attribute
- No duplicate IDs

## Running Tests

### Run all E2E tests
```bash
npm run test:e2e
```

### Run with UI mode (interactive)
```bash
npm run test:e2e:ui
```

### Run in debug mode
```bash
npm run test:e2e:debug
```

### View test report
```bash
npm run test:e2e:report
```

### Run specific test file
```bash
npx playwright test e2e/smoke.spec.ts
```

### Run tests in headed mode (see browser)
```bash
npx playwright test --headed
```

## Requirements

- Node.js and npm installed
- Playwright browsers installed (run `npx playwright install` if needed)
- Development server running on port 5173 (or configure in `playwright.config.ts`)

## Configuration

Test configuration is in `playwright.config.ts`. Key settings:
- **baseURL**: `http://localhost:5173`
- **Browser**: Chromium
- **Timeout**: 30 seconds per test
- **Retries**: 2 on CI, 0 locally
- **Screenshots**: On failure
- **Video**: On failure
- **Trace**: On first retry

## CI/CD Integration

Tests are configured to run in CI environments with:
- Automatic dev server startup
- Increased timeouts
- Test retries
- Artifact collection (screenshots, videos, traces)

## Best Practices

1. **Test User Flows**: Focus on testing complete user workflows
2. **Use Selectors Wisely**: Prefer role-based and accessible selectors
3. **Wait Properly**: Use Playwright's auto-waiting features
4. **Keep Tests Independent**: Each test should be able to run standalone
5. **Use Fixtures**: Leverage fixtures for common setup (auth, data)
6. **Mobile Testing**: Test responsive designs at different viewports
7. **Accessibility**: Include accessibility checks in tests

## Debugging

### Visual debugging
```bash
npm run test:e2e:debug
```

### Trace viewer
When a test fails, view the trace:
```bash
npx playwright show-trace trace.zip
```

### Screenshots and videos
Failed tests automatically capture screenshots and videos in:
- `test-results/` - Test artifacts
- `playwright-report/` - HTML report

## Writing New Tests

Create a new file in `e2e/` with `.spec.ts` extension:

```typescript
import { test, expect } from '@playwright/test';

test.describe('Feature Name', () => {
  test('should do something', async ({ page }) => {
    await page.goto('/path');
    await expect(page.locator('selector')).toBeVisible();
  });
});
```

For authenticated tests, use the fixture:
```typescript
import { test, expect } from './fixtures';

test('protected feature', async ({ authenticatedPage }) => {
  await expect(authenticatedPage).toHaveURL(/dashboard/);
});
```
