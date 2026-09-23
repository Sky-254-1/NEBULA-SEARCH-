import { apiClient } from './client';
import { NotificationResponse, NotificationListResponse } from '@/types';

export const notificationsApi = {
  // List notifications
  list: async (limit: number = 50): Promise<NotificationListResponse> => {
    return apiClient.get<NotificationListResponse>('/notifications', { limit });
  },

  // Mark notification as read
  markAsRead: async (id: number): Promise<void> => {
    return apiClient.post(`/notifications/${id}/read`);
  },

  // Mark all notifications as read
  markAllAsRead: async (): Promise<void> => {
    return apiClient.post('/notifications/read-all');
  },
};