import { create } from 'zustand';
import { QueuedAction } from '@/types';

interface OfflineState {
  isOnline: boolean;
  queuedActions: QueuedAction[];
  syncInProgress: boolean;
}

interface OfflineActions {
  setOnlineStatus: (isOnline: boolean) => void;
  addQueuedAction: (action: Omit<QueuedAction, 'id' | 'timestamp' | 'retries' | 'status'>) => void;
  updateQueuedAction: (id: string, updates: Partial<QueuedAction>) => void;
  removeQueuedAction: (id: string) => void;
  setSyncInProgress: (inProgress: boolean) => void;
  clearQueue: () => void;
}

type OfflineStore = OfflineState & OfflineActions;

export const useOfflineStore = create<OfflineStore>((set, get) => ({
  // Initial state
  isOnline: navigator.onLine,
  queuedActions: [],
  syncInProgress: false,

  // Actions
  setOnlineStatus: (isOnline: boolean) => {
    set({ isOnline });
  },

  addQueuedAction: (action) => {
    const queuedAction: QueuedAction = {
      ...action,
      id: crypto.randomUUID(),
      timestamp: Date.now(),
      retries: 0,
      status: 'pending',
    };
    set((state) => ({
      queuedActions: [...state.queuedActions, queuedAction],
    }));
  },

  updateQueuedAction: (id: string, updates: Partial<QueuedAction>) => {
    set((state) => ({
      queuedActions: state.queuedActions.map((action) =>
        action.id === id ? { ...action, ...updates } : action
      ),
    }));
  },

  removeQueuedAction: (id: string) => {
    set((state) => ({
      queuedActions: state.queuedActions.filter((action) => action.id !== id),
    }));
  },

  setSyncInProgress: (inProgress: boolean) => {
    set({ syncInProgress: inProgress });
  },

  clearQueue: () => {
    set({ queuedActions: [] });
  },
}));