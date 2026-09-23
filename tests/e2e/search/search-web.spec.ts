import { test, expect } from '../fixtures/test-context';

// Requires external search backend (Wikipedia API) — skip if BRAVE_API_KEY and SERPAPI_KEY are both unset
test.skip(!process.env.BRAVE_API_KEY && !process.env.SERPAPI_KEY, 'BRAVE_API_KEY / SERPAPI_KEY not set — skipping external search tests');

const EMAIL = `search-test-${Date.now()}@test.nebula`;
const PASS = 'SearchP1!';

test.beforeAll(async ({ request }) => {
  await request.post('http://localhost:8000/api/v1/auth/signup', {
    data: { email: EMAIL, password: PASS },
  });
});

test.describe('web search API', () => {
  let token: string;

  test.beforeAll(async ({ request }) => {
    const res = await request.post('http://localhost:8000/api/v1/auth/login', {
      data: { email: EMAIL, password: PASS },
    });
    const body = await res.json();
    token = body.access_token;
  });

  test('search with query returns results', async ({ request }) => {
    const res = await request.get('http://localhost:8000/api/v1/search/orchestrate?q=test&backends=wikipedia', {
      headers: { Authorization: `Bearer ${token}` },
    });
    expect(res.ok()).toBeTruthy();
    const body = await res.json();
    expect(body.results).toBeDefined();
    expect(body.meta).toBeDefined();
  });

  test('search with empty query returns 422', async ({ request }) => {
    const res = await request.get('http://localhost:8000/api/v1/search/orchestrate', {
      headers: { Authorization: `Bearer ${token}` },
    });
    expect(res.status()).toBe(422);
  });

  test('search with unknown backend still returns results', async ({ request }) => {
    const res = await request.get('http://localhost:8000/api/v1/search/orchestrate?q=test&backends=unknown', {
      headers: { Authorization: `Bearer ${token}` },
    });
    expect(res.ok()).toBeTruthy();
  });

  test('search with pagination returns page meta', async ({ request }) => {
    const res = await request.get('http://localhost:8000/api/v1/search/orchestrate?q=test&backends=wikipedia&page=1&page_size=5', {
      headers: { Authorization: `Bearer ${token}` },
    });
    expect(res.ok()).toBeTruthy();
    const body = await res.json();
    expect(body.meta.page).toBe(1);
    expect(body.meta.page_size).toBe(5);
  });
});
