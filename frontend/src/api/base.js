const API_BASE = import.meta.env.VITE_API_URL || '/api/v1';

export class ApiError extends Error {
  constructor(message, status) {
    super(message);
    this.status = status;
  }
}

export function createAuthedFetch(getTokens, setTokens, clearTokens) {
  return async function authedFetch(path, options = {}) {
    const tokens = getTokens();
    const headers = {
      'Content-Type': 'application/json',
      ...(options.headers || {}),
    };
    if (tokens?.access_token) {
      headers.Authorization = `Bearer ${tokens.access_token}`;
    }

    let response = await fetch(`${API_BASE}${path}`, { ...options, headers });
    if (response.status === 401 && tokens?.refresh_token) {
      const refreshRes = await fetch(`${API_BASE}/auth/refresh`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ refresh_token: tokens.refresh_token }),
      });
      if (refreshRes.ok) {
        const refreshed = await refreshRes.json();
        setTokens(refreshed);
        headers.Authorization = `Bearer ${refreshed.access_token}`;
        response = await fetch(`${API_BASE}${path}`, { ...options, headers });
      }
    }

    if (!response.ok) {
      let detail = response.statusText;
      try {
        const body = await response.json();
        detail = body.detail || detail;
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
