import { test as base, Page } from '@playwright/test';

export type AuthTokens = {
  access_token: string;
  refresh_token: string;
};

export type TestContext = {
  apiBase: string;
  tokens: AuthTokens | null;
  currentUser: { email: string; password: string } | null;
};

export const test = base.extend<{ ctx: TestContext }>({
  ctx: async ({ page }, use) => {
    const ctx: TestContext = {
      apiBase: 'http://localhost:8000/api/v1',
      tokens: null,
      currentUser: null,
    };
    await use(ctx);
  },
});

export const expect = base.expect;

export async function signUpUser(page: Page, ctx: TestContext, email: string, password: string) {
  const res = await page.request.post(`${ctx.apiBase}/auth/signup`, {
    data: { email, password },
  });
  if (res.status() === 409) return;
  expect(res.status()).toBe(201);
}

export async function loginUser(page: Page, ctx: TestContext, email: string, password: string) {
  const res = await page.request.post(`${ctx.apiBase}/auth/login`, {
    data: { email, password },
  });
  expect(res.ok()).toBeTruthy();
  const body = await res.json();
  ctx.tokens = body;
  ctx.currentUser = { email, password };
}
