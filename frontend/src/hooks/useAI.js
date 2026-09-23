import { useCallback, useRef, useState } from 'react';
import { useAuth } from '../auth/AuthContext';

export function useAI() {
  const { api, isAuthenticated } = useAuth();
  const [answer, setAnswer] = useState(null);
  const [provider, setProvider] = useState(null);
  const [loading, setLoading] = useState(false);
  const [streaming, setStreaming] = useState(false);
  const [error, setError] = useState(null);
  const abortRef = useRef(false);

  const ask = useCallback(
    async (prompt, { stream = true } = {}) => {
      if (!prompt.trim()) return;
      abortRef.current = false;
      setLoading(true);
      setStreaming(false);
      setError(null);
      setAnswer(null);
      setProvider(null);

      try {
        if (isAuthenticated && stream && api.aiAskStream) {
          setStreaming(true);
          let accumulated = '';
          await api.aiAskStream(prompt, {
            onChunk: (chunk) => {
              if (abortRef.current) return;
              accumulated += chunk;
              setAnswer(accumulated);
            },
            onDone: () => {
              setProvider('stream');
              setStreaming(false);
            },
            onError: (err) => setError(err.message),
          });
          if (!accumulated) {
            const data = await api.aiAsk(prompt);
            setAnswer(data.answer);
            setProvider(data.provider);
          }
        } else if (isAuthenticated) {
          const data = await api.aiAsk(prompt);
          setAnswer(data.answer);
          setProvider(data.provider);
        } else {
          const res = await fetch(
            `https://api.duckduckgo.com/?q=${encodeURIComponent(prompt)}&format=json&no_redirect=1&t=Nebula`
          );
          const json = await res.json();
          setAnswer(json.AbstractText || json.Answer || 'No instant answer available.');
          setProvider('duckduckgo');
        }
      } catch (err) {
        setError(err.message || 'AI request failed');
        setAnswer(null);
      } finally {
        setLoading(false);
        setStreaming(false);
      }
    },
    [api, isAuthenticated]
  );

  const cancel = useCallback(() => {
    abortRef.current = true;
    setStreaming(false);
    setLoading(false);
  }, []);

  return { answer, provider, loading, streaming, error, ask, cancel };
}
