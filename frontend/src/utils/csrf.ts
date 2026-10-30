/** Return the double-submit header required for cookie-authenticated writes. */
export function getCsrfHeaders(): Record<string, string> {
  const entry = document.cookie
    .split('; ')
    .find((cookie) => cookie.startsWith('csrf_token='));
  if (!entry) return {};
  return { 'X-CSRF-Token': decodeURIComponent(entry.slice('csrf_token='.length)) };
}
