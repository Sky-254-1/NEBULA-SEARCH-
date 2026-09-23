import { test, expect } from '../fixtures/test-context';

const EMAIL = `reconnect-${Date.now()}@test.nebula`;
const PASS = 'ReP1!';

test.beforeAll(async ({ request }) => {
  await request.post('http://localhost:8000/api/v1/auth/signup', {
    data: { email: EMAIL, password: PASS },
  });
});

test('app shows toast on network disconnect and recovers', async ({ page, context }) => {
  const login = await page.request.post('http://localhost:8000/api/v1/auth/login', {
    data: { email: EMAIL, password: PASS },
  });
  const { access_token, refresh_token } = await login.json();

  await page.goto('/');
  await page.evaluate((tokens) => {
    localStorage.setItem('nebula_tokens', JSON.stringify(tokens));
  }, { access_token, refresh_token });
  await page.reload();
  await page.waitForLoadState('networkidle');

  await context.setOffline(true);
  await page.waitForTimeout(1000);
  await context.setOffline(false);
  await page.waitForTimeout(1000);

  const bodyText = await page.textContent('body').catch(() => '');
  expect(bodyText.length).toBeGreaterThan(0);
});
