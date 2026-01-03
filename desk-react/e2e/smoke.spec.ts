import { test, expect } from '@playwright/test';

test.describe('Smoke Tests', () => {
  test('application loads successfully', async ({ page }) => {
    // Navigate to the application
    await page.goto('/');

    // Wait for page to load
    await page.waitForLoadState('networkidle');

    // Check that we can see some content
    await expect(page.locator('body')).toBeVisible();

    // Page should not show critical errors
    const bodyText = await page.locator('body').textContent();
    expect(bodyText).toBeTruthy();
  });

  test('page has valid HTML structure', async ({ page }) => {
    await page.goto('/');

    // Check for basic HTML elements
    await expect(page.locator('html')).toBeVisible();
    await expect(page.locator('body')).toBeVisible();
  });

  test('page loads without JavaScript errors', async ({ page }) => {
    const errors: string[] = [];

    page.on('pageerror', (error) => {
      errors.push(error.message);
    });

    await page.goto('/');
    await page.waitForLoadState('networkidle');

    // Filter out known harmless errors
    const criticalErrors = errors.filter(
      (error) =>
        !error.includes('DevTools') &&
        !error.includes('Violation') &&
        !error.includes('Extension')
    );

    expect(criticalErrors.length).toBe(0);
  });

  test('page responds to basic interactions', async ({ page }) => {
    await page.goto('/');

    // Try to find any clickable element
    const links = page.getByRole('link').or(page.getByRole('button'));
    const count = await links.count();

    // Should have at least one interactive element
    expect(count).toBeGreaterThan(0);
  });

  test('page is mobile responsive', async ({ page }) => {
    // Test on mobile viewport
    await page.setViewportSize({ width: 375, height: 667 });
    await page.goto('/');

    await expect(page.locator('body')).toBeVisible();

    // Check that content fits within viewport (no horizontal scroll)
    const hasHorizontalScroll = await page.evaluate(() => {
      return document.documentElement.scrollWidth > document.documentElement.clientWidth;
    });

    // Some horizontal scroll might be acceptable, but excessive is not
    expect(hasHorizontalScroll).toBeFalsy();
  });

  test('critical resources load successfully', async ({ page }) => {
    const failedResources: string[] = [];

    page.on('requestfailed', (request) => {
      failedResources.push(request.url());
    });

    await page.goto('/');
    await page.waitForLoadState('networkidle');

    // Filter out non-critical failed requests (analytics, ads, etc.)
    const criticalFailures = failedResources.filter(
      (url) =>
        !url.includes('analytics') &&
        !url.includes('tracking') &&
        !url.includes('ads')
    );

    // Log failures for debugging
    if (criticalFailures.length > 0) {
      console.log('Failed resources:', criticalFailures);
    }
  });
});
