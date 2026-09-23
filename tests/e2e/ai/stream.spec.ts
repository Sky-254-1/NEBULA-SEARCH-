import { test, expect } from '../fixtures/test-context';

const EMAIL = `stream-test-${Date.now()}@test.nebula`;
const PASS = 'StreamP1!';

test.beforeAll(async ({ request }) => {
  await request.post('http://localhost:8000/api/v1/auth/signup', {
    data: { email: EMAIL, password: PASS },
  });
});

test('stream endpoint returns SSE events', async ({ request }) => {
  const login = await request.post('http://localhost:8000/api/v1/auth/login', {
    data: { email: EMAIL, password: PASS },
  });
  const { access_token } = await login.json();

  const res = await request.post('http://localhost:8000/api/v1/ai/ask/stream', {
    headers: { Authorization: `Bearer ${access_token}` },
    data: { prompt: 'Hello' },
  });
  expect(res.ok()).toBeTruthy();
  const text = await res.text();
  expect(text).toContain('data:');
});

test('stream with missing auth returns 401', async ({ request }) => {
  const res = await request.post('http://localhost:8000/api/v1/ai/ask/stream', {
    data: { prompt: 'test' },
  });
  expect(res.status()).toBe(401);
});
