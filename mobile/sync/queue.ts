import { Preferences } from '@capacitor/preferences';
import { config } from '../src/config';

export type SyncJob = {
  id: string;
  type: 'upload' | 'search' | 'export';
  payload: Record<string, unknown>;
  createdAt: string;
};

export async function enqueueJob(job: Omit<SyncJob, 'createdAt'>) {
  const queue = await getQueue();
  queue.push({ ...job, createdAt: new Date().toISOString() });
  await Preferences.set({ key: config.syncQueueKey, value: JSON.stringify(queue) });
}

export async function getQueue(): Promise<SyncJob[]> {
  const { value } = await Preferences.get({ key: config.syncQueueKey });
  return value ? JSON.parse(value) : [];
}

export async function flushQueue(apiBase: string, token: string) {
  const queue = await getQueue();
  const remaining: SyncJob[] = [];
  for (const job of queue) {
    try {
      if (job.type === 'search') {
        await fetch(`${apiBase}/api/v1/search/web?${new URLSearchParams(job.payload as Record<string, string>)}`, {
          headers: { Authorization: `Bearer ${token}` },
        });
      }
    } catch {
      remaining.push(job);
    }
  }
  await Preferences.set({ key: config.syncQueueKey, value: JSON.stringify(remaining) });
}
