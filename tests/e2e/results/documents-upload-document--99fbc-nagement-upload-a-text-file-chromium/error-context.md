# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: documents\upload.spec.ts >> document upload and management >> upload a text file
- Location: tests\e2e\documents\upload.spec.ts:25:7

# Error details

```
Error: expect(received).toBeTruthy()

Received: false
```

# Test source

```ts
  1  | import { test, expect } from '../fixtures/test-context';
  2  | import * as path from 'path';
  3  | import * as fs from 'fs';
  4  | 
  5  | const EMAIL = `doc-test-${Date.now()}@test.nebula`;
  6  | const PASS = 'DocTest1!';
  7  | 
  8  | test.beforeAll(async ({ request }) => {
  9  |   await request.post('http://localhost:8000/api/v1/auth/signup', {
  10 |     data: { email: EMAIL, password: PASS },
  11 |   });
  12 | });
  13 | 
  14 | test.describe('document upload and management', () => {
  15 |   let token: string;
  16 | 
  17 |   test.beforeAll(async ({ request }) => {
  18 |     const res = await request.post('http://localhost:8000/api/v1/auth/login', {
  19 |       data: { email: EMAIL, password: PASS },
  20 |     });
  21 |     const body = await res.json();
  22 |     token = body.access_token;
  23 |   });
  24 | 
  25 |   test('upload a text file', async ({ request }) => {
  26 |     const tmpFile = path.join(require('os').tmpdir(), `nebula-test-${Date.now()}.txt`);
  27 |     fs.writeFileSync(tmpFile, 'This is a test document for Nebula search engine.');
  28 |     const file = fs.readFileSync(tmpFile);
  29 | 
  30 |     const res = await request.post('http://localhost:8000/api/v1/storage/documents', {
  31 |       headers: {
  32 |         Authorization: `Bearer ${token}`,
  33 |       },
  34 |       multipart: {
  35 |         file: {
  36 |           name: 'test-doc.txt',
  37 |           mimeType: 'text/plain',
  38 |           buffer: file,
  39 |         },
  40 |       },
  41 |     });
> 42 |     expect(res.ok()).toBeTruthy();
     |                      ^ Error: expect(received).toBeTruthy()
  43 |     const body = await res.json();
  44 |     expect(body.id).toBeGreaterThan(0);
  45 |     expect(body.filename).toBe('test-doc.txt');
  46 |     fs.unlinkSync(tmpFile);
  47 |   });
  48 | 
  49 |   test('list documents returns uploaded files', async ({ request }) => {
  50 |     const res = await request.get('http://localhost:8000/api/v1/storage/documents', {
  51 |       headers: { Authorization: `Bearer ${token}` },
  52 |     });
  53 |     expect(res.ok()).toBeTruthy();
  54 |     const body = await res.json();
  55 |     expect(body.documents).toBeInstanceOf(Array);
  56 |   });
  57 | 
  58 |   test('delete document', async ({ request }) => {
  59 |     const tmpFile = path.join(require('os').tmpdir(), `nebula-del-${Date.now()}.txt`);
  60 |     fs.writeFileSync(tmpFile, 'Delete me');
  61 |     const upload = await request.post('http://localhost:8000/api/v1/storage/documents', {
  62 |       headers: { Authorization: `Bearer ${token}` },
  63 |       multipart: {
  64 |         file: {
  65 |           name: 'delete-me.txt',
  66 |           mimeType: 'text/plain',
  67 |           buffer: fs.readFileSync(tmpFile),
  68 |         },
  69 |       },
  70 |     });
  71 |     const { id } = await upload.json();
  72 |     fs.unlinkSync(tmpFile);
  73 | 
  74 |     const res = await request.delete(`http://localhost:8000/api/v1/storage/documents/${id}`, {
  75 |       headers: { Authorization: `Bearer ${token}` },
  76 |     });
  77 |     expect(res.ok()).toBeTruthy();
  78 |   });
  79 | 
  80 |   test('reject unsupported file type', async ({ request }) => {
  81 |     const res = await request.post('http://localhost:8000/api/v1/storage/documents', {
  82 |       headers: { Authorization: `Bearer ${token}` },
  83 |       multipart: {
  84 |         file: {
  85 |           name: 'test.exe',
  86 |           mimeType: 'application/octet-stream',
  87 |           buffer: Buffer.from('bad'),
  88 |         },
  89 |       },
  90 |     });
  91 |     expect(res.status()).toBe(400);
  92 |   });
  93 | });
  94 | 
```