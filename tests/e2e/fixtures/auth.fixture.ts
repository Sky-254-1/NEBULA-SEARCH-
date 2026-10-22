import { test as base } from '@playwright/test';
import { env } from '../config/env';

export type AuthFixtures = {
  testEmail: string;
  testPassword: string;
  accessToken: string;
};

export const test = base.extend<AuthFixtures>({
  testEmail: async ({}, use) => {
    const token = Math.random().toString(36).slice(2, 8);
    await use(`e2e_${token}@nebula.test`);
  },
  testPassword: async ({}, use) => {
    await use(env.defaultPassword);
  },
  accessToken: async ({ request, testEmail, testPassword }, use) => {
    await request.post(`${env.apiURL}/api/v1/auth/signup`, {
      data: { email: testEmail, password: testPassword },
    });
    const login = await request.post(`${env.apiURL}/api/v1/auth/login`, {
      data: { email: testEmail, password: testPassword },
    });
    const body = await login.json();
    await use(body.access_token);
  },
});

export { expect } from '@playwright/test';
