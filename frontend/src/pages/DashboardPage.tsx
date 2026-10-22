import React, { useEffect } from 'react';
import { motion } from 'framer-motion';
import {
  Search,
  Upload,
  MessageSquare,
  BarChart3,
  TrendingUp,
  Clock,
  FileText,
  Activity,
} from 'lucide-react';
import { useAuthStore } from '@/state';
import { useSearchStore } from '@/state';
import { useDocumentStore } from '@/state';
import { useAIChatStore } from '@/state';
import { useAnalyticsStore } from '@/state';

export const DashboardPage: React.FC = () => {
  const { user } = useAuthStore();
  const { searchHistory, fetchSearchHistory } = useSearchStore();
  const { documents, fetchDocuments } = useDocumentStore();
  const { messages } = useAIChatStore();
  const { usageStats, fetchUsageStats } = useAnalyticsStore();

  useEffect(() => {
    fetchSearchHistory();
    fetchDocuments();
    fetchUsageStats();
  }, [fetchSearchHistory, fetchDocuments, fetchUsageStats]);

  const stats = [
    {
      label: 'Total Searches',
      value: usageStats?.total_searches || 0,
      icon: Search,
      color: 'blue',
      change: '+12%',
    },
    {
      label: 'Documents',
      value: usageStats?.total_documents || 0,
      icon: FileText,
      color: 'green',
      change: '+5%',
    },
    {
      label: 'AI Queries',
      value: usageStats?.total_ai_queries || 0,
      icon: MessageSquare,
      color: 'purple',
      change: '+8%',
    },
    {
      label: 'Daily Average',
      value: usageStats?.daily_average || 0,
      icon: TrendingUp,
      color: 'orange',
      change: '+3%',
    },
  ];

  const recentSearches = searchHistory.slice(0, 5);
  const recentDocuments = documents.slice(0, 5);

  return (
    <div className="space-y-6">
      {/* Welcome section */}
      <div>
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
          Welcome back, {user?.email?.split('@')[0]}!
        </h1>
        <p className="mt-2 text-gray-600 dark:text-gray-300">
          Here's what's happening with your searches today.
        </p>
      </div>

      {/* Stats grid — 2 cols on mobile, 2 on tablet, 4 on desktop */}
      <div className="grid grid-cols-2 sm:grid-cols-2 lg:grid-cols-4 gap-3 sm:gap-6">
        {stats.map((stat, index) => {
          const Icon = stat.icon;
          return (
            <motion.div
              key={stat.label}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: index * 0.1 }}
              className="bg-white dark:bg-gray-800 rounded-xl p-4 sm:p-6 shadow-sm border border-gray-200 dark:border-gray-700"
            >
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-600 dark:text-gray-400">
                    {stat.label}
                  </p>
                  <p className="text-2xl font-bold text-gray-900 dark:text-white mt-1">
                    {stat.value}
                  </p>
                  <p className="text-sm text-green-600 mt-1">
                    {stat.change}
                  </p>
                </div>
                <div className={`p-3 rounded-lg bg-${stat.color}-100 dark:bg-${stat.color}-900/20`}>
                  <Icon className={`text-${stat.color}-600 dark:text-${stat.color}-400`} size={24} />
                </div>
              </div>
            </motion.div>
          );
        })}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 sm:gap-6">
        {/* Recent Searches */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="bg-white dark:bg-gray-800 rounded-xl p-6 shadow-sm border border-gray-200 dark:border-gray-700"
        >
          <div className="flex items-center gap-2 mb-4">
            <Clock className="text-gray-600 dark:text-gray-400" size={20} />
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
              Recent Searches
            </h3>
          </div>
          <div className="space-y-3">
            {recentSearches.length > 0 ? (
              recentSearches.map((search) => (
                <div
                  key={search.id}
                  className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-700 rounded-lg"
                >
                  <div className="flex-1">
                    <p className="text-sm font-medium text-gray-900 dark:text-white">
                      {search.query}
                    </p>
                    <p className="text-xs text-gray-500 dark:text-gray-400">
                      {search.backend} • {search.result_count} results
                    </p>
                  </div>
                  <span className="text-xs text-gray-500 dark:text-gray-400">
                    {new Date(search.created_at).toLocaleDateString()}
                  </span>
                </div>
              ))
            ) : (
              <p className="text-sm text-gray-500 dark:text-gray-400 text-center py-4">
                No recent searches
              </p>
            )}
          </div>
        </motion.div>

        {/* Recent Documents */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
          className="bg-white dark:bg-gray-800 rounded-xl p-6 shadow-sm border border-gray-200 dark:border-gray-700"
        >
          <div className="flex items-center gap-2 mb-4">
            <Upload className="text-gray-600 dark:text-gray-400" size={20} />
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
              Recent Documents
            </h3>
          </div>
          <div className="space-y-3">
            {recentDocuments.length > 0 ? (
              recentDocuments.map((doc) => (
                <div
                  key={doc.id}
                  className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-700 rounded-lg"
                >
                  <div className="flex items-center gap-3">
                    <FileText className="text-gray-400" size={20} />
                    <div>
                      <p className="text-sm font-medium text-gray-900 dark:text-white">
                        {doc.filename}
                      </p>
                      <p className="text-xs text-gray-500 dark:text-gray-400">
                        {doc.content_type || 'Unknown type'}
                      </p>
                    </div>
                  </div>
                  <span className="text-xs text-gray-500 dark:text-gray-400">
                    {new Date(doc.created_at).toLocaleDateString()}
                  </span>
                </div>
              ))
            ) : (
              <p className="text-sm text-gray-500 dark:text-gray-400 text-center py-4">
                No documents uploaded yet
              </p>
            )}
          </div>
        </motion.div>
      </div>

      {/* Quick Actions */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.4 }}
        className="bg-white dark:bg-gray-800 rounded-xl p-6 shadow-sm border border-gray-200 dark:border-gray-700"
      >
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
          Quick Actions
        </h3>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 sm:gap-4">
          <a
            href="/search"
            className="flex items-center gap-3 p-4 bg-blue-50 dark:bg-blue-900/20 rounded-lg hover:bg-blue-100 dark:hover:bg-blue-900/30 transition-colors"
          >
            <Search className="text-blue-600 dark:text-blue-400" size={24} />
            <div>
              <p className="font-medium text-gray-900 dark:text-white">New Search</p>
              <p className="text-sm text-gray-600 dark:text-gray-400">Search the web</p>
            </div>
          </a>
          <a
            href="/ai-chat"
            className="flex items-center gap-3 p-4 bg-purple-50 dark:bg-purple-900/20 rounded-lg hover:bg-purple-100 dark:hover:bg-purple-900/30 transition-colors"
          >
            <MessageSquare className="text-purple-600 dark:text-purple-400" size={24} />
            <div>
              <p className="font-medium text-gray-900 dark:text-white">AI Chat</p>
              <p className="text-sm text-gray-600 dark:text-gray-400">Ask AI anything</p>
            </div>
          </a>
          <a
            href="/documents"
            className="flex items-center gap-3 p-4 bg-green-50 dark:bg-green-900/20 rounded-lg hover:bg-green-100 dark:hover:bg-green-900/30 transition-colors"
          >
            <Upload className="text-green-600 dark:text-green-400" size={24} />
            <div>
              <p className="font-medium text-gray-900 dark:text-white">Upload Document</p>
              <p className="text-sm text-gray-600 dark:text-gray-400">Add to library</p>
            </div>
          </a>
        </div>
      </motion.div>
    </div>
  );
};