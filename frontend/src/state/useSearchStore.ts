import { create } from 'zustand';
import { persist, createJSONStorage } from 'zustand/middleware';
import { SearchResult, SearchHistoryItem, OrchestratedSearchResponse } from '@/types';
import { searchApi } from '@/api/search';
import { historyApi } from '@/api/history';

interface SearchState {
  // Current search
  query: string;
  results: SearchResult[];
  isSearching: boolean;
  searchError: string | null;
  
  // Search history
  searchHistory: SearchHistoryItem[];
  
  // Filters
  selectedBackend: string;
  page: number;
  pageSize: number;
  
  // Orchestrated search
  orchestratedResults: OrchestratedSearchResponse | null;
}

interface SearchActions {
  setQuery: (query: string) => void;
  setSelectedBackend: (backend: string) => void;
  setPage: (page: number) => void;
  setPageSize: (size: number) => void;
  
  webSearch: (query: string, backend?: string) => Promise<void>;
  orchestratedSearch: (query: string, backends?: string) => Promise<void>;
  intelligentSearch: (query: string, options?: { enable_semantic?: boolean; enable_personalization?: boolean }) => Promise<void>;
  fetchSearchHistory: () => Promise<void>;
  clearResults: () => void;
  clearError: () => void;
}

type SearchStore = SearchState & SearchActions;

export const useSearchStore = create<SearchStore>()(
  persist(
    (set, get) => ({
      // Initial state
      query: '',
      results: [],
      isSearching: false,
      searchError: null,
      searchHistory: [],
      selectedBackend: 'wikipedia',
      page: 1,
      pageSize: 10,
      orchestratedResults: null,

      // Actions
      setQuery: (query: string) => {
        set({ query });
      },

      setSelectedBackend: (backend: string) => {
        set({ selectedBackend: backend });
      },

      setPage: (page: number) => {
        set({ page });
      },

      setPageSize: (size: number) => {
        set({ pageSize: size, page: 1 });
      },

      webSearch: async (query: string, backend?: string) => {
        try {
          set({ isSearching: true, searchError: null, query });
          const results = await searchApi.webSearch({ q: query, backend });
          set({ results, isSearching: false });
        } catch (error) {
          set({
            searchError: error instanceof Error ? error.message : 'Search failed',
            isSearching: false,
          });
          throw error;
        }
      },

      orchestratedSearch: async () => {
        // Kept for compatibility; currently maps to intelligentSearch behavior
      },

      intelligentSearch: async (query: string, options?: { enable_semantic?: boolean; enable_personalization?: boolean }) => {
        try {
          set({ isSearching: true, searchError: null, query });
          const response = await searchApi.search({
            q: query,
            page: 1,
            page_size: get().pageSize,
            enable_semantic: options?.enable_semantic ?? true,
            enable_personalization: options?.enable_personalization ?? true,
          });
          const results = response.results || response.data?.results || [];
          set({ results, isSearching: false });
        } catch (error) {
          set({
            searchError: error instanceof Error ? error.message : 'Search failed',
            isSearching: false,
          });
          throw error;
        }
      },

      fetchSearchHistory: async () => {
        try {
          const response = await historyApi.getSearchHistory(20);
          set({ searchHistory: response.history });
        } catch (error) {
          console.error('Failed to fetch search history:', error);
        }
      },

      clearResults: () => {
        set({
          results: [],
          orchestratedResults: null,
          query: '',
          searchError: null,
        });
      },

      clearError: () => {
        set({ searchError: null });
      },
    }),
    {
      name: 'search-storage',
      storage: createJSONStorage(() => localStorage),
      partialize: (state) => ({
        query: state.query,
        selectedBackend: state.selectedBackend,
        pageSize: state.pageSize,
        searchHistory: state.searchHistory,
      }),
    }
  )
);