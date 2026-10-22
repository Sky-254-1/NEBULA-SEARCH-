import { Page } from '@playwright/test';

export async function openAuthModal(page: Page) {
  const signIn = page.getByRole('button', { name: 'Sign in' });
  if (await signIn.isVisible()) {
    await signIn.click();
  }
}

export async function fillAuthForm(page: Page, email: string, password: string) {
  await page.getByLabel('Email').fill(email);
  await page.getByLabel('Password').fill(password);
}

export async function submitSearch(page: Page, query: string) {
  const input = page.getByLabel('Search query');
  await input.fill(query);
  await page.getByRole('button', { name: 'Search' }).click();
}

export async function waitForResultsOrError(page: Page) {
  await page.waitForSelector('.results-section, .error-box, .ai-box', { timeout: 30000 });
}

export async function setOffline(page: Page, offline: boolean) {
  await page.context().setOffline(offline);
}
