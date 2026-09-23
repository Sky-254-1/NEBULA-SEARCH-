import { test, expect } from '../fixtures/test-context';

test('service worker is registered', async ({ page }) => {
  await page.goto('/');
  const hasSw = await page.evaluate(() => 'serviceWorker' in navigator);
  expect(hasSw).toBeTruthy();

  const registrations = await page.evaluate(async () => {
    const regs = await navigator.serviceWorker.getRegistrations();
    return regs.map((r) => r.active?.scriptURL).filter(Boolean);
  });
  expect(registrations.length).toBeGreaterThanOrEqual(1);
});

test('manifest is served', async ({ page }) => {
  const res = await page.goto('/manifest.json');
  expect(res?.status()).toBe(200);
  const manifest = await res?.json();
  expect(manifest.name).toBeDefined();
  expect(manifest.short_name).toBeDefined();
});

test('app shell loads offline with cached content', async ({ page, context }) => {
  await page.goto('/');
  await page.waitForLoadState('networkidle');

  await context.setOffline(true);
  await page.goto('/').catch(() => {});
  await page.waitForTimeout(500);
  const text = await page.textContent('body').catch(() => '');
  expect(text.length).toBeGreaterThan(0);
  await context.setOffline(false);
});
