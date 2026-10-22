import { apiClient } from './client';

export interface SearchHistoryItem {
  id: number;
  query: string;
  backend: string;
  result_count: number;
  created_at: string;
}

export interface ChatHistoryItem {
  role: 'user' | 'assistant';
  content: string;
  timestamp?: string;
}

export interface SearchHistoryResponse {
  history: SearchHistoryItem[];
}

export interface ChatHistoryResponse {
  messages: ChatHistoryItem[];
}

export const historyApi = {
  // Search history
  getSearchHistory: async (limit: number = 20): Promise<SearchHistoryResponse> => {
    return apiClient.get<SearchHistoryResponse>('/search/history', { limit });
  },

  clearSearchHistory: async (): Promise<void> => {
    return apiClient.delete('/search/history');
  },

  deleteSearchHistoryItem: async (id: number): Promise<void> => {
    // Backend doesn't support deleting individual items, so we clear all
    // In a future enhancement, this could be implemented
    console.warn('Delete individual search history item not supported by backend');
  },

  // Chat history
  getChatHistory: async (): Promise<ChatHistoryResponse> => {
    return apiClient.get<ChatHistoryResponse>('/ai/chat/history');
  },

  clearChatHistory: async (): Promise<void> => {
    return apiClient.delete('/ai/chat/history');
  },
};