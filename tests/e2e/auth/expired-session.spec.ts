import { test, expect } from '../fixtures/auth.fixture';
import { env } from '../config/env';

test.describe('Expired sessions', () => {
  test('invalid access token rejected', async ({ request }) => {
    const res = await request.get(`${env.apiURL}/api/v1/auth/me`, {
      headers: { Authorization: 'Bearer invalid-token' },
    });
    expect(res.status()).toBe(401);
  });

  test('expired refresh token rejected', async ({ request }) => {
    const res = await request.post(`${env.apiURL}/api/v1/auth/refresh`, {
      data: { refresh_token: 'expired-invalid-token-xyz' },
    });
    expect(res.status()).toBe(401);
  });
});
