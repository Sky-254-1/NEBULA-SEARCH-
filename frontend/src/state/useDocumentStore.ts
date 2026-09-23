import { create } from 'zustand';
import { persist, createJSONStorage } from 'zustand/middleware';
import { DocumentResponse, ExportResponse } from '@/types';
import { storageApi } from '@/api/storage';

interface DocumentState {
  documents: DocumentResponse[];
  currentDocument: DocumentResponse | null;
  exports: ExportResponse[];
  isLoading: boolean;
  error: string | null;
  uploadProgress: number;
}

interface DocumentActions {
  fetchDocuments: () => Promise<void>;
  uploadDocument: (file: File) => Promise<void>;
  deleteDocument: (documentId: number) => Promise<void>;
  fetchExports: () => Promise<void>;
  createExport: (exportType: string, data?: Record<string, any>) => Promise<void>;
  setCurrentDocument: (document: DocumentResponse | null) => void;
  clearError: () => void;
  setUploadProgress: (progress: number) => void;
}

type DocumentStore = DocumentState & DocumentActions;

export const useDocumentStore = create<DocumentStore>()(
  persist(
    (set, get) => ({
      // Initial state
      documents: [],
      currentDocument: null,
      exports: [],
      isLoading: false,
      error: null,
      uploadProgress: 0,

      // Actions
      fetchDocuments: async () => {
        try {
          set({ isLoading: true, error: null });
          const response = await storageApi.getDocuments();
          set({ documents: response.documents || [], isLoading: false });
        } catch (error) {
          set({
            error: error instanceof Error ? error.message : 'Failed to fetch documents',
            isLoading: false,
          });
          throw error;
        }
      },

      uploadDocument: async (file: File) => {
        try {
          set({ isLoading: true, error: null, uploadProgress: 0 });
          
          const document = await storageApi.uploadDocument({
            file,
            onProgress: (progress) => {
              set({ uploadProgress: progress });
            },
          });
          
          set((state) => ({
            documents: [document, ...state.documents],
            isLoading: false,
            uploadProgress: 100,
          }));
          
          // Reset progress after a delay
          setTimeout(() => {
            set({ uploadProgress: 0 });
          }, 2000);
        } catch (error) {
          set({
            error: error instanceof Error ? error.message : 'Failed to upload document',
            isLoading: false,
            uploadProgress: 0,
          });
          throw error;
        }
      },

      deleteDocument: async (documentId: number) => {
        try {
          set({ isLoading: true, error: null });
          await storageApi.deleteDocument(documentId);
          set((state) => ({
            documents: state.documents.filter((doc) => doc.id !== documentId),
            isLoading: false,
          }));
        } catch (error) {
          set({
            error: error instanceof Error ? error.message : 'Failed to delete document',
            isLoading: false,
          });
          throw error;
        }
      },

      fetchExports: async () => {
        try {
          const response = await storageApi.getExports();
          set({ exports: response.exports });
        } catch (error) {
          console.error('Failed to fetch exports:', error);
        }
      },

      createExport: async (exportType: string, data?: Record<string, any>) => {
        try {
          set({ isLoading: true, error: null });
          const export_ = await storageApi.createExport(exportType, data);
          set((state) => ({
            exports: [export_, ...state.exports],
            isLoading: false,
          }));
        } catch (error) {
          set({
            error: error instanceof Error ? error.message : 'Failed to create export',
            isLoading: false,
          });
          throw error;
        }
      },

      setCurrentDocument: (document: DocumentResponse | null) => {
        set({ currentDocument: document });
      },

      clearError: () => {
        set({ error: null });
      },

      setUploadProgress: (progress: number) => {
        set({ uploadProgress: progress });
      },
    }),
    {
      name: 'document-storage',
      storage: createJSONStorage(() => localStorage),
      partialize: (state) => ({
        documents: state.documents,
        exports: state.exports,
      }),
    }
  )
);