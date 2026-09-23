export function ResultsList({ results, loading, query }) {
  if (loading) {
    return (
      <div className="results-skeleton" aria-busy="true">
        {[1, 2, 3].map((i) => (
          <div key={i} className="skeleton-card" />
        ))}
      </div>
    );
  }

  if (!results.length) {
    return (
      <div className="empty-state">
        <div className="empty-icon">🔭</div>
        <h3>No results for “{query}”</h3>
        <p>Try different keywords or sign in to use multi-backend search.</p>
      </div>
    );
  }

  return (
    <div className="results-grid">
      {results.map((item) => (
        <a key={item.url} href={item.url} target="_blank" rel="noopener noreferrer" className="result-card">
          <h3>{item.title}</h3>
          <p>{item.snippet}</p>
          <span className="result-url">{item.url}</span>
          <span className="result-source">{item.source}</span>
        </a>
      ))}
    </div>
  );
}
