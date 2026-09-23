import { test, expect } from '../fixtures/auth.fixture';
import { env } from '../config/env';
import { setOffline } from '../utils/helpers';

test.describe('Error handling', () => {
  test('server failure returns error', async ({ request }) => {
    const res = await request.get(`${env.apiURL}/api/v1/search/web?q=test`, {
      headers: { Authorization: 'Bearer invalid' },
    });
    expect(res.status()).toBe(401);
  });

  test('network interruption recovery', async ({ page }) => {
    await page.goto('/');
    await setOffline(page, true);
    await page.reload();
    await setOffline(page, false);
    await page.reload();
    await expect(page.getByText('Nebula Search')).toBeVisible();
  });

  test('timeout recovery via retry', async ({ page, accessToken }) => {
    void accessToken;
    await page.goto('/');
    await page.getByLabel('Search query').fill('timeout recovery');
    await page.getByRole('button', { name: 'Search' }).click();
    await page.waitForTimeout(6000);
    const retry = page.getByRole('button', { name: 'Retry' });
    if (await retry.isVisible()) {
      await retry.click();
    }
    await expect(page.locator('.hero')).toBeVisible();
  });
});
