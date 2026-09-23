import { Capacitor } from '@capacitor/core';

export const isNative = Capacitor.isNativePlatform();

export const config = {
  apiBase: import.meta.env?.VITE_API_URL || 'http://localhost:8000',
  offlineCacheKey: 'nebula_offline_cache',
  syncQueueKey: 'nebula_sync_queue',
};
