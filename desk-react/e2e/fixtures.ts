import { test as base, expect } from '@playwright/test';

// Extend basic test with custom fixtures
export const test = base.extend({
  // Add authenticated page fixture
  authenticatedPage: async ({ page }, use) => {
    // Navigate to login page
    await page.goto('/login');

    // Perform login
    await page.fill('input[name="email"]', 'test@example.com');
    await page.fill('input[name="password"]', 'password123');
    await page.click('button[type="submit"]');

    // Wait for navigation after login
    await page.waitForURL('**/dashboard', { timeout: 10000 });

    // Use the authenticated page
    await use(page);
  },
});

export { expect };
