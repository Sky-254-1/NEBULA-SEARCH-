import { Page } from '@playwright/test';

const SEED_EMAIL = `e2e-seed-${Date.now()}@test.nebula`;
const SEED_PASSWORD = 'TestPass123!';

export async function seedUser(page: Page, apiBase: string) {
  const res = await page.request.post(`${apiBase}/auth/signup`, {
    data: { email: SEED_EMAIL, password: SEED_PASSWORD },
  });
  if (res.status() === 409) return { email: SEED_EMAIL, password: SEED_PASSWORD };
  if (!res.ok()) throw new Error(`Seed signup failed: ${res.status()}`);
  return { email: SEED_EMAIL, password: SEED_PASSWORD };
}

export { SEED_EMAIL, SEED_PASSWORD };
