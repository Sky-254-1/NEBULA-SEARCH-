import { apiClient } from './client';
import { AuthRequest, AuthResponse, UserInfo, RefreshRequest } from '@/types';

export const authApi = {
  login: async (data: AuthRequest): Promise<AuthResponse> => {
    return apiClient.login(data.email, data.password);
  },

  signup: async (data: AuthRequest): Promise<void> => {
    return apiClient.signup(data.email, data.password);
  },

  logout: async (): Promise<void> => {
    return apiClient.logout();
  },

  logoutAll: async (): Promise<void> => {
    return apiClient.logoutAll();
  },

  refreshToken: async (data: RefreshRequest): Promise<AuthResponse> => {
    return apiClient.post<AuthResponse>('/auth/refresh', data);
  },

  getCurrentUser: async (): Promise<UserInfo> => {
    return apiClient.get<UserInfo>('/auth/me');
  },

  verifyEmail: async (token: string): Promise<void> => {
    // Backend creates verification token but frontend endpoint may vary
    return apiClient.post('/auth/verify-email', { token });
  },

  requestPasswordReset: async (email: string): Promise<void> => {
    return apiClient.post('/auth/forgot-password', { email });
  },

  resetPassword: async (token: string, newPassword: string): Promise<void> => {
    return apiClient.post('/auth/reset-password', { token, new_password: newPassword });
  },
};
