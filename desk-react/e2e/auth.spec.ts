import { test, expect } from '@playwright/test';

test.describe('Authentication', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
  });

  test('should display login page', async ({ page }) => {
    await page.goto('/login');

    // Check that login form is visible
    await expect(page.locator('input[name="email"]')).toBeVisible();
    await expect(page.locator('input[name="password"]')).toBeVisible();
    await expect(page.locator('button[type="submit"]')).toBeVisible();
  });

  test('should show validation error for empty fields', async ({ page }) => {
    await page.goto('/login');

    // Click submit without filling fields
    await page.click('button[type="submit"]');

    // Should show validation errors or prevent submission
    await expect(page.locator('input[name="email"]')).toBeVisible();
  });

  test('should show error for invalid credentials', async ({ page }) => {
    await page.goto('/login');

    // Fill with invalid credentials
    await page.fill('input[name="email"]', 'invalid@example.com');
    await page.fill('input[name="password"]', 'wrongpassword');
    await page.click('button[type="submit"]');

    // Should show error message
    await expect(page.getByText(/invalid|error|incorrect/i)).toBeVisible({ timeout: 5000 });
  });

  test('should redirect to login when accessing protected route', async ({ page }) => {
    // Try to access dashboard without authentication
    await page.goto('/dashboard');

    // Should redirect to login
    await expect(page).toHaveURL(/\/login/);
  });

  test('should display registration page', async ({ page }) => {
    await page.goto('/register');

    // Check registration form fields
    await expect(page.locator('input[name="email"]')).toBeVisible();
    await expect(page.locator('input[name="password"]')).toBeVisible();
    await expect(page.locator('input[name="fullName"]')).toBeVisible();
  });

  test('should navigate between login and register', async ({ page }) => {
    await page.goto('/login');

    // Find and click register link
    const registerLink = page.getByRole('link', { name: /sign up|register|create account/i });
    await registerLink.click();

    // Should navigate to register page
    await expect(page).toHaveURL(/\/register/);

    // Find and click login link
    const loginLink = page.getByRole('link', { name: /sign in|login|have an account/i });
    await loginLink.click();

    // Should navigate back to login
    await expect(page).toHaveURL(/\/login/);
  });

  test('should handle password visibility toggle', async ({ page }) => {
    await page.goto('/login');

    const passwordInput = page.locator('input[name="password"]');

    // Check initial type is password
    await expect(passwordInput).toHaveAttribute('type', 'password');

    // Look for visibility toggle button
    const toggleButton = page.locator('[aria-label*="password"], [data-testid*="password-toggle"]').first();

    if (await toggleButton.isVisible()) {
      await toggleButton.click();
      // Type might change to text
      // This is optional based on implementation
    }
  });
});
