import { apiClient } from './client';
import { DocumentResponse, DocumentListResponse, ExportResponse, ExportListResponse, SettingsResponse, SettingsUpdateRequest } from '@/types';

export interface UploadDocumentParams {
  file: File;
  onProgress?: (progress: number) => void;
}

export const storageApi = {
  async getDocuments(): Promise<DocumentListResponse> {
    return apiClient.get<DocumentListResponse>('/documents');
  },

  async uploadDocument(params: UploadDocumentParams): Promise<DocumentResponse> {
    const { file, onProgress } = params;
    return apiClient.upload<DocumentResponse>('/documents', file, onProgress);
  },

  async deleteDocument(documentId: number): Promise<{ message: string }> {
    return apiClient.delete(`/documents/${documentId}`);
  },

  async getSettings(): Promise<SettingsResponse> {
    return apiClient.get<SettingsResponse>('/storage/settings');
  },

  async updateSettings(settings: SettingsUpdateRequest): Promise<SettingsResponse> {
    return apiClient.put<SettingsResponse>('/storage/settings', settings);
  },

  async createExport(exportType: string, data?: Record<string, any>): Promise<ExportResponse> {
    return apiClient.post<ExportResponse>('/storage/exports', { export_type: exportType, data });
  },

  async getExports(): Promise<ExportListResponse> {
    return apiClient.get<ExportListResponse>('/storage/exports');
  }
};
