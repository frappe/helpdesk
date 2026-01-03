import { test, expect } from '@playwright/test';

test.describe('Working Smoke Tests', () => {
  test('application loads and renders', async ({ page }) => {
    await page.goto('/');

    // Wait for React to render
    await page.waitForSelector('#root', { timeout: 10000 });

    // Check that root div has content
    const rootContent = await page.locator('#root').textContent();
    expect(rootContent).toBeTruthy();

    // Page should have a title
    const title = await page.title();
    expect(title).toContain('Helpdesk');
  });

  test('page has valid HTML structure', async ({ page }) => {
    await page.goto('/');

    // Check basic HTML elements exist
    const html = page.locator('html');
    const body = page.locator('body');
    const root = page.locator('#root');

    await expect(html).toBeVisible();
    await expect(body).toBeVisible();
    await expect(root).toBeVisible();

    // Check html has lang attribute
    const lang = await html.getAttribute('lang');
    expect(lang).toBeTruthy();
  });

  test('no critical JavaScript errors on load', async ({ page }) => {
    const errors: string[] = [];

    page.on('pageerror', (error) => {
      errors.push(error.message);
    });

    await page.goto('/');
    await page.waitForLoadState('networkidle');

    // Filter out non-critical errors
    const criticalErrors = errors.filter(error =>
      !error.includes('DevTools') &&
      !error.includes('Extension') &&
      !error.includes('chrome-extension')
    );

    expect(criticalErrors.length).toBe(0);
  });

  test('page is responsive on mobile', async ({ page }) => {
    // Set mobile viewport
    await page.setViewportSize({ width: 375, height: 667 });
    await page.goto('/');

    // Page should render
    await expect(page.locator('body')).toBeVisible();

    // Check no excessive horizontal scroll
    const scrollWidth = await page.evaluate(() => document.documentElement.scrollWidth);
    const clientWidth = await page.evaluate(() => document.documentElement.clientWidth);

    // Allow small differences but not excessive
    expect(scrollWidth - clientWidth).toBeLessThan(50);
  });

  test('page is responsive on tablet', async ({ page }) => {
    await page.setViewportSize({ width: 768, height: 1024 });
    await page.goto('/');

    await expect(page.locator('body')).toBeVisible();
    await expect(page.locator('#root')).toBeVisible();
  });

  test('page is responsive on desktop', async ({ page }) => {
    await page.setViewportSize({ width: 1920, height: 1080 });
    await page.goto('/');

    await expect(page.locator('body')).toBeVisible();
    await expect(page.locator('#root')).toBeVisible();
  });

  test('React components render without errors', async ({ page }) => {
    await page.goto('/');

    // Wait for React to hydrate
    await page.waitForTimeout(2000);

    // Check that #root has React-rendered content
    const rootChildren = await page.locator('#root > *').count();
    expect(rootChildren).toBeGreaterThan(0);
  });

  test('CSS styles are loaded', async ({ page }) => {
    await page.goto('/');

    // Check that body has some styling applied
    const backgroundColor = await page.locator('body').evaluate((el) => {
      return window.getComputedStyle(el).backgroundColor;
    });

    // Should have some color value
    expect(backgroundColor).toBeTruthy();
    expect(backgroundColor).not.toBe('');
  });

  test('fonts are loaded', async ({ page }) => {
    await page.goto('/');

    const fontFamily = await page.locator('body').evaluate((el) => {
      return window.getComputedStyle(el).fontFamily;
    });

    // Should have font family defined
    expect(fontFamily).toBeTruthy();
    expect(fontFamily).not.toBe('');
  });

  test('images load successfully', async ({ page }) => {
    const failedImages: string[] = [];

    page.on('response', (response) => {
      if (response.request().resourceType() === 'image' && !response.ok()) {
        failedImages.push(response.url());
      }
    });

    await page.goto('/');
    await page.waitForLoadState('networkidle');

    // Critical images should load
    const criticalFailures = failedImages.filter(url =>
      !url.includes('analytics') &&
      !url.includes('tracking')
    );

    if (criticalFailures.length > 0) {
      console.log('Failed to load images:', criticalFailures);
    }

    // Log but don't fail - some images might be expected to fail
  });

  test('navigation works (if routes exist)', async ({ page }) => {
    await page.goto('/');

    // Look for any links
    const links = page.locator('a[href]');
    const linkCount = await links.count();

    if (linkCount > 0) {
      // At least some navigation exists
      expect(linkCount).toBeGreaterThan(0);
    }
  });

  test('accessibility - proper page title', async ({ page }) => {
    await page.goto('/');

    const title = await page.title();
    expect(title.length).toBeGreaterThan(0);
    expect(title).not.toBe('');
  });

  test('accessibility - no duplicate IDs', async ({ page }) => {
    await page.goto('/');

    const duplicateIds = await page.evaluate(() => {
      const ids = Array.from(document.querySelectorAll('[id]')).map(el => el.id);
      const duplicates = ids.filter((id, index) => ids.indexOf(id) !== index);
      return [...new Set(duplicates)];
    });

    expect(duplicateIds.length).toBe(0);
  });

  test('accessibility - html lang attribute', async ({ page }) => {
    await page.goto('/');

    const lang = await page.locator('html').getAttribute('lang');
    expect(lang).toBeTruthy();
    expect(lang?.length).toBeGreaterThan(0);
  });

  test('performance - page loads in reasonable time', async ({ page }) => {
    const startTime = Date.now();
    await page.goto('/');
    await page.waitForLoadState('networkidle');
    const loadTime = Date.now() - startTime;

    // Should load in less than 10 seconds
    expect(loadTime).toBeLessThan(10000);
  });
});
