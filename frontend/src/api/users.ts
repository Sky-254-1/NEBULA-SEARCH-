import { apiClient } from './client';
import { 
  UserProfile, 
  UserPreferences, 
  UpdateProfileRequest, 
  ActivityResponse 
} from '@/types';

export interface AvatarUploadResponse {
  success: boolean;
  data: {
    avatar_url: string;
    message: string;
  };
}

export const usersApi = {
  // Get current user profile
  getProfile: async (): Promise<UserProfile> => {
    return apiClient.get<UserProfile>('/users/profile');
  },

  // Update profile
  updateProfile: async (data: UpdateProfileRequest): Promise<UserProfile> => {
    return apiClient.put<UserProfile>('/users/profile', data);
  },

  // Get user preferences
  getPreferences: async (): Promise<UserPreferences> => {
    return apiClient.get<UserPreferences>('/users/preferences');
  },

  // Update preferences
  updatePreferences: async (preferences: Record<string, any>): Promise<UserPreferences> => {
    return apiClient.put<UserPreferences>('/users/preferences', { preferences });
  },

  // Get user activity
  getActivity: async (limit: number = 20, actionType?: string): Promise<ActivityResponse> => {
    const params: Record<string, any> = { limit };
    if (actionType) {
      params.action_type = actionType;
    }
    return apiClient.get<ActivityResponse>('/users/activity', params);
  },

  // Upload avatar
  uploadAvatar: async (file: File): Promise<AvatarUploadResponse> => {
    return apiClient.upload<AvatarUploadResponse>('/users/avatar', file);
  },

  // Delete avatar
  deleteAvatar: async (): Promise<AvatarUploadResponse> => {
    return apiClient.delete<AvatarUploadResponse>('/users/avatar');
  },

  // Delete account
  deleteAccount: async (password: string): Promise<{ success: boolean; data: { message: string } }> => {
    return apiClient.post('/users/account', { password });
  },
};