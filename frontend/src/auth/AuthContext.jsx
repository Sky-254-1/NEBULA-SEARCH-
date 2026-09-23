import { createContext, useContext, useEffect, useMemo, useState } from 'react';
import { buildClient } from '../api/client';
import { clearTokens, loadTokens, saveTokens } from '../utils/storage';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [tokens, setTokensState] = useState(() => loadTokens());
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  const setTokens = (next) => {
    setTokensState(next);
    saveTokens(next);
  };

  const clear = () => {
    setTokensState(null);
    clearTokens();
    setUser(null);
  };

  const api = useMemo(
    () => buildClient(() => tokens, setTokens, clear),
    [tokens]
  );

  useEffect(() => {
    let active = true;
    async function restore() {
      if (!tokens?.access_token) {
        setLoading(false);
        return;
      }
      try {
        const me = await api.me();
        if (active) setUser(me);
      } catch {
        clear();
      } finally {
        if (active) setLoading(false);
      }
    }
    restore();
    return () => {
      active = false;
    };
  }, []);

  const value = {
    user,
    loading,
    isAuthenticated: Boolean(user),
    api,
    login: async (email, password) => {
      await api.login(email, password);
      const me = await api.me();
      setUser(me);
      return me;
    },
    signup: (email, password) => api.signup(email, password),
    logout: async () => {
      await api.logout();
      clear();
    },
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used within AuthProvider');
  return ctx;
}
