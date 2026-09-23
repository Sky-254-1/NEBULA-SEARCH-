import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { BarChart3, TrendingUp, Activity, Clock, FileText, Search } from 'lucide-react';
import { useAnalyticsStore } from '@/state';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

export const AnalyticsPage: React.FC = () => {
  const { usageStats, searchAnalytics, performanceMetrics, isLoading, fetchUsageStats, fetchSearchAnalytics, fetchPerformanceMetrics } = useAnalyticsStore();
  const [period, setPeriod] = useState(30);

  useEffect(() => {
    fetchUsageStats(period);
    fetchSearchAnalytics(period);
    fetchPerformanceMetrics(period);
  }, [period, fetchUsageStats, fetchSearchAnalytics, fetchPerformanceMetrics]);

  // Mock data for charts
  const chartData = [
    { date: '2024-01', searches: 65, documents: 28 },
    { date: '2024-02', searches: 78, documents: 35 },
    { date: '2024-03', searches: 90, documents: 42 },
    { date: '2024-04', searches: 81, documents: 38 },
    { date: '2024-05', searches: 95, documents: 45 },
    { date: '2024-06', searches: 110, documents: 52 },
  ];

  return (
    <div className="max-w-6xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-2">
            Analytics
          </h1>
          <p className="text-gray-600 dark:text-gray-300">
            Track your search and usage metrics
          </p>
        </div>
        <select
          value={period}
          onChange={(e) => setPeriod(Number(e.target.value))}
          className="bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 text-gray-900 dark:text-white py-2 px-4 rounded-lg focus:ring-2 focus:ring-blue-500"
        >
          <option value="7">Last 7 days</option>
          <option value="30">Last 30 days</option>
          <option value="90">Last 90 days</option>
        </select>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="bg-white dark:bg-gray-800 rounded-xl p-6 shadow-sm border border-gray-200 dark:border-gray-700"
        >
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600 dark:text-gray-400">Total Searches</p>
              <p className="text-2xl font-bold text-gray-900 dark:text-white mt-1">
                {usageStats?.total_searches || 0}
              </p>
            </div>
            <Search className="text-blue-600" size={24} />
          </div>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="bg-white dark:bg-gray-800 rounded-xl p-6 shadow-sm border border-gray-200 dark:border-gray-700"
        >
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600 dark:text-gray-400">Documents</p>
              <p className="text-2xl font-bold text-gray-900 dark:text-white mt-1">
                {usageStats?.total_documents || 0}
              </p>
            </div>
            <FileText className="text-green-600" size={24} />
          </div>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="bg-white dark:bg-gray-800 rounded-xl p-6 shadow-sm border border-gray-200 dark:border-gray-700"
        >
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600 dark:text-gray-400">AI Queries</p>
              <p className="text-2xl font-bold text-gray-900 dark:text-white mt-1">
                {usageStats?.total_ai_queries || 0}
              </p>
            </div>
            <Activity className="text-purple-600" size={24} />
          </div>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
          className="bg-white dark:bg-gray-800 rounded-xl p-6 shadow-sm border border-gray-200 dark:border-gray-700"
        >
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600 dark:text-gray-400">Daily Average</p>
              <p className="text-2xl font-bold text-gray-900 dark:text-white mt-1">
                {usageStats?.daily_average || 0}
              </p>
            </div>
            <TrendingUp className="text-orange-600" size={24} />
          </div>
        </motion.div>
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.4 }}
          className="bg-white dark:bg-gray-800 rounded-xl p-6 shadow-sm border border-gray-200 dark:border-gray-700"
        >
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
            Search Activity
          </h3>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" stroke="var(--color-text-dark-muted, #374151)" />
              <XAxis dataKey="date" stroke="var(--color-text-muted, #9CA3AF)" />
              <YAxis stroke="var(--color-text-muted, #9CA3AF)" />
              <Tooltip
                contentStyle={{
                  backgroundColor: 'var(--color-surface-dark-secondary, #1F2937)',
                  border: 'none',
                  borderRadius: '8px',
                  color: 'var(--color-text-dark-primary, #F3F4F6)',
                }}
              />
              <Line type="monotone" dataKey="searches" stroke="var(--color-primary, #3B82F6)" strokeWidth={2} />
            </LineChart>
          </ResponsiveContainer>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.5 }}
          className="bg-white dark:bg-gray-800 rounded-xl p-6 shadow-sm border border-gray-200 dark:border-gray-700"
        >
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
            Document Uploads
          </h3>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" stroke="var(--color-text-dark-muted, #374151)" />
              <XAxis dataKey="date" stroke="var(--color-text-muted, #9CA3AF)" />
              <YAxis stroke="var(--color-text-muted, #9CA3AF)" />
              <Tooltip
                contentStyle={{
                  backgroundColor: 'var(--color-surface-dark-secondary, #1F2937)',
                  border: 'none',
                  borderRadius: '8px',
                  color: 'var(--color-text-dark-primary, #F3F4F6)',
                }}
              />
              <Line type="monotone" dataKey="documents" stroke="var(--color-success, #10B981)" strokeWidth={2} />
            </LineChart>
          </ResponsiveContainer>
        </motion.div>
      </div>

      {/* Top Queries */}
      {searchAnalytics?.top_queries && searchAnalytics.top_queries.length > 0 && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.6 }}
          className="bg-white dark:bg-gray-800 rounded-xl p-6 shadow-sm border border-gray-200 dark:border-gray-700"
        >
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
            Top Queries
          </h3>
          <div className="space-y-3">
            {searchAnalytics.top_queries.map((query, index) => (
              <div
                key={index}
                className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-700 rounded-lg"
              >
                <div className="flex items-center gap-3">
                  <span className="text-sm font-medium text-gray-500 dark:text-gray-400">
                    #{index + 1}
                  </span>
                  <span className="text-gray-900 dark:text-white">{query.query}</span>
                </div>
                <span className="text-sm text-gray-500 dark:text-gray-400">
                  {query.count} searches
                </span>
              </div>
            ))}
          </div>
        </motion.div>
      )}

      {/* Performance Metrics */}
      {performanceMetrics && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.7 }}
          className="bg-white dark:bg-gray-800 rounded-xl p-6 shadow-sm border border-gray-200 dark:border-gray-700"
        >
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
            Performance Metrics
          </h3>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div>
              <p className="text-sm text-gray-600 dark:text-gray-400">Avg Latency</p>
              <p className="text-xl font-bold text-gray-900 dark:text-white">
                {performanceMetrics.avg_latency_ms}ms
              </p>
            </div>
            <div>
              <p className="text-sm text-gray-600 dark:text-gray-400">P95 Latency</p>
              <p className="text-xl font-bold text-gray-900 dark:text-white">
                {performanceMetrics.p95_latency_ms}ms
              </p>
            </div>
            <div>
              <p className="text-sm text-gray-600 dark:text-gray-400">Cache Hit Ratio</p>
              <p className="text-xl font-bold text-gray-900 dark:text-white">
                {(performanceMetrics.cache_hit_ratio * 100).toFixed(1)}%
              </p>
            </div>
            <div>
              <p className="text-sm text-gray-600 dark:text-gray-400">Error Rate</p>
              <p className="text-xl font-bold text-gray-900 dark:text-white">
                {(performanceMetrics.error_rate * 100).toFixed(2)}%
              </p>
            </div>
          </div>
        </motion.div>
      )}
    </div>
  );
};