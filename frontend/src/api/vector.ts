import { apiClient } from './client';
import { VectorSearchRequest, VectorSearchResponse, VectorAskResponse, Citation, DocumentIndexStatusResponse } from '@/types';

export interface VectorAskParams {
  query: string;
  top_k?: number;
}

export interface VectorSearchParams {
  query: string;
  top_k?: number;
  filters?: Record<string, any>;
}

export interface ReindexParams {
  limit?: number;
}

export const vectorApi = {
  async search(params: VectorSearchParams): Promise<VectorSearchResponse> {
    return apiClient.post<VectorSearchResponse>('/vector/search', params);
  },

  async ask(params: VectorAskParams): Promise<VectorAskResponse> {
    return apiClient.post<VectorAskResponse>('/vector/ask', params);
  },

  async getDocumentStatus(documentId: number): Promise<DocumentIndexStatusResponse> {
    return apiClient.get<DocumentIndexStatusResponse>(`/vector/documents/${documentId}/status`);
  },

  async reindexDocument(documentId: number): Promise<{ message: string; document_id: number }> {
    return apiClient.post(`/vector/documents/${documentId}/reindex`);
  },

  async reindexAll(params?: ReindexParams): Promise<{ message: string; count: number }> {
    return apiClient.post('/vector/documents/reindex-all', params || {});
  },

  async getCitations(): Promise<{ citations: Citation[]; pagination?: any }> {
    return apiClient.get('/vector/citations');
  },

  async getStats(): Promise<{ chunks: number; documents_indexed: number }> {
    return apiClient.get('/vector/stats');
  },

  async exportVectors(): Promise<{ export_id: number; path: string; chunk_count: number }> {
    return apiClient.post('/vector/export');
  }
};