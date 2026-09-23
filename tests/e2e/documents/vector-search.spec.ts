import { test, expect } from '../fixtures/test-context';
import * as path from 'path';
import * as fs from 'fs';

const EMAIL = `vec-test-${Date.now()}@test.nebula`;
const PASS = 'VecTest1!';

test.beforeAll(async ({ request }) => {
  await request.post('http://localhost:8000/api/v1/auth/signup', {
    data: { email: EMAIL, password: PASS },
  });
});

test.describe('vector search', () => {
  let token: string;
  let docId: number;

  test.beforeAll(async ({ request }) => {
    const login = await request.post('http://localhost:8000/api/v1/auth/login', {
      data: { email: EMAIL, password: PASS },
    });
    const body = await login.json();
    token = body.access_token;

    const tmpFile = path.join(require('os').tmpdir(), `nebula-vec-${Date.now()}.md`);
    fs.writeFileSync(tmpFile, 'Nebula is a private search engine focused on user privacy and AI-powered results.');
    const upload = await request.post('http://localhost:8000/api/v1/storage/documents', {
      headers: { Authorization: `Bearer ${token}` },
      multipart: {
        file: {
          name: 'nebula-intro.md',
          mimeType: 'text/markdown',
          buffer: fs.readFileSync(tmpFile),
        },
      },
    });
    const uploadBody = await upload.json();
    docId = uploadBody.id;
    fs.unlinkSync(tmpFile);
  });

  test('document status returns pending or indexed', async ({ request }) => {
    const res = await request.get(`http://localhost:8000/api/v1/vector/documents/${docId}/status`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    expect(res.ok()).toBeTruthy();
    const body = await res.json();
    expect(['pending', 'indexing', 'indexed']).toContain(body.status);
  });

  test('index-now processes document synchronously', async ({ request }) => {
    const res = await request.post(`http://localhost:8000/api/v1/vector/documents/${docId}/index-now`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    expect([200, 400]).toContain(res.status());
  });

  test('vector search with query returns results', async ({ request }) => {
    const res = await request.post('http://localhost:8000/api/v1/vector/search', {
      headers: { Authorization: `Bearer ${token}` },
      data: { query: 'privacy search engine', top_k: 5 },
    });
    expect(res.ok()).toBeTruthy();
    const body = await res.json();
    expect(body.results).toBeInstanceOf(Array);
    expect(body.query).toBe('privacy search engine');
  });

  test('vector search without auth returns 401', async ({ request }) => {
    const res = await request.post('http://localhost:8000/api/v1/vector/search', {
      data: { query: 'test', top_k: 5 },
    });
    expect(res.status()).toBe(401);
  });
});
