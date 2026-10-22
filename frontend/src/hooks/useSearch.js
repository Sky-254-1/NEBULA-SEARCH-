import { useCallback, useState } from 'react';
import { useAuth } from '../auth/AuthContext';

function escapeHtml(str = '') {
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}

export function useSearch() {
  const { api, isAuthenticated } = useAuth();

  const [results, setResults] = useState([]);
  const [meta, setMeta] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const search = useCallback(
    async function (query, options) {
      const {
        backends = 'wikipedia',
        page = 1,
        page_size = 10,
      } = options || {};

      if (!query || !query.trim()) {
        return;
      }

      setLoading(true);
      setError(null);

      try {
        if (isAuthenticated) {
          const data = await api.searchOrchestrate({
            q: query,
            backends,
            page,
            page_size,
          });

          setResults((data && data.results) || []);
          setMeta(data || null);
        } else {
          const offset = (page - 1) * page_size;

          const url =
            'https://en.wikipedia.org/w/api.php' +
            '?action=query' +
            '&list=search' +
            '&srsearch=' + encodeURIComponent(query) +
            '&format=json' +
            '&origin=*' +
            '&srlimit=' + page_size +
            '&sroffset=' + offset;

          const res = await fetch(url);

          if (!res.ok) {
            throw new Error('Request failed: ' + res.status);
          }

          const json = await res.json();

          const searchResults =
            (json && json.query && json.query.search) || [];

          const mapped = searchResults.map(function (item) {
            return {
              title: item.title || '',
              snippet: escapeHtml(item.snippet || ''),
              url:
                'https://en.wikipedia.org/wiki/' +
                encodeURIComponent((item.title || '').replace(/ /g, '_')),
              source: 'wikipedia',
            };
          });

          setResults(mapped);

          setMeta({
            query: query,
            total:
              (json &&
                json.query &&
                json.query.searchinfo &&
                json.query.searchinfo.totalhits) ||
              mapped.length,
            page: page,
            page_size: page_size,
            cached: false,
          });
        }
      } catch (err) {
        setError((err && err.message) || 'Search failed');
        setResults([]);
        setMeta(null);
      } finally {
        setLoading(false);
      }
    },
    [api, isAuthenticated]
  );

  return {
    results,
    meta,
    loading,
    error,
    search,
  };
}
