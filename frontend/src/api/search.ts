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
  UnifiedSearchResponse,
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
  filters?: {
    date_range?: Record<string, string>;
    document_type?: string[];
    tags?: string[];
    source?: string;
  };
}

export interface LegacySearchParams {
  q: string;
  backend?: string;
}

export const searchApi = {
  // ── Main unified search (POST /api/v1/search/) ──────────────────────────
  async search(params: SearchParams): Promise<UnifiedSearchResponse> {
    return apiClient.post<UnifiedSearchResponse>('/search/', {
      query: params.q,
      mode: params.mode ?? 'hybrid',
      page: params.page ?? 1,
      limit: params.page_size ?? 20,
      include_ai_answer: params.include_ai_answer ?? true,
      include_suggestions: params.include_suggestions ?? true,
      spell_check: params.enable_spell_check ?? true,
      include_highlights: true,
      facets: params.facets ?? null,
      filters: params.filters ?? null,
    });
  },

  // ── Intelligent search v2 (GET /api/v2/search/) ────────────────────────
  async intelligentSearch(params: SearchParams): Promise<IntelligentSearchResponse> {
    return apiClient.get<IntelligentSearchResponse>('/v2/search/', {
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
    return apiClient.get<SuggestionsResponse>('/search/suggestions', { q, limit });
  },

  async autocomplete(q: string, limit: number = 10): Promise<AutocompleteResponse> {
    return apiClient.get<AutocompleteResponse>('/v2/search/autocomplete', { q, limit });
  },

  async spellCheck(q: string): Promise<SpellCheckResponse> {
    return apiClient.get<SpellCheckResponse>('/v2/search/spell-check', { q });
  },

  // ── Trending & popular ─────────────────────────────────────────────────
  async getTrending(limit: number = 10, hours: number = 24): Promise<TrendingResponse> {
    return apiClient.get<TrendingResponse>('/v2/search/trending', { limit, hours });
  },

  async getPopular(limit: number = 10): Promise<PopularResponse> {
    return apiClient.get<PopularResponse>('/v2/search/popular', { limit });
  },

  // ── Search history ─────────────────────────────────────────────────────
  async getSearchHistory(limit: number = 20): Promise<{ history: SearchHistoryItem[] }> {
    const resp = await apiClient.get<{ success: boolean; data: { history: SearchHistoryItem[] } }>(
      '/search/history',
      { limit },
    );
    // Unwrap the success wrapper if present
    return { history: (resp as any)?.data?.history ?? (resp as any)?.history ?? [] };
  },

  async clearHistory(): Promise<void> {
    await apiClient.delete('/search/history');
  },

  // ── Saved searches ─────────────────────────────────────────────────────
  async saveSearch(
    query: string,
    mode: string = 'hybrid',
    filters?: Record<string, any>,
  ): Promise<any> {
    const params: Record<string, any> = { query, mode };
    if (filters) params.filters = JSON.stringify(filters);
    return apiClient.post('/search/save', null, { params });
  },

  async getSavedSearches(): Promise<any> {
    const resp = await apiClient.get<{ success: boolean; data: { saved: any[] } }>(
      '/search/saved',
    );
    return (resp as any)?.data?.saved ?? [];
  },

  async deleteSavedSearch(searchId: number): Promise<void> {
    await apiClient.delete(`/search/saved/${searchId}`);
  },

  // ── Analytics click tracking ───────────────────────────────────────────
  async logClick(
    query: string,
    position: number,
    url: string,
    sessionId?: string,
  ): Promise<void> {
    await apiClient.post(
      '/v2/search/click',
      null,
      { params: { query, position, url, session_id: sessionId } },
    );
  },

  // ── Search profile ─────────────────────────────────────────────────────
  async getSearchProfile(): Promise<SearchProfile> {
    return apiClient.get<SearchProfile>('/v2/search/profile');
  },

  // ── Legacy web search (GET /api/v1/search/web) ────────────────────────
  async webSearch(params: LegacySearchParams): Promise<SearchResult[]> {
    try {
      const response = await apiClient.get<{ results?: SearchResult[] }>(
        '/search/web',
        { q: params.q, backend: params.backend },
      );
      return response.results ?? [];
    } catch {
      return [];
    }
  },
};
