import { test, expect } from '../fixtures/test-context';
import * as fs from 'fs';
import * as os from 'os';
import * as path from 'path';
import { env } from '../config/env';

// Requires AI provider (OPENAI_API_KEY or AI_PROVIDER) — skip if not configured
test.skip(!process.env.OPENAI_API_KEY && !process.env.AI_PROVIDER, 'OPENAI_API_KEY / AI_PROVIDER not set — skipping AI-dependent tests');

const EMAIL = `summarize-${Date.now()}@test.nebula`;
const PASS = 'SumP1!';

test.beforeAll(async ({ request }) => {
  await request.post(`${env.apiURL}/api/v1/auth/signup`, {
    data: { email: EMAIL, password: PASS },
  });
});

test('summarize uploaded documents returns answer with citations', async ({ request }) => {
  const login = await request.post(`${env.apiURL}/api/v1/auth/login`, {
    data: { email: EMAIL, password: PASS },
  });
  const { access_token } = await login.json();

  const tmpFile = path.join(os.tmpdir(), `nebula-sum-${Date.now()}.txt`);
  fs.writeFileSync(
    tmpFile,
    'Nebula Search is a private hybrid search engine with AI-powered answers and document intelligence.',
  );

  const upload = await request.post(`${env.apiURL}/api/v1/storage/documents`, {
    headers: { Authorization: `Bearer ${access_token}` },
    multipart: {
      file: {
        name: 'nebula-overview.txt',
        mimeType: 'text/plain',
        buffer: fs.readFileSync(tmpFile),
      },
    },
  });
  expect(upload.ok()).toBeTruthy();
  const { id: docId } = await upload.json();
  fs.unlinkSync(tmpFile);

  const index = await request.post(`${env.apiURL}/api/v1/vector/documents/${docId}/index-now`, {
    headers: { Authorization: `Bearer ${access_token}` },
  });
  expect(index.ok()).toBeTruthy();

  const ask = await request.post(`${env.apiURL}/api/v1/vector/ask`, {
    headers: { Authorization: `Bearer ${access_token}` },
    data: { query: 'Summarize uploaded documents', top_k: 5 },
  });
  expect(ask.ok()).toBeTruthy();
  const body = await ask.json();
  expect(body.answer).toBeTruthy();
  expect(body.citations).toBeInstanceOf(Array);
  expect(body.sources).toBeInstanceOf(Array);
});
