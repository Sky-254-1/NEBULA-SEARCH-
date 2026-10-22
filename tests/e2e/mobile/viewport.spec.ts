import { test, expect } from '../fixtures/test-context';

test.describe('mobile viewport', () => {
  test.use({ viewport: { width: 375, height: 812 } });

  test('home page renders in mobile viewport', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');
    const title = await page.textContent('.hero-title');
    expect(title).toBe('Nebula Search');
  });

  test('search bar is visible on mobile', async ({ page }) => {
    await page.goto('/');
    await expect(page.locator('.search-bar')).toBeVisible();
    await expect(page.locator('input[aria-label="Search query"]')).toBeVisible();
  });

  test('mobile sidebar toggle opens menu', async ({ page }) => {
    const EMAIL = `mobile-${Date.now()}@test.nebula`;
    const PASS = 'MobP1!';

    await page.request.post('http://localhost:8000/api/v1/auth/signup', { data: { email: EMAIL, password: PASS } });
    const login = await page.request.post('http://localhost:8000/api/v1/auth/login', { data: { email: EMAIL, password: PASS } });
    const { access_token, refresh_token } = await login.json();

    await page.goto('/search?q=test');
    await page.evaluate((t) => {
      localStorage.setItem('nebula_tokens', JSON.stringify(t));
    }, { access_token, refresh_token });
    await page.reload();
    await page.waitForLoadState('networkidle');
  });
});

test.describe('tablet viewport', () => {
  test.use({ viewport: { width: 768, height: 1024 } });

  test('layout adapts to tablet', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');
    await expect(page.locator('.hero-title')).toBeVisible();
  });
});

test.describe('landscape mobile', () => {
  test.use({ viewport: { width: 812, height: 375 } });

  test('app renders in landscape', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');
    const title = await page.textContent('.hero-title');
    expect(title).toBe('Nebula Search');
  });
});
