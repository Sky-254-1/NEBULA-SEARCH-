export function setLocalStorage(page: import('@playwright/test').Page, key: string, value: unknown) {
  return page.evaluate(({ k, v }) => localStorage.setItem(k, JSON.stringify(v)), { k: key, v: value });
}

export function getLocalStorage(page: import('@playwright/test').Page, key: string) {
  return page.evaluate((k) => {
    const v = localStorage.getItem(k);
    return v ? JSON.parse(v) : null;
  }, key);
}
