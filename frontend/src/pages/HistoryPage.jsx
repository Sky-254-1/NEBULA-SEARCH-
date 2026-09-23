import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../auth/AuthContext';
import { ProtectedRoute } from '../auth/guards/ProtectedRoute';

export function HistoryPage() {
  const { api } = useAuth();
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    let active = true;
    async function load() {
      try {
        const data = await api.searchHistory(50);
        if (active) setHistory(data.history || []);
      } catch (err) {
        if (active) setError(err.message);
      } finally {
        if (active) setLoading(false);
      }
    }
    load();
    return () => {
      active = false;
    };
  }, [api]);

  return (
    <ProtectedRoute>
      <div className="page">
        <header className="header">
          <Link to="/" className="logo">
            Nebula
          </Link>
          <Link to="/" className="btn ghost">
            ← Back to search
          </Link>
        </header>
        <main className="hero">
          <h1 className="hero-title" style={{ fontSize: '2rem' }}>
            Search History
          </h1>
          {loading && (
            <div className="results-skeleton" aria-busy="true">
              {[1, 2, 3].map((i) => (
                <div key={i} className="skeleton-card" />
              ))}
            </div>
          )}
          {error && (
            <div className="error-box">
              <p>{error}</p>
            </div>
          )}
          {!loading && !error && history.length === 0 && (
            <div className="empty-state">
              <div className="empty-icon">📜</div>
              <h3>No search history yet</h3>
              <p>Your searches will appear here once you start exploring.</p>
            </div>
          )}
          {!loading && history.length > 0 && (
            <ul className="history-list">
              {history.map((item, i) => (
                <li key={i} className="history-item">
                  <Link to={`/?q=${encodeURIComponent(item.query)}`} className="history-query">
                    {item.query}
                  </Link>
                  <span className="history-meta">
                    {item.backend} · {item.results_count} results ·{' '}
                    {new Date(item.searched_at).toLocaleString()}
                  </span>
                </li>
              ))}
            </ul>
          )}
        </main>
      </div>
    </ProtectedRoute>
  );
}
