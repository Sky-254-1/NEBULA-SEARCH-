import { apiClient } from './client';
import { BookmarkResponse, BookmarkCreate, BookmarkUpdate, BookmarkListResponse } from '@/types';

export const bookmarksApi = {
  // List bookmarks
  list: async (limit: number = 50): Promise<BookmarkListResponse> => {
    return apiClient.get<BookmarkListResponse>('/bookmarks', { limit });
  },

  // Search bookmarks
  search: async (q: string): Promise<BookmarkListResponse> => {
    return apiClient.get<BookmarkListResponse>('/bookmarks/search', { q });
  },

  // Create bookmark
  create: async (data: BookmarkCreate): Promise<BookmarkResponse> => {
    return apiClient.post<BookmarkResponse>('/bookmarks', data);
  },

  // Update bookmark
  update: async (id: number, data: BookmarkUpdate): Promise<BookmarkResponse> => {
    return apiClient.put<BookmarkResponse>(`/bookmarks/${id}`, data);
  },

  // Delete bookmark
  delete: async (id: number): Promise<void> => {
    return apiClient.delete(`/bookmarks/${id}`);
  },
};