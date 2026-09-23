import { apiClient } from './client';
import { SavedSearchResponse, SavedSearchCreate, SavedSearchListResponse } from '@/types';

export const savedSearchesApi = {
  // List saved searches
  list: async (): Promise<SavedSearchListResponse> => {
    return apiClient.get<SavedSearchListResponse>('/saved-searches');
  },

  // Create saved search
  create: async (data: SavedSearchCreate): Promise<SavedSearchResponse> => {
    return apiClient.post<SavedSearchResponse>('/saved-searches', data);
  },

  // Delete saved search
  delete: async (id: number): Promise<void> => {
    return apiClient.delete(`/saved-searches/${id}`);
  },
};