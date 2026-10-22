import { test, expect } from '../fixtures/test-context';

const EMAIL = `refresh-test-${Date.now()}@test.nebula`;
const PASS = 'RefreshP1!';

test.beforeAll(async ({ request }) => {
  await request.post('http://localhost:8000/api/v1/auth/signup', {
    data: { email: EMAIL, password: PASS },
  });
});

test('refresh with valid token returns new tokens', async ({ request }) => {
  const login = await request.post('http://localhost:8000/api/v1/auth/login', {
    data: { email: EMAIL, password: PASS },
  });
  const { refresh_token } = await login.json();

  const refresh = await request.post('http://localhost:8000/api/v1/auth/refresh', {
    data: { refresh_token },
  });
  expect(refresh.ok()).toBeTruthy();
  const body = await refresh.json();
  expect(body.access_token).toBeTruthy();
  expect(body.refresh_token).toBeTruthy();
});

test('refresh with expired token returns 401', async ({ request }) => {
  const res = await request.post('http://localhost:8000/api/v1/auth/refresh', {
    data: { refresh_token: 'invalid-or-expired-token' },
  });
  expect(res.status()).toBe(401);
});
