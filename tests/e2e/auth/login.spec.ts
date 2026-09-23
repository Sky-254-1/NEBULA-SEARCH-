import { test, expect, signUpUser, loginUser } from '../fixtures/test-context';

const TEST_EMAIL = `login-test-${Date.now()}@test.nebula`;
const TEST_PASS = 'Password123!';

test.beforeAll(async ({ request }) => {
  const res = await request.post('http://localhost:8000/api/v1/auth/signup', {
    data: { email: TEST_EMAIL, password: TEST_PASS },
  });
  if (res.status() !== 409) expect(res.status()).toBe(201);
});

test('login with valid credentials returns tokens', async ({ request }) => {
  const res = await request.post('http://localhost:8000/api/v1/auth/login', {
    data: { email: TEST_EMAIL, password: TEST_PASS },
  });
  expect(res.ok()).toBeTruthy();
  const body = await res.json();
  expect(body.access_token).toBeTruthy();
  expect(body.refresh_token).toBeTruthy();
});

test('login with wrong password returns 401', async ({ request }) => {
  const res = await request.post('http://localhost:8000/api/v1/auth/login', {
    data: { email: TEST_EMAIL, password: 'WrongPass!' },
  });
  expect(res.status()).toBe(401);
});

test('login with non-existent email returns 401', async ({ request }) => {
  const res = await request.post('http://localhost:8000/api/v1/auth/login', {
    data: { email: 'noone@test.nebula', password: TEST_PASS },
  });
  expect(res.status()).toBe(401);
});
