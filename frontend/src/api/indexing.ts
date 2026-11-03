import { apiClient } from './client';
import { APIResponse, PaginationMeta } from '@/types';

export type IndexingJobStatus =
  | 'QUEUED'
  | 'RUNNING'
  | 'RETRYING'
  | 'COMPLETED'
  | 'FAILED'
  | 'CANCELLED';

export interface IndexingJob {
  job_id: string;
  document_id: number;
  status: IndexingJobStatus;
  progress?: number;
  current_step?: string;
  error_message?: string | null;
  retry_count?: number;
}

export interface IndexingJobPage {
  jobs: IndexingJob[];
  pagination: PaginationMeta;
}

export const indexingApi = {
  start(documentId: number): Promise<APIResponse<{ job_id: string }>> {
    return apiClient.post<APIResponse<{ job_id: string }>>(
      '/indexing/jobs',
      { document_id: documentId },
    );
  },

  list(page = 1, pageSize = 20): Promise<APIResponse<IndexingJobPage>> {
    return apiClient.get<APIResponse<IndexingJobPage>>(
      '/indexing/jobs',
      { page, page_size: pageSize },
    );
  },

  get(jobId: string): Promise<APIResponse<IndexingJob>> {
    return apiClient.get<APIResponse<IndexingJob>>(
      `/indexing/jobs/${encodeURIComponent(jobId)}`,
    );
  },

  cancel(jobId: string): Promise<APIResponse<{ job_id: string }>> {
    return apiClient.post<APIResponse<{ job_id: string }>>(
      `/indexing/jobs/${encodeURIComponent(jobId)}/cancel`,
    );
  },

  retry(jobId: string): Promise<APIResponse<{ job_id: string; status: IndexingJobStatus }>> {
    return apiClient.post<APIResponse<{ job_id: string; status: IndexingJobStatus }>>(
      `/indexing/jobs/${encodeURIComponent(jobId)}/retry`,
    );
  },
};
