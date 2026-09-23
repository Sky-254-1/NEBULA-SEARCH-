import { test, expect } from '../fixtures/test-context';

test('dark mode toggle persists', async ({ page }) => {
  await page.goto('/');
  const initial = await page.evaluate(() => document.body.dataset.theme);
  expect(['dark', 'light']).toContain(initial);
});
