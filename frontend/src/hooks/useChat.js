import { useCallback, useEffect, useState } from 'react';
import { useAuth } from '../auth/AuthContext';

export function useChat() {
  const { api, isAuthenticated } = useAuth();
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const load = useCallback(async () => {
    if (!isAuthenticated) {
      setMessages([]);
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const data = await api.chatHistory();
      setMessages(data.messages || []);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, [api, isAuthenticated]);

  const clear = useCallback(async () => {
    if (!isAuthenticated) return;
    try {
      await api.clearChat();
      setMessages([]);
    } catch (err) {
      setError(err.message);
    }
  }, [api, isAuthenticated]);

  useEffect(() => {
    load();
  }, [load]);

  return { messages, loading, error, reload: load, clear };
}
