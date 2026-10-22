import { apiClient } from './client';
import { UsageStats, SearchAnalytics, PerformanceMetrics, AnalyticsExport } from '@/types';

export interface UsageStatsParams {
  period_days?: number;
}

export interface SearchAnalyticsParams {
  period_days?: number;
}

export interface PerformanceMetricsParams {
  period_days?: number;
}

export interface ExportAnalyticsParams {
  export_type?: string;
  period_days?: number;
}

export const analyticsApi = {
  async getUsageStats(params?: UsageStatsParams): Promise<UsageStats> {
    return apiClient.get<UsageStats>('/analytics/usage', params);
  },

  async getSearchAnalytics(params?: SearchAnalyticsParams): Promise<SearchAnalytics> {
    return apiClient.get<SearchAnalytics>('/analytics/search', params);
  },

  async getPerformanceMetrics(params?: PerformanceMetricsParams): Promise<PerformanceMetrics> {
    return apiClient.get<PerformanceMetrics>('/analytics/performance', params);
  },

  async exportAnalytics(params?: ExportAnalyticsParams): Promise<AnalyticsExport> {
    return apiClient.get<AnalyticsExport>('/analytics/export', params);
  }
};