import { apiClient } from './client';
import { SavedSearchResponse, SavedSearchListResponse, CollectionResponse, CollectionListResponse, BookmarkResponse, BookmarkListResponse, NotificationResponse, NotificationListResponse } from '@/types';

// ============================================
// Saved Searches
// ============================================
export interface CreateSavedSearchParams {
  query: string;
  filters?: Record<string, any>;
  label?: string;
}

export const featuresApi = {
  // Saved Searches
  async getSavedSearches(): Promise<SavedSearchListResponse> {
    return apiClient.get<SavedSearchListResponse>('/saved-searches');
  },

  async createSavedSearch(params: CreateSavedSearchParams): Promise<SavedSearchResponse> {
    return apiClient.post<SavedSearchResponse>('/saved-searches', params);
  },

  async deleteSavedSearch(searchId: number): Promise<void> {
    return apiClient.delete(`/saved-searches/${searchId}`);
  },

  // Collections
  async getCollections(): Promise<CollectionListResponse> {
    return apiClient.get<CollectionListResponse>('/collections');
  },

  async createCollection(name: string, description?: string, isPublic: boolean = false): Promise<CollectionResponse> {
    return apiClient.post<CollectionResponse>('/collections', { name, description, is_public: isPublic });
  },

  async getCollection(collectionId: number): Promise<CollectionResponse> {
    return apiClient.get<CollectionResponse>(`/collections/${collectionId}`);
  },

  async updateCollection(collectionId: number, updates: { name?: string; description?: string; is_public?: boolean }): Promise<CollectionResponse> {
    return apiClient.put<CollectionResponse>(`/collections/${collectionId}`, updates);
  },

  async deleteCollection(collectionId: number): Promise<void> {
    return apiClient.delete(`/collections/${collectionId}`);
  },

  async addCollectionItem(collectionId: number, documentId?: number, searchResultId?: number, note?: string): Promise<any> {
    return apiClient.post(`/collections/${collectionId}/items`, { document_id: documentId, search_result_id: searchResultId, note });
  },

  async removeCollectionItem(collectionId: number, itemId: number): Promise<void> {
    return apiClient.delete(`/collections/${collectionId}/items/${itemId}`);
  },

  // Bookmarks
  async getBookmarks(limit: number = 50): Promise<BookmarkListResponse> {
    return apiClient.get<BookmarkListResponse>('/bookmarks', { limit });
  },

  async searchBookmarks(query: string): Promise<BookmarkListResponse> {
    return apiClient.get<BookmarkListResponse>('/bookmarks/search', { q: query });
  },

  async createBookmark(title: string, url: string, snippet?: string, tags?: string[]): Promise<BookmarkResponse> {
    return apiClient.post<BookmarkResponse>('/bookmarks', { title, url, snippet, tags });
  },

  async updateBookmark(bookmarkId: number, updates: { title?: string; snippet?: string; tags?: string[] }): Promise<BookmarkResponse> {
    return apiClient.put<BookmarkResponse>(`/bookmarks/${bookmarkId}`, updates);
  },

  async deleteBookmark(bookmarkId: number): Promise<void> {
    return apiClient.delete(`/bookmarks/${bookmarkId}`);
  },

  // Notifications
  async getNotifications(limit: number = 50): Promise<NotificationListResponse> {
    return apiClient.get<NotificationListResponse>('/notifications', { limit });
  },

  async markNotificationRead(notificationId: number): Promise<void> {
    return apiClient.post(`/notifications/${notificationId}/read`);
  },

  async markAllNotificationsRead(): Promise<void> {
    return apiClient.post('/notifications/read-all');
  }
};