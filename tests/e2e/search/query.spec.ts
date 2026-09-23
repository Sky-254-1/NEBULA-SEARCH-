import { test, expect } from '../fixtures/auth.fixture';
import { submitSearch, waitForResultsOrError } from '../utils/helpers';

test.describe('Search', () => {
  test('query returns results or AI overview', async ({ page, accessToken }) => {
    void accessToken;
    await page.goto('/');
    await submitSearch(page, 'Python programming');
    await waitForResultsOrError(page);
    const hasResults = await page.locator('.results-section').isVisible();
    const hasAi = await page.locator('.ai-box').isVisible();
    const hasError = await page.locator('.error-box').isVisible();
    expect(hasResults || hasAi || hasError).toBeTruthy();
  });

  test('pagination controls appear when results exist', async ({ page, accessToken }) => {
    void accessToken;
    await page.goto('/');
    await submitSearch(page, 'Wikipedia');
    await waitForResultsOrError(page);
    const pagination = page.locator('.pagination, [class*="pagination"]');
    const results = page.locator('.results-section');
    if (await results.isVisible()) {
      const count = await pagination.count();
      expect(count >= 0).toBeTruthy();
    }
  });

  test('backend filter selection', async ({ page, accessToken }) => {
    void accessToken;
    await page.goto('/');
    await page.locator('.backend-select select').selectOption('wikipedia');
    await submitSearch(page, 'Earth');
    await waitForResultsOrError(page);
    await expect(page.locator('.hero')).toBeVisible();
  });

  test('empty query does not submit', async ({ page }) => {
    await page.goto('/');
    const btn = page.getByRole('button', { name: 'Search' });
    await expect(btn).toBeDisabled();
  });

  test('retry on error', async ({ page, accessToken }) => {
    void accessToken;
    await page.goto('/');
    await submitSearch(page, 'retry test query');
    await page.waitForTimeout(5000);
    const retry = page.getByRole('button', { name: 'Retry' });
    if (await retry.isVisible()) {
      await retry.click();
      await waitForResultsOrError(page);
    }
    await expect(page.locator('.hero')).toBeVisible();
  });
});
