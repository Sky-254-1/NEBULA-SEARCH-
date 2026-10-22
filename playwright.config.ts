import { defineConfig, devices } from '@playwright/test';

/**
 * Playwright E2E configuration for Nebula Search.
 * Runs against the full stack (backend on :8000, frontend on :5173).
 *
 * Start the stack first:
 *   docker compose up -d   or   make dev
 * Then:
 *   npx playwright test
 */
export default defineConfig({
  testDir: './tests/e2e',
  outputDir: './tests/e2e/results',
  timeout: 30_000,
  expect: { timeout: 5_000 },
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,

  reporter: [
    ['html', { outputFolder: 'playwright-report', open: 'never' }],
    ['list'],
    ...(process.env.CI ? [['github'] as any] : []),
  ],

  use: {
    baseURL: process.env.E2E_BASE_URL ?? 'http://localhost:5173',
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
    video: 'on-first-retry',
  },

  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
    {
      name: 'firefox',
      use: { ...devices['Desktop Firefox'] },
    },
    {
      name: 'webkit',
      use: { ...devices['Desktop Safari'] },
    },
    /* Mobile viewports */
    {
      name: 'mobile-chrome',
      use: { ...devices['Pixel 5'] },
    },
    {
      name: 'tablet',
      use: { ...devices['iPad Pro 11'] },
    },
  ],

  /* Start local dev server automatically when not in CI */
  webServer: process.env.CI
    ? undefined
    : {
        command: 'npm run dev',
        cwd: './frontend',
        port: 5173,
        reuseExistingServer: true,
        timeout: 60_000,
      },
});
