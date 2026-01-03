import { test, expect } from '@playwright/test';

test('debug console errors', async ({ page }) => {
  const consoleMessages: string[] = [];
  const consoleErrors: string[] = [];

  page.on('console', msg => {
    const text = `${msg.type()}: ${msg.text()}`;
    consoleMessages.push(text);
    if (msg.type() === 'error') {
      consoleErrors.push(text);
    }
  });

  page.on('pageerror', error => {
    consoleErrors.push(`PageError: ${error.message}`);
  });

  await page.goto('http://localhost:8080');

  // Wait a bit for any errors to appear
  await page.waitForTimeout(3000);

  console.log('\n=== All Console Messages ===');
  consoleMessages.forEach(msg => console.log(msg));

  console.log('\n=== Console Errors ===');
  consoleErrors.forEach(err => console.log(err));

  // Check the HTML
  const html = await page.content();
  console.log('\n=== Page HTML (first 500 chars) ===');
  console.log(html.substring(0, 500));

  // Check if root div exists and its visibility
  const rootExists = await page.locator('#root').count();
  console.log(`\n=== Root div exists: ${rootExists > 0} ===`);

  if (rootExists > 0) {
    const rootHTML = await page.locator('#root').innerHTML();
    console.log(`Root innerHTML length: ${rootHTML.length}`);
    console.log('Root HTML:', rootHTML.substring(0, 200));
  }
});
