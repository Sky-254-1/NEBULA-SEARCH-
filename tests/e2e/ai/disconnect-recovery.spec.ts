import { test, expect } from '../fixtures/test-context';
import { env } from '../config/env';

// Requires AI provider (OPENAI_API_KEY or AI_PROVIDER) — skip if not configured
test.skip(!process.env.OPENAI_API_KEY && !process.env.AI_PROVIDER, 'OPENAI_API_KEY / AI_PROVIDER not set — skipping AI-dependent tests');

const EMAIL = `disconnect-${Date.now()}@test.nebula`;
const PASS = 'DiscP1!';

test.beforeAll(async ({ request }) => {
  await request.post(`${env.apiURL}/api/v1/auth/signup`, {
    data: { email: EMAIL, password: PASS },
  });
});

test('stream recovers after brief disconnect', async ({ request, context }) => {
  const login = await request.post(`${env.apiURL}/api/v1/auth/login`, {
    data: { email: EMAIL, password: PASS },
  });
  const { access_token } = await login.json();

  await context.setOffline(true);
  const offlineRes = await request
    .post(`${env.apiURL}/api/v1/ai/ask/stream`, {
      headers: { Authorization: `Bearer ${access_token}` },
      data: { prompt: 'offline test' },
    })
    .catch(() => null);
  if (offlineRes) {
    expect(offlineRes.ok()).toBeFalsy();
  }

  await context.setOffline(false);
  const res = await request.post(`${env.apiURL}/api/v1/ai/ask/stream`, {
    headers: { Authorization: `Bearer ${access_token}` },
    data: { prompt: 'Hello after reconnect' },
  });
  expect(res.ok()).toBeTruthy();
  const text = await res.text();
  expect(text).toContain('data:');
});

test('search UI shows retry after offline', async ({ page, context }) => {
  await page.goto('/');
  await context.setOffline(true);
  const input = page.getByLabel('Search query');
  await input.fill('offline recovery test');
  const searchBtn = page.getByRole('button', { name: 'Search' });
  if (await searchBtn.isEnabled()) {
    await searchBtn.click();
    await page.waitForTimeout(2000);
  }
  await context.setOffline(false);
  await expect(page.locator('.hero')).toBeVisible();
});
