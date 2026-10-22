import { openDB, DBSchema, IDBPDatabase } from 'idb';
import { QueuedAction } from '@/types';

interface NebulaDB extends DBSchema {
  'search-cache': {
    key: string;
    value: {
      query: string;
      results: any[];
      timestamp: number;
    };
  };
  'upload-queue': {
    key: string;
    value: QueuedAction;
  };
  'chat-history': {
    key: number;
    value: {
      id: number;
      messages: any[];
      timestamp: number;
    };
  };
}

class OfflineService {
  private db: IDBPDatabase<NebulaDB> | null = null;
  private isOnline: boolean = navigator.onLine;

  async init() {
    this.db = await openDB<NebulaDB>('nebula-offline', 1, {
      upgrade(db) {
        // Search cache store
        if (!db.objectStoreNames.contains('search-cache')) {
          db.createObjectStore('search-cache', { keyPath: 'query' });
        }

        // Upload queue store
        if (!db.objectStoreNames.contains('upload-queue')) {
          db.createObjectStore('upload-queue', { keyPath: 'id' });
        }

        // Chat history store
        if (!db.objectStoreNames.contains('chat-history')) {
          const chatStore = db.createObjectStore('chat-history', { keyPath: 'id', autoIncrement: true });
          (chatStore as any).createIndex('timestamp', 'timestamp', { unique: false });
        }
      },
    });

    // Listen for online/offline events
    window.addEventListener('online', () => this.handleOnline());
    window.addEventListener('offline', () => this.handleOffline());
  }

  private handleOnline() {
    this.isOnline = true;
    this.syncQueuedActions();
  }

  private handleOffline() {
    this.isOnline = false;
  }

  getOnlineStatus(): boolean {
    return this.isOnline;
  }

  // Search cache methods
  async cacheSearchResults(query: string, results: any[]): Promise<void> {
    if (!this.db) return;
    
    await this.db.put('search-cache', {
      query,
      results,
      timestamp: Date.now(),
    });
  }

  async getCachedSearchResults(query: string): Promise<any[] | null> {
    if (!this.db) return null;
    
    const cached = await this.db.get('search-cache', query);
    if (!cached) return null;

    // Cache expires after 1 hour
    const isExpired = Date.now() - cached.timestamp > 3600000;
    if (isExpired) {
      await this.db.delete('search-cache', query);
      return null;
    }

    return cached.results;
  }

  // Upload queue methods
  async queueUpload(action: Omit<QueuedAction, 'id' | 'timestamp' | 'retries' | 'status'>): Promise<void> {
    if (!this.db) return;

    const queuedAction: QueuedAction = {
      ...action,
      id: crypto.randomUUID(),
      timestamp: Date.now(),
      retries: 0,
      status: 'pending',
    };

    await this.db.add('upload-queue', queuedAction);
  }

  async getQueuedActions(): Promise<QueuedAction[]> {
    if (!this.db) return [];
    
    const actions = await this.db.getAll('upload-queue');
    return actions.filter(action => action.status === 'pending');
  }

  async updateQueuedAction(id: string, updates: Partial<QueuedAction>): Promise<void> {
    if (!this.db) return;
    
    const action = await this.db.get('upload-queue', id);
    if (action) {
      await this.db.put('upload-queue', { ...action, ...updates });
    }
  }

  async removeQueuedAction(id: string): Promise<void> {
    if (!this.db) return;
    
    await this.db.delete('upload-queue', id);
  }

  // Chat history methods
  async saveChatHistory(messages: any[]): Promise<void> {
    if (!this.db) return;
    
    await this.db.put('chat-history', {
      id: 1, // Single chat history per user
      messages,
      timestamp: Date.now(),
    });
  }

  async getChatHistory(): Promise<any[] | null> {
    if (!this.db) return null;
    
    const history = await this.db.get('chat-history', 1);
    return history?.messages || null;
  }

  async clearChatHistory(): Promise<void> {
    if (!this.db) return;
    
    await this.db.delete('chat-history', 1);
  }

  // Sync queued actions when back online
  private async syncQueuedActions(): Promise<void> {
    const queuedActions = await this.getQueuedActions();
    
    for (const action of queuedActions) {
      try {
        // TODO: Implement actual sync logic based on action type
        console.log('Syncing action:', action);
        await this.removeQueuedAction(action.id);
      } catch (error) {
        console.error('Failed to sync action:', action, error);
        await this.updateQueuedAction(action.id, {
          retries: action.retries + 1,
          status: action.retries >= 3 ? 'failed' : 'pending',
        });
      }
    }
  }

  // Clear all data
  async clearAll(): Promise<void> {
    if (!this.db) return;
    
    await this.db.clear('search-cache');
    await this.db.clear('upload-queue');
    await this.db.clear('chat-history');
  }
}

// Export singleton instance
export const offlineService = new OfflineService();
export default offlineService;