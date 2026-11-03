const configuredApiBase = import.meta.env.VITE_API_URL || '';
const apiOrigin = configuredApiBase
  .replace(/\/(?:api\/)?v[12]\/??$/, '')
  .replace(/\/$/, '');
const API_BASE = `${apiOrigin}/api/v1`;

export class ApiError extends Error {
  constructor(message, status) {
    super(message);
    this.status = status;
  }
}

export function createAuthedFetch(getTokens, setTokens, clearTokens) {
  return async function authedFetch(path, options = {}) {
    const tokens = getTokens();
    const csrfToken = document.cookie
      .split('; ')
      .find((cookie) => cookie.startsWith('csrf_token='))
      ?.slice('csrf_token='.length);
    const headers = {
      'Content-Type': 'application/json',
      ...(options.headers || {}),
    };
    const method = (options.method || 'GET').toUpperCase();
    if (['POST', 'PUT', 'PATCH', 'DELETE'].includes(method) && csrfToken) {
      headers['X-CSRF-Token'] = decodeURIComponent(csrfToken);
    }
    if (tokens?.access_token) {
      headers.Authorization = `Bearer ${tokens.access_token}`;
    }

    let response = await fetch(`${API_BASE}${path}`, { ...options, headers, credentials: 'include' });
    const authEntryPoint = ['/auth/login', '/auth/signup', '/auth/refresh'].some((entry) => path.includes(entry));
    if (response.status === 401 && !authEntryPoint) {
      const refreshRes = await fetch(`${API_BASE}/auth/refresh`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(csrfToken ? { 'X-CSRF-Token': decodeURIComponent(csrfToken) } : {}),
        },
        credentials: 'include',
        body: JSON.stringify({}),
      });
      if (refreshRes.ok) {
        const refreshed = await refreshRes.json();
        setTokens(refreshed);
        headers.Authorization = `Bearer ${refreshed.access_token}`;
        response = await fetch(`${API_BASE}${path}`, { ...options, headers, credentials: 'include' });
      } else {
        clearTokens();
      }
    }

    if (!response.ok) {
      let detail = response.statusText;
      try {
        const body = await response.json();
        detail = body.message || body.detail || detail;
      } catch {
        /* ignore */
      }
      throw new ApiError(String(detail), response.status);
    }
    if (response.status === 204) return null;
    return response.json();
  };
}

export function getApiBase() {
  return API_BASE;
}
