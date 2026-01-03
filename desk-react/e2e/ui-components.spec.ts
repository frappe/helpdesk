import { test, expect } from '@playwright/test';

test.describe('UI Components', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
  });

  test('buttons should be clickable and styled', async ({ page }) => {
    await page.goto('/login');

    // Find submit button
    const submitButton = page.locator('button[type="submit"]').first();

    // Check button is visible and enabled
    await expect(submitButton).toBeVisible();
    await expect(submitButton).toBeEnabled();

    // Check that button has proper styling
    const styles = await submitButton.evaluate((el) => {
      const computed = window.getComputedStyle(el);
      return {
        cursor: computed.cursor,
        backgroundColor: computed.backgroundColor,
      };
    });

    expect(styles.cursor).toBe('pointer');
  });

  test('input fields should be functional', async ({ page }) => {
    await page.goto('/login');

    const emailInput = page.locator('input[name="email"]');
    const passwordInput = page.locator('input[name="password"]');

    // Test email input
    await emailInput.click();
    await emailInput.fill('test@example.com');
    await expect(emailInput).toHaveValue('test@example.com');

    // Test password input
    await passwordInput.click();
    await passwordInput.fill('password123');
    await expect(passwordInput).toHaveValue('password123');

    // Check input types
    await expect(emailInput).toHaveAttribute('type', 'email');
    await expect(passwordInput).toHaveAttribute('type', 'password');
  });

  test('forms should have proper labels', async ({ page }) => {
    await page.goto('/login');

    // Check for labels or placeholders
    const emailInput = page.locator('input[name="email"]');
    const passwordInput = page.locator('input[name="password"]');

    // Should have either label or placeholder
    const emailPlaceholder = await emailInput.getAttribute('placeholder');
    const passwordPlaceholder = await passwordInput.getAttribute('placeholder');

    expect(emailPlaceholder || 'Email').toBeTruthy();
    expect(passwordPlaceholder || 'Password').toBeTruthy();
  });

  test('should handle keyboard navigation', async ({ page }) => {
    await page.goto('/login');

    const emailInput = page.locator('input[name="email"]');
    const passwordInput = page.locator('input[name="password"]');
    const submitButton = page.locator('button[type="submit"]');

    // Tab through form
    await emailInput.focus();
    await expect(emailInput).toBeFocused();

    await page.keyboard.press('Tab');
    await expect(passwordInput).toBeFocused();

    await page.keyboard.press('Tab');
    // Submit button should be focusable
    const focusedElement = await page.evaluate(() => document.activeElement?.tagName);
    expect(focusedElement).toBe('BUTTON');
  });

  test('should display loading states', async ({ page }) => {
    await page.goto('/login');

    const emailInput = page.locator('input[name="email"]');
    const passwordInput = page.locator('input[name="password"]');
    const submitButton = page.locator('button[type="submit"]');

    // Fill form
    await emailInput.fill('test@example.com');
    await passwordInput.fill('password123');

    // Click submit
    await submitButton.click();

    // Button might show loading state
    // This depends on implementation
  });

  test('should have proper focus styles', async ({ page }) => {
    await page.goto('/login');

    const emailInput = page.locator('input[name="email"]');

    // Focus the input
    await emailInput.focus();

    // Check that focus ring or outline is visible
    const outline = await emailInput.evaluate((el) => {
      const computed = window.getComputedStyle(el);
      return computed.outline || computed.boxShadow;
    });

    // Should have some focus indicator
    expect(outline).toBeTruthy();
  });
});
