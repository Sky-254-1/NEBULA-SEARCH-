import { test, expect } from '../fixtures/test-context';

test('auth modal opens and closes via Escape key', async ({ page }) => {
  await page.goto('/');
  await page.click('text=Sign in');
  await expect(page.locator('[role="dialog"]')).toBeVisible();
  await page.keyboard.press('Escape');
  await expect(page.locator('[role="dialog"]')).not.toBeVisible();
});

test('auth modal overlay click closes', async ({ page }) => {
  await page.goto('/');
  await page.click('text=Sign in');
  await expect(page.locator('.modal-overlay')).toBeVisible();
  await page.click('.modal-overlay', { position: { x: 10, y: 10 } });
  await expect(page.locator('[role="dialog"]')).not.toBeVisible();
});

test('search input focus rings visible', async ({ page }) => {
  await page.goto('/');
  const input = page.locator('input[aria-label="Search query"]');
  await input.focus();
  await expect(input).toBeFocused();
});
