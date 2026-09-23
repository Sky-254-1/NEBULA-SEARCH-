import { apiClient } from './client';
import { CollectionResponse, CollectionCreate, CollectionUpdate, CollectionListResponse, CollectionItemCreate, CollectionItemResponse } from '@/types';

export const collectionsApi = {
  // List collections
  list: async (): Promise<CollectionListResponse> => {
    return apiClient.get<CollectionListResponse>('/collections');
  },

  // Get collection by ID
  get: async (id: number): Promise<CollectionResponse> => {
    return apiClient.get<CollectionResponse>(`/collections/${id}`);
  },

  // Create collection
  create: async (data: CollectionCreate): Promise<CollectionResponse> => {
    return apiClient.post<CollectionResponse>('/collections', data);
  },

  // Update collection
  update: async (id: number, data: CollectionUpdate): Promise<CollectionResponse> => {
    return apiClient.put<CollectionResponse>(`/collections/${id}`, data);
  },

  // Delete collection
  delete: async (id: number): Promise<void> => {
    return apiClient.delete(`/collections/${id}`);
  },

  // Add item to collection
  addItem: async (collectionId: number, data: CollectionItemCreate): Promise<CollectionItemResponse> => {
    return apiClient.post<CollectionItemResponse>(`/collections/${collectionId}/items`, data);
  },

  // Remove item from collection
  removeItem: async (collectionId: number, itemId: number): Promise<void> => {
    return apiClient.delete(`/collections/${collectionId}/items/${itemId}`);
  },
};