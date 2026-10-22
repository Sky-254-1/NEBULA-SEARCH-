import { create } from 'zustand';
import { NotificationResponse } from '@/types';
import { featuresApi } from '@/api/features';

interface NotificationState {
  notifications: NotificationResponse[];
  unreadCount: number;
  isLoading: boolean;
  error: string | null;
}

interface NotificationActions {
  fetchNotifications: (limit?: number) => Promise<void>;
  markAsRead: (notificationId: number) => Promise<void>;
  markAllAsRead: () => Promise<void>;
  clearError: () => void;
}

type NotificationStore = NotificationState & NotificationActions;

export const useNotificationStore = create<NotificationStore>((set, get) => ({
  // Initial state
  notifications: [],
  unreadCount: 0,
  isLoading: false,
  error: null,

  // Actions
  fetchNotifications: async (limit: number = 50) => {
    try {
      set({ isLoading: true, error: null });
      const response = await featuresApi.getNotifications(limit);
      set({ 
        notifications: response.notifications, 
        unreadCount: response.unread_count,
        isLoading: false 
      });
    } catch (error) {
      set({
        error: error instanceof Error ? error.message : 'Failed to fetch notifications',
        isLoading: false,
      });
      throw error;
    }
  },

  markAsRead: async (notificationId: number) => {
    try {
      await featuresApi.markNotificationRead(notificationId);
      set((state) => ({
        notifications: state.notifications.map((notification) =>
          notification.id === notificationId
            ? { ...notification, is_read: true }
            : notification
        ),
        unreadCount: Math.max(0, state.unreadCount - 1),
      }));
    } catch (error) {
      set({
        error: error instanceof Error ? error.message : 'Failed to mark notification as read',
      });
      throw error;
    }
  },

  markAllAsRead: async () => {
    try {
      await featuresApi.markAllNotificationsRead();
      set((state) => ({
        notifications: state.notifications.map((notification) => ({
          ...notification,
          is_read: true,
        })),
        unreadCount: 0,
      }));
    } catch (error) {
      set({
        error: error instanceof Error ? error.message : 'Failed to mark all notifications as read',
      });
      throw error;
    }
  },

  clearError: () => {
    set({ error: null });
  },
}));