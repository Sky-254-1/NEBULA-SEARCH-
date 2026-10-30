const TOKEN_KEY = 'nebula_tokens';
const CONFIG_KEY = 'nebula_cfg';

export function loadTokens() {
  try {
    const raw = localStorage.getItem(TOKEN_KEY);
    const stored = raw ? JSON.parse(raw) : null;
    const accessToken = stored?.access_token || localStorage.getItem('access_token');
    if (accessToken) return { access_token: accessToken };
    return null;
  } catch {
    return null;
  }
}

export function saveTokens(tokens) {
  if (tokens?.access_token) localStorage.setItem('access_token', tokens.access_token);
  localStorage.removeItem('refresh_token');
  localStorage.removeItem(TOKEN_KEY);
}

export function clearTokens() {
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem('access_token');
  localStorage.removeItem('refresh_token');
}

export function loadConfig(defaults = {}) {
  try {
    const raw = localStorage.getItem(CONFIG_KEY);
    return raw ? { ...defaults, ...JSON.parse(raw) } : defaults;
  } catch {
    return defaults;
  }
}

export function saveConfig(config) {
  localStorage.setItem(CONFIG_KEY, JSON.stringify(config));
}

export function loadHistory() {
  try {
    const raw = localStorage.getItem('nebula_history');
    return raw ? JSON.parse(raw) : [];
  } catch {
    return [];
  }
}

export function saveHistory(items) {
  localStorage.setItem('nebula_history', JSON.stringify(items));
}
