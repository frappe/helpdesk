import { test, expect } from '@playwright/test';

test.describe('Home Page', () => {
  test('should load the home page', async ({ page }) => {
    await page.goto('/');

    // Check that the page loaded
    await expect(page).toHaveTitle(/helpdesk|support/i);
  });

  test('should have navigation menu', async ({ page }) => {
    await page.goto('/');

    // Check for navigation elements
    const nav = page.locator('nav, header').first();
    await expect(nav).toBeVisible();
  });

  test('should display logo or brand name', async ({ page }) => {
    await page.goto('/');

    // Look for logo or brand text
    const logo = page.locator('[alt*="logo"], h1, [role="banner"]').first();
    await expect(logo).toBeVisible();
  });

  test('should have accessible navigation', async ({ page }) => {
    await page.goto('/');

    // Check for links
    const links = page.getByRole('link');
    await expect(links.first()).toBeVisible();
  });

  test('should be responsive', async ({ page }) => {
    // Test mobile viewport
    await page.setViewportSize({ width: 375, height: 667 });
    await page.goto('/');

    // Page should still be visible and functional
    await expect(page.locator('body')).toBeVisible();

    // Test tablet viewport
    await page.setViewportSize({ width: 768, height: 1024 });
    await page.goto('/');

    await expect(page.locator('body')).toBeVisible();

    // Test desktop viewport
    await page.setViewportSize({ width: 1920, height: 1080 });
    await page.goto('/');

    await expect(page.locator('body')).toBeVisible();
  });

  test('should not have console errors', async ({ page }) => {
    const errors: string[] = [];

    page.on('console', (msg) => {
      if (msg.type() === 'error') {
        errors.push(msg.text());
      }
    });

    await page.goto('/');

    // Allow some time for any async errors
    await page.waitForTimeout(2000);

    // Filter out known harmless errors (like React dev warnings)
    const criticalErrors = errors.filter(
      (error) =>
        !error.includes('DevTools') &&
        !error.includes('Violation') &&
        !error.includes('Extension')
    );

    expect(criticalErrors).toHaveLength(0);
  });
});
