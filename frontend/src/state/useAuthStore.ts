import { create } from 'zustand';
import { persist, createJSONStorage } from 'zustand/middleware';
import { UserInfo, AuthResponse } from '@/types';
import { authApi } from '@/api/auth';

interface AuthState {
  user: UserInfo | null;
  accessToken: string | null;
  refreshToken: string | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  error: string | null;
}

interface AuthActions {
  login: (email: string, password: string) => Promise<void>;
  signup: (email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  logoutAll: () => Promise<void>;
  refreshTokenAction: () => Promise<void>;
  fetchCurrentUser: () => Promise<void>;
  clearError: () => void;
  setLoading: (loading: boolean) => void;
}

type AuthStore = AuthState & AuthActions;

export const useAuthStore = create<AuthStore>()(
  persist(
    (set, get) => ({
      // Initial state
      user: null,
      accessToken: null,
      refreshToken: null,
      isLoading: false,
      isAuthenticated: false,
      error: null,

      // Actions
      login: async (email: string, password: string) => {
        try {
          set({ isLoading: true, error: null });
          const response: AuthResponse = await authApi.login({ email, password });
          
          set({
            accessToken: response.access_token,
            refreshToken: response.refresh_token,
            isAuthenticated: true,
            isLoading: false,
          });

          // Fetch actual user data
          await get().fetchCurrentUser();
        } catch (error) {
          set({
            error: error instanceof Error ? error.message : 'Login failed',
            isLoading: false,
            isAuthenticated: false,
          });
          throw error;
        }
      },

      signup: async (email: string, password: string) => {
        try {
          set({ isLoading: true, error: null });
          await authApi.signup({ email, password });
          set({ isLoading: false });
        } catch (error) {
          set({
            error: error instanceof Error ? error.message : 'Signup failed',
            isLoading: false,
          });
          throw error;
        }
      },

      logout: async () => {
        try {
          set({ isLoading: true });
          await authApi.logout();
        } catch (error) {
          console.error('Logout error:', error);
        } finally {
          set({
            user: null,
            accessToken: null,
            refreshToken: null,
            isAuthenticated: false,
            isLoading: false,
            error: null,
          });
        }
      },

      logoutAll: async () => {
        try {
          set({ isLoading: true });
          await authApi.logoutAll();
        } catch (error) {
          console.error('Logout all error:', error);
        } finally {
          set({
            user: null,
            accessToken: null,
            refreshToken: null,
            isAuthenticated: false,
            isLoading: false,
            error: null,
          });
        }
      },

      refreshTokenAction: async () => {
        const { refreshToken } = get();
        if (!refreshToken) {
          throw new Error('No refresh token available');
        }

        try {
          const response: AuthResponse = await authApi.refreshToken({ refresh_token: refreshToken });
          set({
            accessToken: response.access_token,
            refreshToken: response.refresh_token,
            isAuthenticated: true,
          });
        } catch (error) {
          // Refresh failed, clear auth
          set({
            user: null,
            accessToken: null,
            refreshToken: null,
            isAuthenticated: false,
            error: 'Session expired',
          });
          throw error;
        }
      },

      fetchCurrentUser: async () => {
        try {
          const user = await authApi.getCurrentUser();
          set({ user });
        } catch (error) {
          console.error('Failed to fetch user:', error);
          // If we can't fetch user, we might need to refresh token
          const { refreshToken } = get();
          if (refreshToken) {
            try {
              await get().refreshTokenAction();
              // Retry fetching user
              const user = await authApi.getCurrentUser();
              set({ user });
            } catch (refreshError) {
              console.error('Token refresh failed:', refreshError);
              await get().logout();
            }
          }
        }
      },

      clearError: () => {
        set({ error: null });
      },

      setLoading: (loading: boolean) => {
        set({ isLoading: loading });
      },
    }),
    {
      name: 'auth-storage',
      storage: createJSONStorage(() => localStorage),
      partialize: (state) => ({
        accessToken: state.accessToken,
        refreshToken: state.refreshToken,
        user: state.user,
        isAuthenticated: state.isAuthenticated,
      }),
    }
  )
);