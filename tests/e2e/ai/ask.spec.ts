import { test, expect } from '../fixtures/test-context';

const EMAIL = `ai-test-${Date.now()}@test.nebula`;
const PASS = 'AiTestP1!';

test.beforeAll(async ({ request }) => {
  await request.post('http://localhost:8000/api/v1/auth/signup', {
    data: { email: EMAIL, password: PASS },
  });
});

test.describe('AI endpoints', () => {
  let token: string;

  test.beforeAll(async ({ request }) => {
    const res = await request.post('http://localhost:8000/api/v1/auth/login', {
      data: { email: EMAIL, password: PASS },
    });
    const body = await res.json();
    token = body.access_token;
  });

  test('ask returns answer or 404', async ({ request }) => {
    const res = await request.post('http://localhost:8000/api/v1/ai/ask', {
      headers: { Authorization: `Bearer ${token}` },
      data: { prompt: 'What is the capital of France?' },
    });
    expect([200, 404]).toContain(res.status());
    if (res.ok()) {
      const body = await res.json();
      expect(body.answer).toBeTruthy();
    }
  });

  test('ask with missing auth returns 401', async ({ request }) => {
    const res = await request.post('http://localhost:8000/api/v1/ai/ask', {
      data: { prompt: 'test' },
    });
    expect(res.status()).toBe(401);
  });

  test('chat history returns messages', async ({ request }) => {
    const res = await request.get('http://localhost:8000/api/v1/ai/chat/history', {
      headers: { Authorization: `Bearer ${token}` },
    });
    expect(res.ok()).toBeTruthy();
    const body = await res.json();
    expect(body.messages).toBeDefined();
  });

  test('chat history can be cleared', async ({ request }) => {
    const res = await request.delete('http://localhost:8000/api/v1/ai/chat/history', {
      headers: { Authorization: `Bearer ${token}` },
    });
    expect(res.ok()).toBeTruthy();
  });
});
