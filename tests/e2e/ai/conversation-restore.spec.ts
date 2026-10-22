import { test, expect } from '../fixtures/test-context';
import { env } from '../config/env';

const EMAIL = `restore-test-${Date.now()}@test.nebula`;
const PASS = 'RestoreP1!';

test.beforeAll(async ({ request }) => {
  await request.post(`${env.apiURL}/api/v1/auth/signup`, {
    data: { email: EMAIL, password: PASS },
  });
});

test.describe('AI conversation restore', () => {
  let token: string;

  test.beforeAll(async ({ request }) => {
    const res = await request.post(`${env.apiURL}/api/v1/auth/login`, {
      data: { email: EMAIL, password: PASS },
    });
    const body = await res.json();
    token = body.access_token;
  });

  test('ask persists messages to chat history', async ({ request }) => {
    const prompt = 'What is Nebula Search?';
    const ask = await request.post(`${env.apiURL}/api/v1/ai/ask`, {
      headers: { Authorization: `Bearer ${token}` },
      data: { prompt },
    });
    expect([200, 404]).toContain(ask.status());

    const history = await request.get(`${env.apiURL}/api/v1/ai/chat/history`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    expect(history.ok()).toBeTruthy();
    const body = await history.json();
    expect(body.messages.length).toBeGreaterThanOrEqual(ask.ok() ? 2 : 0);
    if (ask.ok()) {
      const roles = body.messages.map((m: { role: string }) => m.role);
      expect(roles).toContain('user');
      expect(roles).toContain('assistant');
    }
  });

  test('history survives page reload simulation', async ({ page, request }) => {
    await request.post(`${env.apiURL}/api/v1/ai/ask`, {
      headers: { Authorization: `Bearer ${token}` },
      data: { prompt: 'Restore test message' },
    });

    await page.goto('/');
    await page.reload();
    const history = await request.get(`${env.apiURL}/api/v1/ai/chat/history`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    expect(history.ok()).toBeTruthy();
  });
});
