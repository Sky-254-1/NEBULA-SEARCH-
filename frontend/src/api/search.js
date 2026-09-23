export function createSearchApi(authedFetch) {
  return {
    searchOrchestrate: ({ q, backends = 'wikipedia', page = 1, page_size = 10 }) =>
      authedFetch(
        `/search/orchestrate?q=${encodeURIComponent(q)}&backends=${encodeURIComponent(backends)}&page=${page}&page_size=${page_size}`
      ),
    searchHistory: (limit = 20) => authedFetch(`/search/history?limit=${limit}`),
  };
}
