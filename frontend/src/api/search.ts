import { apiClient } from './client';
import {
  SearchResult,
  IntelligentSearchResponse,
  SuggestionsResponse,
  AutocompleteResponse,
  SpellCheckResponse,
  TrendingResponse,
  PopularResponse,
  SearchProfile,
  SearchHistoryItem,
} from '@/types';

export interface SearchParams {
  q: string;
  backends?: string;
  page?: number;
  page_size?: number;
  enable_semantic?: boolean;
  enable_personalization?: boolean;
  enable_spell_check?: boolean;
  enable_diversity?: boolean;
  mode?: 'web' | 'vector' | 'hybrid' | 'ai';
  include_ai_answer?: boolean;
  include_suggestions?: boolean;
  facets?: string[];
}

export interface LegacySearchParams {
  q: string;
  backend?: string;
}

export const searchApi = {
  // ── Main unified search (POST /api/v1/search/) ──────────────────────────
  async search(params: SearchParams): Promise<any> {
    return apiClient.post('/api/v1/search/', {
      query: params.q,
      mode: params.mode ?? 'hybrid',
      page: params.page ?? 1,
      limit: params.page_size ?? 20,
      include_ai_answer: params.include_ai_answer ?? true,
      include_suggestions: params.include_suggestions ?? true,
      spell_check: params.enable_spell_check ?? true,
      include_highlights: true,
      facets: params.facets ?? null,
    });
  },

  // ── Intelligent search v2 (GET /api/v2/search/) ────────────────────────
  async intelligentSearch(params: SearchParams): Promise<IntelligentSearchResponse> {
    return apiClient.get<IntelligentSearchResponse>('/api/v2/search/', {
      q: params.q,
      backends: params.backends ?? 'wikipedia',
      page: params.page ?? 1,
      page_size: params.page_size ?? 20,
      enable_semantic: params.enable_semantic ?? true,
      enable_personalization: params.enable_personalization ?? true,
      enable_spell_check: params.enable_spell_check ?? true,
      enable_diversity: params.enable_diversity ?? true,
    });
  },

  // ── Suggestions & autocomplete ─────────────────────────────────────────
  async getSuggestions(q: string, limit: number = 10): Promise<SuggestionsResponse> {
    return apiClient.get<SuggestionsResponse>('/api/v1/search/suggestions', { q, limit });
  },

  async autocomplete(q: string, limit: number = 10): Promise<AutocompleteResponse> {
    return apiClient.get<AutocompleteResponse>('/api/v2/search/autocomplete', { q, limit });
  },

  async spellCheck(q: string): Promise<SpellCheckResponse> {
    return apiClient.get<SpellCheckResponse>('/api/v2/search/spell-check', { q });
  },

  // ── Trending & popular ─────────────────────────────────────────────────
  async getTrending(limit: number = 10, hours: number = 24): Promise<TrendingResponse> {
    return apiClient.get<TrendingResponse>('/api/v2/search/trending', { limit, hours });
  },

  async getPopular(limit: number = 10): Promise<PopularResponse> {
    return apiClient.get<PopularResponse>('/api/v2/search/popular', { limit });
  },

  // ── Search history ─────────────────────────────────────────────────────
  async getSearchHistory(limit: number = 20): Promise<{ history: SearchHistoryItem[] }> {
    const resp = await apiClient.get<{ success: boolean; data: { history: SearchHistoryItem[] } }>(
      '/api/v1/search/history',
      { limit },
    );
    // Unwrap the success wrapper if present
    return { history: (resp as any)?.data?.history ?? (resp as any)?.history ?? [] };
  },

  async clearHistory(): Promise<void> {
    await apiClient.delete('/api/v1/search/history');
  },

  // ── Saved searches ─────────────────────────────────────────────────────
  async saveSearch(
    query: string,
    mode: string = 'hybrid',
    filters?: Record<string, any>,
  ): Promise<any> {
    const params: Record<string, any> = { query, mode };
    if (filters) params.filters = JSON.stringify(filters);
    return apiClient.post('/api/v1/search/save', null, { params });
  },

  async getSavedSearches(): Promise<any> {
    const resp = await apiClient.get<{ success: boolean; data: { saved: any[] } }>(
      '/api/v1/search/saved',
    );
    return (resp as any)?.data?.saved ?? [];
  },

  async deleteSavedSearch(searchId: number): Promise<void> {
    await apiClient.delete(`/api/v1/search/saved/${searchId}`);
  },

  // ── Analytics click tracking ───────────────────────────────────────────
  async logClick(
    query: string,
    position: number,
    url: string,
    sessionId?: string,
  ): Promise<void> {
    await apiClient.post(
      '/api/v2/search/click',
      null,
      { params: { query, position, url, session_id: sessionId } },
    );
  },

  // ── Search profile ─────────────────────────────────────────────────────
  async getSearchProfile(): Promise<SearchProfile> {
    return apiClient.get<SearchProfile>('/api/v2/search/profile');
  },

  // ── Legacy web search (GET /api/v1/search/web) ────────────────────────
  async webSearch(params: LegacySearchParams): Promise<SearchResult[]> {
    try {
      const response = await apiClient.get<{ results?: SearchResult[] }>(
        '/api/v1/search/web',
        { q: params.q, backend: params.backend },
      );
      return response.results ?? [];
    } catch {
      return [];
    }
  },
};
