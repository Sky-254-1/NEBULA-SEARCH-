import { test, expect } from '../fixtures/test-context';

const EMAIL = `logout-test-${Date.now()}@test.nebula`;
const PASS = 'LogoutPass1!';

test.beforeAll(async ({ request }) => {
  await request.post('http://localhost:8000/api/v1/auth/signup', {
    data: { email: EMAIL, password: PASS },
  });
});

test('logout invalidates refresh token', async ({ request }) => {
  const login = await request.post('http://localhost:8000/api/v1/auth/login', {
    data: { email: EMAIL, password: PASS },
  });
  const { refresh_token } = await login.json();

  const logout = await request.post('http://localhost:8000/api/v1/auth/logout', {
    data: { refresh_token },
  });
  expect(logout.ok()).toBeTruthy();

  const refresh = await request.post('http://localhost:8000/api/v1/auth/refresh', {
    data: { refresh_token },
  });
  expect(refresh.status()).toBe(401);
});
