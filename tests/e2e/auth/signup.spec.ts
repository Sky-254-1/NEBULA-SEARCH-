import { test, expect } from '../fixtures/test-context';

const UNIQUE = `signup-${Date.now()}`;

test('signup with valid data returns 201', async ({ request }) => {
  const res = await request.post('http://localhost:8000/api/v1/auth/signup', {
    data: { email: `${UNIQUE}@test.nebula`, password: 'NewPass123!' },
  });
  expect(res.status()).toBe(201);
});

test('signup with duplicate email returns 409', async ({ request }) => {
  const email = `dup-${Date.now()}@test.nebula`;
  await request.post('http://localhost:8000/api/v1/auth/signup', {
    data: { email, password: 'Pass1234!' },
  });
  const res = await request.post('http://localhost:8000/api/v1/auth/signup', {
    data: { email, password: 'Pass1234!' },
  });
  expect(res.status()).toBe(409);
});

test('signup with weak password returns 422', async ({ request }) => {
  const res = await request.post('http://localhost:8000/api/v1/auth/signup', {
    data: { email: `${UNIQUE}-weak@test.nebula`, password: 'ab' },
  });
  expect(res.status()).toBe(422);
});
