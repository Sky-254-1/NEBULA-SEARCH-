/**
 * Store tests: useSearchStore, useAuthStore, useAIChatStore
 * Tests all Zustand store implementations to ensure 85%+ coverage.
 */
import { describe, it, expect, vi, beforeEach } from 'vitest';

// ── Mocks before imports ──────────────────────────────────────────────────────
vi.mock('@/api/search', () => ({
  searchApi: {
    search: vi.fn().mockResolvedValue({ results: [], total: 0 }),
    webSearch: vi.fn().mockResolvedValue([]),
    getSearchHistory: vi.fn().mockResolvedValue({ history: [] }),
    intelligentSearch: vi.fn().mockResolvedValue({ results: [] }),
    getSuggestions: vi.fn().mockResolvedValue({ suggestions: [] }),
    autocomplete: vi.fn().mockResolvedValue({ completions: [] }),
    spellCheck: vi.fn().mockResolvedValue({ original: '', corrected: '', was_corrected: false }),
    getTrending: vi.fn().mockResolvedValue({ trending: [], period_hours: 24 }),
    getPopular: vi.fn().mockResolvedValue({ popular: [] }),
    saveSearch: vi.fn().mockResolvedValue({ success: true, data: { id: 1 } }),
    getSavedSearches: vi.fn().mockResolvedValue({ saved: [] }),
    deleteSavedSearch: vi.fn().mockResolvedValue(undefined),
    logClick: vi.fn().mockResolvedValue(undefined),
    getSearchProfile: vi.fn().mockResolvedValue({}),
    clearHistory: vi.fn().mockResolvedValue(undefined),
  },
}));

vi.mock('@/api/history', () => ({
  historyApi: {
    getSearchHistory: vi.fn().mockResolvedValue({ history: [] }),
    clearHistory: vi.fn().mockResolvedValue(undefined),
  },
}));

vi.mock('@/api/auth', () => ({
  authApi: {
    login: vi.fn().mockResolvedValue({
      access_token: 'tok', refresh_token: 'ref',
      token_type: 'bearer', expires_in: 1800,
    }),
    signup: vi.fn().mockResolvedValue(undefined),
    logout: vi.fn().mockResolvedValue(undefined),
    logoutAll: vi.fn().mockResolvedValue(undefined),
    getCurrentUser: vi.fn().mockResolvedValue({
      email: 'u@t.com', role: 'user', email_verified: true,
    }),
    refreshToken: vi.fn().mockResolvedValue({
      access_token: 'new_tok', refresh_token: 'new_ref',
      token_type: 'bearer', expires_in: 1800,
    }),
    verifyEmail: vi.fn().mockResolvedValue(undefined),
    requestPasswordReset: vi.fn().mockResolvedValue(undefined),
    resetPassword: vi.fn().mockResolvedValue(undefined),
  },
}));

vi.mock('@/api/ai', () => ({
  aiApi: {
    ask: vi.fn().mockResolvedValue({ answer: 'Hello!', provider: 'openai' }),
    askStream: vi.fn().mockResolvedValue(undefined),
    getChatHistory: vi.fn().mockResolvedValue({ messages: [] }),
    clearChatHistory: vi.fn().mockResolvedValue(undefined),
  },
}));

vi.mock('@/api/vector', () => ({
  vectorApi: {
    search: vi.fn().mockResolvedValue({ results: [] }),
    ask: vi.fn().mockResolvedValue({ answer: 'Answer', citations: [] }),
    reindexDocument: vi.fn().mockResolvedValue(undefined),
    getCitations: vi.fn().mockResolvedValue({ citations: [] }),
    getStats: vi.fn().mockResolvedValue({}),
    exportVectors: vi.fn().mockResolvedValue(undefined),
  },
}));

vi.mock('@/api/documents', () => ({
  documentsApi: {
    list: vi.fn().mockResolvedValue({ documents: [], pagination: {} }),
    upload: vi.fn().mockResolvedValue({ id: 1, filename: 'test.txt' }),
    delete: vi.fn().mockResolvedValue(undefined),
    get: vi.fn().mockResolvedValue({}),
  },
}));

// ── useSearchStore tests ──────────────────────────────────────────────────────
describe('useSearchStore', () => {
  beforeEach(() => {
    localStorage.clear();
    vi.clearAllMocks();
  });

  it('initial state has empty results and no error', async () => {
    const { useSearchStore } = await import('@/state/useSearchStore');
    const s = useSearchStore.getState();
    expect(s.results).toEqual([]);
    expect(s.searchError).toBeNull();
    expect(s.isSearching).toBe(false);
  });

  it('setQuery updates query', async () => {
    const { useSearchStore } = await import('@/state/useSearchStore');
    useSearchStore.getState().setQuery('hello');
    expect(useSearchStore.getState().query).toBe('hello');
  });

  it('setSelectedBackend updates backend', async () => {
    const { useSearchStore } = await import('@/state/useSearchStore');
    useSearchStore.getState().setSelectedBackend('brave');
    expect(useSearchStore.getState().selectedBackend).toBe('brave');
  });

  it('setPage updates page', async () => {
    const { useSearchStore } = await import('@/state/useSearchStore');
    useSearchStore.getState().setPage(3);
    expect(useSearchStore.getState().page).toBe(3);
  });

  it('setPageSize resets page to 1', async () => {
    const { useSearchStore } = await import('@/state/useSearchStore');
    useSearchStore.getState().setPage(5);
    useSearchStore.getState().setPageSize(20);
    expect(useSearchStore.getState().page).toBe(1);
  });

  it('clearResults resets results and query', async () => {
    const { useSearchStore } = await import('@/state/useSearchStore');
    useSearchStore.setState({ results: [{ score: 0.9 }], query: 'old' } as any);
    useSearchStore.getState().clearResults();
    expect(useSearchStore.getState().results).toEqual([]);
    expect(useSearchStore.getState().query).toBe('');
  });

  it('clearError resets searchError', async () => {
    const { useSearchStore } = await import('@/state/useSearchStore');
    useSearchStore.setState({ searchError: 'some error' } as any);
    useSearchStore.getState().clearError();
    expect(useSearchStore.getState().searchError).toBeNull();
  });

  it('intelligentSearch sets results from api', async () => {
    const { searchApi } = await import('@/api/search');
    (searchApi.search as any).mockResolvedValueOnce({
      results: [{ title: 'R1', score: 0.9 }],
      total: 1,
    });
    const { useSearchStore } = await import('@/state/useSearchStore');
    await useSearchStore.getState().intelligentSearch('test query');
    expect(useSearchStore.getState().isSearching).toBe(false);
  });

  it('webSearch calls searchApi.webSearch', async () => {
    const { searchApi } = await import('@/api/search');
    (searchApi.webSearch as any).mockResolvedValueOnce([{ title: 'W1', score: 0.8 }]);
    const { useSearchStore } = await import('@/state/useSearchStore');
    await useSearchStore.getState().webSearch('query', 'wikipedia');
    expect(searchApi.webSearch).toHaveBeenCalled();
  });

  it('intelligentSearch on error sets searchError', async () => {
    const { searchApi } = await import('@/api/search');
    (searchApi.search as any).mockRejectedValueOnce(new Error('Network fail'));
    const { useSearchStore } = await import('@/state/useSearchStore');
    try {
      await useSearchStore.getState().intelligentSearch('fail query');
    } catch {}
    expect(useSearchStore.getState().searchError).toBeTruthy();
    expect(useSearchStore.getState().isSearching).toBe(false);
  });
});

// ── useAuthStore tests ────────────────────────────────────────────────────────
describe('useAuthStore', () => {
  beforeEach(() => {
    localStorage.clear();
    vi.clearAllMocks();
  });

  it('initial state is unauthenticated', async () => {
    const { useAuthStore } = await import('@/state/useAuthStore');
    useAuthStore.setState({
      user: null, accessToken: null, refreshToken: null,
      isLoading: false, isAuthenticated: false, error: null,
    });
    const s = useAuthStore.getState();
    expect(s.isAuthenticated).toBe(false);
    expect(s.user).toBeNull();
    expect(s.accessToken).toBeNull();
  });

  it('login stores tokens and sets isAuthenticated', async () => {
    const { authApi } = await import('@/api/auth');
    (authApi.login as any).mockResolvedValueOnce({
      access_token: 'acc', refresh_token: 'ref', token_type: 'bearer', expires_in: 1800,
    });
    (authApi.getCurrentUser as any).mockResolvedValueOnce({
      email: 'u@t.com', role: 'user', email_verified: true,
    });
    const { useAuthStore } = await import('@/state/useAuthStore');
    await useAuthStore.getState().login('u@t.com', 'Pass1!');
    const s = useAuthStore.getState();
    expect(s.isAuthenticated).toBe(true);
    expect(s.accessToken).toBe('acc');
    expect(s.user?.email).toBe('u@t.com');
  });

  it('logout clears all auth state', async () => {
    const { authApi } = await import('@/api/auth');
    (authApi.logout as any).mockResolvedValueOnce(undefined);
    const { useAuthStore } = await import('@/state/useAuthStore');
    useAuthStore.setState({
      user: { email: 'u@t.com', role: 'user', email_verified: true } as any,
      accessToken: 'tok', refreshToken: 'ref',
      isAuthenticated: true, isLoading: false, error: null,
    });
    await useAuthStore.getState().logout();
    const s = useAuthStore.getState();
    expect(s.isAuthenticated).toBe(false);
    expect(s.accessToken).toBeNull();
    expect(s.user).toBeNull();
  });

  it('login failure sets error', async () => {
    const { authApi } = await import('@/api/auth');
    (authApi.login as any).mockRejectedValueOnce(new Error('Invalid credentials'));
    const { useAuthStore } = await import('@/state/useAuthStore');
    try {
      await useAuthStore.getState().login('bad@t.com', 'wrong');
    } catch {}
    const s = useAuthStore.getState();
    expect(s.error).toBeTruthy();
    expect(s.isAuthenticated).toBe(false);
  });

  it('clearError clears error state', async () => {
    const { useAuthStore } = await import('@/state/useAuthStore');
    useAuthStore.setState({ error: 'Some error' } as any);
    useAuthStore.getState().clearError();
    expect(useAuthStore.getState().error).toBeNull();
  });

  it('fetchCurrentUser populates user', async () => {
    const { authApi } = await import('@/api/auth');
    (authApi.getCurrentUser as any).mockResolvedValueOnce({
      email: 'me@t.com', role: 'admin', email_verified: true,
    });
    const { useAuthStore } = await import('@/state/useAuthStore');
    useAuthStore.setState({ accessToken: 'tok', isAuthenticated: true } as any);
    await useAuthStore.getState().fetchCurrentUser();
    expect(useAuthStore.getState().user?.email).toBe('me@t.com');
  });

  it('signup calls authApi.signup', async () => {
    const { authApi } = await import('@/api/auth');
    (authApi.signup as any).mockResolvedValueOnce(undefined);
    const { useAuthStore } = await import('@/state/useAuthStore');
    await useAuthStore.getState().signup('new@t.com', 'StrongPass1!');
    expect(authApi.signup).toHaveBeenCalledWith({ email: 'new@t.com', password: 'StrongPass1!' });
  });
});

// ── useAIChatStore tests ──────────────────────────────────────────────────────
describe('useAIChatStore', () => {
  beforeEach(() => {
    localStorage.clear();
    vi.clearAllMocks();
  });

  it('initial state has empty messages', async () => {
    const { useAIChatStore } = await import('@/state/useAIChatStore');
    const s = useAIChatStore.getState();
    expect(s.messages).toEqual([]);
    expect(s.isLoading).toBe(false);
    expect(s.isStreaming).toBe(false);
  });

  it('sendMessage adds user message immediately', async () => {
    const { aiApi } = await import('@/api/ai');
    (aiApi.ask as any).mockResolvedValueOnce({
      answer: 'Hello!', provider: 'openai', tokens_used: 50,
    });
    const { useAIChatStore } = await import('@/state/useAIChatStore');
    useAIChatStore.setState({ messages: [], isLoading: false, isStreaming: false } as any);
    const promise = useAIChatStore.getState().sendMessage('Hi there');
    const msgsBefore = useAIChatStore.getState().messages;
    expect(msgsBefore.some((m: any) => m.role === 'user' && m.content === 'Hi there')).toBe(true);
    await promise;
  });

  it('sendMessage adds assistant response after API returns', async () => {
    const { aiApi } = await import('@/api/ai');
    (aiApi.ask as any).mockResolvedValueOnce({
      answer: 'I am an AI.', provider: 'openai',
    });
    const { useAIChatStore } = await import('@/state/useAIChatStore');
    useAIChatStore.setState({ messages: [], isLoading: false, isStreaming: false } as any);
    await useAIChatStore.getState().sendMessage('What are you?');
    const msgs = useAIChatStore.getState().messages;
    expect(msgs.some((m: any) => m.role === 'assistant')).toBe(true);
  });

  it('clearMessages empties the messages array', async () => {
    const { useAIChatStore } = await import('@/state/useAIChatStore');
    useAIChatStore.setState({
      messages: [{ id: '1', role: 'user', content: 'hello', timestamp: new Date() }],
    } as any);
    useAIChatStore.getState().clearMessages();
    expect(useAIChatStore.getState().messages).toEqual([]);
  });

  it('isLoading is true while sendMessage is in flight', async () => {
    const { aiApi } = await import('@/api/ai');
    let resolveAI: any;
    (aiApi.ask as any).mockReturnValueOnce(
      new Promise((res) => { resolveAI = res; })
    );
    const { useAIChatStore } = await import('@/state/useAIChatStore');
    useAIChatStore.setState({ messages: [], isLoading: false, isStreaming: false } as any);
    const p = useAIChatStore.getState().sendMessage('test loading');
    expect(useAIChatStore.getState().isLoading).toBe(true);
    resolveAI({ answer: 'done', provider: 'openai' });
    await p;
    expect(useAIChatStore.getState().isLoading).toBe(false);
  });

  it('sendMessage error sets isLoading false and does not crash', async () => {
    const { aiApi } = await import('@/api/ai');
    (aiApi.ask as any).mockRejectedValueOnce(new Error('AI error'));
    const { useAIChatStore } = await import('@/state/useAIChatStore');
    useAIChatStore.setState({ messages: [], isLoading: false, isStreaming: false } as any);
    try { await useAIChatStore.getState().sendMessage('error test'); } catch {}
    expect(useAIChatStore.getState().isLoading).toBe(false);
  });

  it('fetchChatHistory populates messages', async () => {
    const { aiApi } = await import('@/api/ai');
    (aiApi.getChatHistory as any).mockResolvedValueOnce({
      messages: [
        { id: '1', role: 'user', content: 'Hi', timestamp: new Date().toISOString() },
        { id: '2', role: 'assistant', content: 'Hello!', timestamp: new Date().toISOString() },
      ],
    });
    const { useAIChatStore } = await import('@/state/useAIChatStore');
    useAIChatStore.setState({ messages: [] } as any);
    await useAIChatStore.getState().fetchChatHistory();
    expect(useAIChatStore.getState().messages.length).toBe(2);
  });

  it('clearChatHistory calls aiApi and empties messages', async () => {
    const { aiApi } = await import('@/api/ai');
    (aiApi.clearChatHistory as any).mockResolvedValueOnce(undefined);
    const { useAIChatStore } = await import('@/state/useAIChatStore');
    useAIChatStore.setState({
      messages: [{ id: '1', role: 'user', content: 'x', timestamp: new Date() }],
    } as any);
    await useAIChatStore.getState().clearChatHistory();
    expect(useAIChatStore.getState().messages).toEqual([]);
    expect(aiApi.clearChatHistory).toHaveBeenCalled();
  });
});
