import { createContext, useContext, useMemo, useState } from 'react';
import { loadConfig, saveConfig, loadHistory, saveHistory } from '../utils/storage';

const SearchContext = createContext(null);

export function SearchProvider({ children }) {
  const [query, setQuery] = useState('');
  const [page, setPage] = useState(1);
  const [config, setConfigState] = useState(() =>
    loadConfig({ theme: 'dark', backends: 'wikipedia', pageSize: 10 })
  );
  const [localHistory, setLocalHistory] = useState(() => loadHistory());

  const setConfig = (next) => {
    setConfigState(next);
    saveConfig(next);
    document.body.dataset.theme = next.theme || 'dark';
  };

  const addToHistory = (q) => {
    const hist = [q, ...localHistory.filter((h) => h !== q)].slice(0, 20);
    setLocalHistory(hist);
    saveHistory(hist);
  };

  const value = useMemo(
    () => ({
      query,
      setQuery,
      page,
      setPage,
      config,
      setConfig,
      localHistory,
      addToHistory,
    }),
    [query, page, config, localHistory]
  );

  return <SearchContext.Provider value={value}>{children}</SearchContext.Provider>;
}

export function useSearchState() {
  const ctx = useContext(SearchContext);
  if (!ctx) throw new Error('useSearchState must be used within SearchProvider');
  return ctx;
}
