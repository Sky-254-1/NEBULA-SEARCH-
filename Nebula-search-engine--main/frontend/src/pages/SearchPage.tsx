import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Search as SearchIcon, Filter, X, Loader2, ChevronDown, Lock } from 'lucide-react';
import { useSearchStore } from '@/state';
import { useAuth } from '@/context/AuthContext';
import { SearchResult } from '@/types';

export const SearchPage: React.FC = () => {
  const { query, results, isSearching, searchError, intelligentSearch, setQuery } = useSearchStore();
  const [localQuery, setLocalQuery] = useState(query);
  const [showFilters, setShowFilters] = useState(false);
  const { isGuest, guestFeatures } = useAuth();

  useEffect(() => {
    setLocalQuery(query);
  }, [query]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!localQuery.trim()) return;

    await intelligentSearch(localQuery, {
      enable_semantic: true,
      enable_personalization: true,
    });
  };

  const displayResults = results;

  return (
    <div className="w-full max-w-4xl mx-auto space-y-4 sm:space-y-6 px-2 sm:px-0">
      {/* Search Header */}
      <div>
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-2">
          Search
        </h1>
        <p className="text-gray-600 dark:text-gray-300">
          Search the web with AI-powered semantic understanding
        </p>
      </div>

      {/* Search Form */}
      <form onSubmit={handleSubmit} className="space-y-4">
        <div className="relative">
          <SearchIcon className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400" size={20} />
          <input
            type="text"
            value={localQuery}
            onChange={(e) => setLocalQuery(e.target.value)}
            placeholder={isGuest ? `Guest mode: ${guestFeatures.maxSearchesPerDay} searches/day` : "Search for anything..."}
            className="w-full pl-12 pr-4 py-4 text-lg border border-gray-300 dark:border-gray-600 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent dark:bg-gray-800 dark:text-white"
          />
          {isSearching && (
            <div className="absolute right-4 top-1/2 -translate-y-1/2">
              <Loader2 className="animate-spin text-blue-600" size={24} />
            </div>
          )}
        </div>

        <div className="flex gap-3">
          <button
            type="submit"
            disabled={isSearching || !localQuery.trim()}
            className="flex-1 bg-blue-600 text-white py-2 px-6 rounded-lg font-medium hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {isSearching ? 'Searching...' : 'Search'}
          </button>
          
          <button
            type="button"
            onClick={() => setShowFilters(!showFilters)}
            className="bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-300 py-2 px-4 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-700 transition-colors"
          >
            <Filter size={20} />
          </button>
        </div>
        {isGuest && (
          <p className="text-xs text-gray-500 dark:text-gray-400">
            Guest mode: Unlimited searches. Sign up to unlock AI Chat, Documents, and more.
          </p>
        )}
      </form>

      {/* Filters */}
      {showFilters && (
        <motion.div
          initial={{ opacity: 0, height: 0 }}
          animate={{ opacity: 1, height: 'auto' }}
          className="bg-white dark:bg-gray-800 rounded-xl p-6 border border-gray-200 dark:border-gray-700"
        >
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-semibold text-gray-900 dark:text-white">Filters</h3>
            <button
              onClick={() => setShowFilters(false)}
              className="text-gray-400 hover:text-gray-600"
            >
              <X size={20} />
            </button>
          </div>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Results per page
              </label>
              <select className="w-full bg-gray-50 dark:bg-gray-700 border border-gray-300 dark:border-gray-600 rounded-lg px-3 py-2 text-gray-900 dark:text-white">
                <option value="10">10 results</option>
                <option value="20">20 results</option>
                <option value="50">50 results</option>
              </select>
            </div>
          </div>
        </motion.div>
      )}

      {/* Error */}
      {searchError && (
        <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-xl p-4">
          <p className="text-red-600 dark:text-red-400">{searchError}</p>
        </div>
      )}

      {/* Results */}
      {displayResults.length > 0 && (
        <div className="space-y-4">
          <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
            Found {results.length} results
            {isGuest && (
              <span className="ml-2 text-xs text-gray-500 dark:text-gray-400 font-normal">
                (Guest preview)
              </span>
            )}
          </h2>

          <div className="space-y-4">
            {displayResults.map((result: SearchResult, index: number) => {
              // Support both web results (title/url/snippet) and
              // vector/document results (filename/content/score).
              const heading = result.title || result.filename || 'Untitled';
              const body = result.snippet || result.content || '';
              const displayUrl = result.url;
              const displayScore = result.combined_score ?? result.score;

              return (
                <motion.div
                  key={index}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: index * 0.05 }}
                  className="bg-white dark:bg-gray-800 rounded-xl p-6 border border-gray-200 dark:border-gray-700 hover:shadow-md transition-shadow"
                >
                  <div className="flex items-start justify-between gap-4">
                    <div className="flex-1">
                      {displayUrl ? (
                        <a
                          href={displayUrl}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-lg font-semibold text-blue-600 dark:text-blue-400 mb-1 hover:underline block"
                        >
                          {heading}
                        </a>
                      ) : (
                        <h3 className="text-lg font-semibold text-blue-600 dark:text-blue-400 mb-1">
                          {heading}
                        </h3>
                      )}
                      {displayUrl && (
                        <p className="text-xs text-green-700 dark:text-green-500 mb-2 truncate">
                          {displayUrl}
                        </p>
                      )}
                      {body && (
                        <p className="text-gray-700 dark:text-gray-300 mb-3 line-clamp-3">
                          {body}
                        </p>
                      )}
                      <div className="flex items-center gap-4 text-sm text-gray-500 dark:text-gray-400">
                        <span>Score: {(displayScore * 100).toFixed(1)}%</span>
                        {result.vector_score != null && (
                          <span>Vector: {(result.vector_score * 100).toFixed(1)}%</span>
                        )}
                        {result.keyword_score != null && (
                          <span>Keyword: {(result.keyword_score * 100).toFixed(1)}%</span>
                        )}
                      </div>
                    </div>
                  </div>
                </motion.div>
              );
            })}
          </div>
        </div>
      )}

      {/* Empty State */}
      {!isSearching && displayResults.length === 0 && !searchError && (
        <div className="text-center py-12">
          <SearchIcon className="mx-auto text-gray-400 mb-4" size={48} />
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
            Start searching
          </h3>
          <p className="text-gray-600 dark:text-gray-300">
            Enter a query above to search the web
          </p>
        </div>
      )}
    </div>
  );
};