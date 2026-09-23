import { create } from 'zustand';
import { persist, createJSONStorage } from 'zustand/middleware';
import { SettingsResponse } from '@/types';
import { storageApi } from '@/api/storage';

interface SettingsState {
  settings: SettingsResponse | null;
  theme: 'light' | 'dark' | 'system';
  language: string;
  isLoading: boolean;
  error: string | null;
}

interface SettingsActions {
  fetchSettings: () => Promise<void>;
  updateSettings: (settings: Record<string, any>) => Promise<void>;
  setTheme: (theme: 'light' | 'dark' | 'system') => void;
  setLanguage: (language: string) => void;
  clearError: () => void;
}

type SettingsStore = SettingsState & SettingsActions;

export const useSettingsStore = create<SettingsStore>()(
  persist(
    (set, get) => ({
      // Initial state
      settings: null,
      theme: 'system',
      language: 'en',
      isLoading: false,
      error: null,

      // Actions
      fetchSettings: async () => {
        try {
          set({ isLoading: true, error: null });
          const settings = await storageApi.getSettings();
          set({ settings, isLoading: false });
        } catch (error) {
          set({
            error: error instanceof Error ? error.message : 'Failed to fetch settings',
            isLoading: false,
          });
          throw error;
        }
      },

      updateSettings: async (newSettings: Record<string, any>) => {
        try {
          set({ isLoading: true, error: null });
          const settings = await storageApi.updateSettings({ settings: newSettings });
          set({ settings, isLoading: false });
        } catch (error) {
          set({
            error: error instanceof Error ? error.message : 'Failed to update settings',
            isLoading: false,
          });
          throw error;
        }
      },

      setTheme: (theme: 'light' | 'dark' | 'system') => {
        set({ theme });
        // Apply theme to document
        const root = window.document.documentElement;
        if (theme === 'dark') {
          root.classList.add('dark');
        } else if (theme === 'light') {
          root.classList.remove('dark');
        } else {
          // System preference
          if (window.matchMedia('(prefers-color-scheme: dark)').matches) {
            root.classList.add('dark');
          } else {
            root.classList.remove('dark');
          }
        }
      },

      setLanguage: (language: string) => {
        set({ language });
      },

      clearError: () => {
        set({ error: null });
      },
    }),
    {
      name: 'settings-storage',
      storage: createJSONStorage(() => localStorage),
      partialize: (state) => ({
        theme: state.theme,
        language: state.language,
      }),
    }
  )
);