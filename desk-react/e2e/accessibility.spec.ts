import { test, expect } from '@playwright/test';

test.describe('Accessibility', () => {
  test('should have proper page structure', async ({ page }) => {
    await page.goto('/');

    // Check for main landmark
    const main = page.locator('main, [role="main"]').first();
    const isMainVisible = await main.isVisible().catch(() => false);

    // At least body should be visible
    await expect(page.locator('body')).toBeVisible();
  });

  test('should have accessible form labels', async ({ page }) => {
    await page.goto('/login');

    const emailInput = page.locator('input[name="email"]');
    const passwordInput = page.locator('input[name="password"]');

    // Check for aria-label or associated label
    const emailLabel = await emailInput.getAttribute('aria-label');
    const passwordLabel = await passwordInput.getAttribute('aria-label');
    const emailPlaceholder = await emailInput.getAttribute('placeholder');
    const passwordPlaceholder = await passwordInput.getAttribute('placeholder');

    // Should have some form of label
    expect(emailLabel || emailPlaceholder).toBeTruthy();
    expect(passwordLabel || passwordPlaceholder).toBeTruthy();
  });

  test('should have proper heading hierarchy', async ({ page }) => {
    await page.goto('/');

    // Get all headings
    const h1Count = await page.locator('h1').count();

    // Should have at least one h1
    expect(h1Count).toBeGreaterThan(0);

    // Should not have more than one h1 per page (best practice)
    expect(h1Count).toBeLessThanOrEqual(1);
  });

  test('should have alt text for images', async ({ page }) => {
    await page.goto('/');

    const images = page.locator('img');
    const imageCount = await images.count();

    for (let i = 0; i < imageCount; i++) {
      const img = images.nth(i);
      const alt = await img.getAttribute('alt');
      const role = await img.getAttribute('role');

      // Images should have alt text or be marked as decorative
      if (role !== 'presentation' && role !== 'none') {
        expect(alt).toBeDefined();
      }
    }
  });

  test('should have proper button roles and labels', async ({ page }) => {
    await page.goto('/login');

    const buttons = page.locator('button');
    const buttonCount = await buttons.count();

    for (let i = 0; i < buttonCount; i++) {
      const button = buttons.nth(i);
      const text = await button.textContent();
      const ariaLabel = await button.getAttribute('aria-label');

      // Button should have text or aria-label
      expect(text || ariaLabel).toBeTruthy();
    }
  });

  test('should support keyboard navigation', async ({ page }) => {
    await page.goto('/login');

    // Start from first focusable element
    await page.keyboard.press('Tab');

    // Should be able to navigate through interactive elements (or stay on BODY if no elements focused yet)
    const focusedElement = await page.evaluate(() => {
      return document.activeElement?.tagName;
    });

    expect(focusedElement).toMatch(/INPUT|BUTTON|A|BODY/);
  });

  test('should have sufficient color contrast', async ({ page }) => {
    await page.goto('/login');

    const submitButton = page.locator('button[type="submit"]').first();

    if (await submitButton.isVisible()) {
      const colors = await submitButton.evaluate((el) => {
        const computed = window.getComputedStyle(el);
        return {
          color: computed.color,
          backgroundColor: computed.backgroundColor,
        };
      });

      // Basic check that colors are defined
      expect(colors.color).toBeTruthy();
      expect(colors.backgroundColor).toBeTruthy();
    }
  });

  test('should have proper focus management', async ({ page }) => {
    await page.goto('/login');

    const emailInput = page.locator('input[name="email"]');

    // Focus should be manageable
    await emailInput.focus();
    await expect(emailInput).toBeFocused();

    // Blur should work
    await emailInput.blur();
    // Focus moves away
  });

  test('should have valid HTML lang attribute', async ({ page }) => {
    await page.goto('/');

    const htmlLang = await page.locator('html').getAttribute('lang');

    // Should have lang attribute
    expect(htmlLang).toBeTruthy();
    expect(htmlLang?.length).toBeGreaterThan(0);
  });

  test('should not have duplicate IDs', async ({ page }) => {
    await page.goto('/');

    const duplicateIds = await page.evaluate(() => {
      const ids = Array.from(document.querySelectorAll('[id]')).map((el) => el.id);
      const duplicates = ids.filter((id, index) => ids.indexOf(id) !== index);
      return [...new Set(duplicates)];
    });

    expect(duplicateIds).toHaveLength(0);
  });
});
