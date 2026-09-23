import { test, expect } from '../fixtures/test-context';
import * as path from 'path';
import * as fs from 'fs';

const EMAIL = `doc-test-${Date.now()}@test.nebula`;
const PASS = 'DocTest1!';

test.beforeAll(async ({ request }) => {
  await request.post('http://localhost:8000/api/v1/auth/signup', {
    data: { email: EMAIL, password: PASS },
  });
});

test.describe('document upload and management', () => {
  let token: string;

  test.beforeAll(async ({ request }) => {
    const res = await request.post('http://localhost:8000/api/v1/auth/login', {
      data: { email: EMAIL, password: PASS },
    });
    const body = await res.json();
    token = body.access_token;
  });

  test('upload a text file', async ({ request }) => {
    const tmpFile = path.join(require('os').tmpdir(), `nebula-test-${Date.now()}.txt`);
    fs.writeFileSync(tmpFile, 'This is a test document for Nebula search engine.');
    const file = fs.readFileSync(tmpFile);

    const res = await request.post('http://localhost:8000/api/v1/storage/documents', {
      headers: {
        Authorization: `Bearer ${token}`,
      },
      multipart: {
        file: {
          name: 'test-doc.txt',
          mimeType: 'text/plain',
          buffer: file,
        },
      },
    });
    expect(res.ok()).toBeTruthy();
    const body = await res.json();
    expect(body.id).toBeGreaterThan(0);
    expect(body.filename).toBe('test-doc.txt');
    fs.unlinkSync(tmpFile);
  });

  test('list documents returns uploaded files', async ({ request }) => {
    const res = await request.get('http://localhost:8000/api/v1/storage/documents', {
      headers: { Authorization: `Bearer ${token}` },
    });
    expect(res.ok()).toBeTruthy();
    const body = await res.json();
    expect(body.documents).toBeInstanceOf(Array);
  });

  test('delete document', async ({ request }) => {
    const tmpFile = path.join(require('os').tmpdir(), `nebula-del-${Date.now()}.txt`);
    fs.writeFileSync(tmpFile, 'Delete me');
    const upload = await request.post('http://localhost:8000/api/v1/storage/documents', {
      headers: { Authorization: `Bearer ${token}` },
      multipart: {
        file: {
          name: 'delete-me.txt',
          mimeType: 'text/plain',
          buffer: fs.readFileSync(tmpFile),
        },
      },
    });
    const { id } = await upload.json();
    fs.unlinkSync(tmpFile);

    const res = await request.delete(`http://localhost:8000/api/v1/storage/documents/${id}`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    expect(res.ok()).toBeTruthy();
  });

  test('reject unsupported file type', async ({ request }) => {
    const res = await request.post('http://localhost:8000/api/v1/storage/documents', {
      headers: { Authorization: `Bearer ${token}` },
      multipart: {
        file: {
          name: 'test.exe',
          mimeType: 'application/octet-stream',
          buffer: Buffer.from('bad'),
        },
      },
    });
    expect(res.status()).toBe(400);
  });
});
