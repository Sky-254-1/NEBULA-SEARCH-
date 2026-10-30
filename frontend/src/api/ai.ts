import { apiClient } from './client';
import { APIError } from '@/types';
import { AIResponse, ChatMessage, ChatHistoryResponse, SynthesizeRequest, SynthesizeResponse } from '@/types';

export const aiApi = {
  async ask(prompt: string): Promise<AIResponse> {
    return apiClient.post<AIResponse>('/ai/ask', { prompt });
  },

  async askStream(prompt: string, onChunk: (chunk: string) => void): Promise<void> {
    // Use the same auth token handling as the apiClient
    const token = localStorage.getItem('access_token');
    const csrfToken = document.cookie.split('; ')
      .find((cookie) => cookie.startsWith('csrf_token='))
      ?.slice('csrf_token='.length);
    const baseURL = apiClient['client'].defaults.baseURL || '/api/v1';
    const response = await fetch(`${baseURL}/ai/ask/stream`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...(csrfToken ? { 'X-CSRF-Token': decodeURIComponent(csrfToken) } : {}),
        ...(token ? { 'Authorization': `Bearer ${token}` } : {}),
      },
      credentials: 'include',
      body: JSON.stringify({ prompt }),
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      const error = new Error(errorData.detail || 'Stream request failed') as any;
      // Attach structured error info for interceptor handling
      if (response.status === 401) {
        error.status = 401;
        try {
          const refreshed = await fetch(`${baseURL}/auth/refresh`, {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
              ...(csrfToken ? { 'X-CSRF-Token': decodeURIComponent(csrfToken) } : {}),
            },
            credentials: 'include',
            body: JSON.stringify({}),
          });
          if (!refreshed.ok) throw error;
          const tokens = await refreshed.json();
          apiClient.setAccessToken(tokens.access_token);
          return this.askStream(prompt, onChunk);
        } catch {
          window.location.href = '/login';
          throw error;
        }
      }
      throw error;
    }

    const reader = response.body?.getReader();
    if (!reader) {
      throw new Error('No reader available');
    }

    const decoder = new TextDecoder();
    let buffer = '';

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split('\n');
      buffer = lines.pop() || '';

      for (const line of lines) {
        if (line.startsWith('data: ')) {
          const data = line.slice(6);
          if (data === '[DONE]') {
            return;
          }
          try {
            const parsed = JSON.parse(data);
            if (parsed.chunk) {
              onChunk(parsed.chunk);
            }
          } catch {
            // Ignore parse errors
          }
        }
      }
    }
  },

  async getChatHistory(): Promise<ChatHistoryResponse> {
    return apiClient.get<ChatHistoryResponse>('/ai/chat/history');
  },

  async clearChatHistory(): Promise<void> {
    await apiClient.delete('/ai/chat/history');
  },

  async synthesize(query: string, snippets: string[]): Promise<SynthesizeResponse> {
    return apiClient.post<SynthesizeResponse>('/ai/synthesize', { query, snippets });
  }
};
