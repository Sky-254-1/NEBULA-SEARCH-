import { create } from 'zustand';
import { UsageStats, SearchAnalytics, PerformanceMetrics } from '@/types';
import { analyticsApi } from '@/api/analytics';

interface AnalyticsState {
  usageStats: UsageStats | null;
  searchAnalytics: SearchAnalytics | null;
  performanceMetrics: PerformanceMetrics | null;
  isLoading: boolean;
  error: string | null;
}

interface AnalyticsActions {
  fetchUsageStats: (periodDays?: number) => Promise<void>;
  fetchSearchAnalytics: (periodDays?: number) => Promise<void>;
  fetchPerformanceMetrics: (periodDays?: number) => Promise<void>;
  clearError: () => void;
}

type AnalyticsStore = AnalyticsState & AnalyticsActions;

export const useAnalyticsStore = create<AnalyticsStore>((set, get) => ({
  // Initial state
  usageStats: null,
  searchAnalytics: null,
  performanceMetrics: null,
  isLoading: false,
  error: null,

  // Actions
  fetchUsageStats: async (periodDays: number = 30) => {
    try {
      set({ isLoading: true, error: null });
      const stats = await analyticsApi.getUsageStats({ period_days: periodDays });
      set({ usageStats: stats, isLoading: false });
    } catch (error) {
      set({
        error: error instanceof Error ? error.message : 'Failed to fetch usage stats',
        isLoading: false,
      });
      throw error;
    }
  },

  fetchSearchAnalytics: async (periodDays: number = 30) => {
    try {
      set({ isLoading: true, error: null });
      const analytics = await analyticsApi.getSearchAnalytics({ period_days: periodDays });
      set({ searchAnalytics: analytics, isLoading: false });
    } catch (error) {
      set({
        error: error instanceof Error ? error.message : 'Failed to fetch search analytics',
        isLoading: false,
      });
      throw error;
    }
  },

  fetchPerformanceMetrics: async (periodDays: number = 7) => {
    try {
      set({ isLoading: true, error: null });
      const metrics = await analyticsApi.getPerformanceMetrics({ period_days: periodDays });
      set({ performanceMetrics: metrics, isLoading: false });
    } catch (error) {
      set({
        error: error instanceof Error ? error.message : 'Failed to fetch performance metrics',
        isLoading: false,
      });
      throw error;
    }
  },

  clearError: () => {
    set({ error: null });
  },
}));