import { test, expect } from '../fixtures/test-context';

test('frontend dev server responds and renders app', async ({ page }) => {
  await page.goto('http://localhost:5173/');
  await expect(page).toHaveTitle(/Nebula/);
  await expect(page.locator('#root')).not.toBeEmpty();
});

test('frontend loads JavaScript modules', async ({ page }) => {
  const consoleErrors: string[] = [];
  page.on('console', (msg) => {
    if (msg.type() === 'error') consoleErrors.push(msg.text());
  });

  await page.goto('http://localhost:5173/');
  await page.waitForLoadState('networkidle');

  expect(consoleErrors.filter(e => e.includes('[SECURITY] BLOCKED'))).toEqual([]);
  expect(consoleErrors.filter(e => e.includes('TypeError'))).toEqual([]);
});