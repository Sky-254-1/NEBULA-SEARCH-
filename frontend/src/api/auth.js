export function createAuthApi(authedFetch, setTokens, getTokens, clearTokens) {
  return {
    signup: (email, password) =>
      authedFetch('/auth/signup', { method: 'POST', body: JSON.stringify({ email, password }) }),
    login: async (email, password) => {
      const data = await authedFetch('/auth/login', {
        method: 'POST',
        body: JSON.stringify({ email, password }),
      });
      setTokens(data);
      return data;
    },
    logout: async () => {
      const tokens = getTokens();
      if (tokens?.refresh_token) {
        await authedFetch('/auth/logout', {
          method: 'POST',
          body: JSON.stringify({ refresh_token: tokens.refresh_token }),
        }).catch(() => null);
      }
      clearTokens();
    },
    me: () => authedFetch('/auth/me'),
  };
}
