import { getApiBase } from './base';

export function createAiApi(authedFetch, getTokens, setTokens) {
  return {
    aiAsk: (prompt) =>
      authedFetch('/ai/ask', { method: 'POST', body: JSON.stringify({ prompt }) }),
    aiSynthesize: (query, snippets) =>
      authedFetch('/ai/synthesize', {
        method: 'POST',
        body: JSON.stringify({ query, snippets }),
      }),
    chatHistory: () => authedFetch('/ai/chat/history'),
    clearChat: () => authedFetch('/ai/chat/history', { method: 'DELETE' }),
    aiAskStream: async (prompt, { onChunk, onDone, onError } = {}) => {
      const tokens = getTokens();
      const headers = { 'Content-Type': 'application/json' };
      if (tokens?.access_token) {
        headers.Authorization = `Bearer ${tokens.access_token}`;
      }

      let response = await fetch(`${getApiBase()}/ai/ask/stream`, {
        method: 'POST',
        headers,
        body: JSON.stringify({ prompt }),
      });

      if (response.status === 401 && tokens?.refresh_token) {
        const refreshRes = await fetch(`${getApiBase()}/auth/refresh`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ refresh_token: tokens.refresh_token }),
        });
        if (refreshRes.ok) {
          const refreshed = await refreshRes.json();
          setTokens(refreshed);
          headers.Authorization = `Bearer ${refreshed.access_token}`;
          response = await fetch(`${getApiBase()}/ai/ask/stream`, {
            method: 'POST',
            headers,
            body: JSON.stringify({ prompt }),
          });
        }
      }

      if (!response.ok) {
        const err = new Error(response.statusText);
        onError?.(err);
        throw err;
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() || '';
        for (const line of lines) {
          if (!line.startsWith('data: ')) continue;
          const payload = line.slice(6);
          if (payload === '[DONE]') {
            onDone?.();
            return;
          }
          try {
            const { chunk } = JSON.parse(payload);
            if (chunk) onChunk?.(chunk);
          } catch {
            /* ignore malformed SSE */
          }
        }
      }
      onDone?.();
    },
  };
}
