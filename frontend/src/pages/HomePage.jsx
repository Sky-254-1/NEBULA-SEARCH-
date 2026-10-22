import { useEffect, useState } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import { AuthModal } from '../components/AuthModal';
import { ChatPanel } from '../components/ChatPanel';
import { Header } from '../components/Header';
import { InstallPrompt } from '../components/InstallPrompt';
import { Pagination } from '../components/Pagination';
import { ResultsList } from '../components/ResultsList';
import { SearchBar } from '../components/SearchBar';
import { Toast } from '../components/Toast';
import { useAI } from '../hooks/useAI';
import { useChat } from '../hooks/useChat';
import { useInstallPrompt } from '../hooks/useInstallPrompt';
import { useSearch } from '../hooks/useSearch';
import { useSearchState } from '../state/SearchContext';

export function HomePage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const { query, setQuery, page, setPage, config, setConfig, addToHistory } = useSearchState();
  const [authOpen, setAuthOpen] = useState(false);
  const [toast, setToast] = useState(null);
  const [installDismissed, setInstallDismissed] = useState(false);
  const { results, meta, loading, error, search } = useSearch();
  const { answer, provider, loading: aiLoading, streaming, error: aiError, ask } = useAI();
  const { messages, loading: chatLoading, clear: clearChat, reload: reloadChat } = useChat();
  const { canInstall, install } = useInstallPrompt();

  useEffect(() => {
    document.body.dataset.theme = config.theme || 'dark';
  }, [config.theme]);

  async function runSearch(q = query, targetPage = page) {
    const trimmed = (q || query).trim();
    if (!trimmed) return;
    setQuery(trimmed);
    setSearchParams({ q: trimmed });
    await search(trimmed, {
      backends: config.backends,
      page: targetPage,
      page_size: config.pageSize || 10,
    });
    await ask(trimmed);
    addToHistory(trimmed);
    reloadChat();
  }

  useEffect(() => {
    const q = searchParams.get('q');
    if (q) {
      setQuery(q);
      runSearch(q, 1);
    }
    if (searchParams.get('auth') === '1') setAuthOpen(true);
  }, []);

  function toggleTheme() {
    const theme = config.theme === 'dark' ? 'light' : 'dark';
    setConfig({ ...config, theme });
  }

  function handlePageChange(nextPage) {
    setPage(nextPage);
    runSearch(query, nextPage);
  }

  async function handleInstall() {
    const ok = await install();
    setToast({
      message: ok ? 'Nebula installed successfully' : 'Install dismissed',
      type: ok ? 'success' : 'info',
    });
  }

  return (
    <div className="page">
      <Header
        onAuthClick={() => setAuthOpen(true)}
        theme={config.theme}
        onToggleTheme={toggleTheme}
      />
      {!installDismissed && (
        <InstallPrompt
          canInstall={canInstall}
          onInstall={handleInstall}
          onDismiss={() => setInstallDismissed(true)}
        />
      )}
      <main className="hero">
        <h1 className="hero-title">Nebula Search</h1>
        <p className="hero-tagline">Private · Intelligent · Hybrid search</p>
        <SearchBar
          value={query}
          onChange={setQuery}
          onSubmit={() => {
            setPage(1);
            runSearch(query, 1);
          }}
          loading={loading}
        />
        <div className="backend-select">
          <label>
            Backends
            <select
              value={config.backends}
              onChange={(e) => setConfig({ ...config, backends: e.target.value })}
            >
              <option value="wikipedia">Wikipedia</option>
              <option value="wikipedia,brave">Wikipedia + Brave</option>
              <option value="wikipedia,serpapi">Wikipedia + SerpAPI</option>
            </select>
          </label>
          <Link to="/history" className="btn ghost">
            History
          </Link>
        </div>
        {(error || aiError) && (
          <div className="error-box">
            <p>{error || aiError}</p>
            <button type="button" className="btn ghost" onClick={() => runSearch()}>
              Retry
            </button>
          </div>
        )}
        {(answer || aiLoading) && (
          <section className="ai-box">
            <h2>
              AI Overview {provider ? `· ${provider}` : ''}
              {streaming && <span className="streaming-dot" aria-label="Streaming" />}
            </h2>
            {aiLoading && !answer ? (
              <div className="ai-skeleton">
                <div className="skeleton-line" />
                <div className="skeleton-line short" />
              </div>
            ) : (
              <p>{answer}</p>
            )}
          </section>
        )}
        {meta && (
          <section className="results-section">
            <p className="results-meta">
              {meta.total} results for “{meta.query}” {meta.cached ? '(cached)' : ''}
            </p>
            <ResultsList results={results} loading={loading} query={meta.query} />
            <Pagination
              page={meta.page || page}
              pageSize={meta.page_size || config.pageSize || 10}
              total={meta.total}
              onPageChange={handlePageChange}
              disabled={loading}
            />
          </section>
        )}
        <ChatPanel messages={messages} loading={chatLoading} onClear={clearChat} />
      </main>
      <AuthModal
        open={authOpen}
        onClose={() => setAuthOpen(false)}
        onSuccess={() => setToast({ message: 'Signed in successfully', type: 'success' })}
      />
      <Toast message={toast?.message} type={toast?.type} onClose={() => setToast(null)} />
    </div>
  );
}
