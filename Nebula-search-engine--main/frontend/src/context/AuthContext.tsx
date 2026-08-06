import React, { createContext, useContext, useEffect, useState } from 'react';
import { apiClient } from '@/api/client';
import { UserInfo, AuthResponse } from '@/types';

interface GuestUser {
  email: string;
  role: 'guest';
  isGuest: true;
}

interface AuthContextType {
  user: UserInfo | GuestUser | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  isGuest: boolean;
  guestFeatures: {
    canUseAIChat: boolean;
    canUseDocuments: boolean;
    canUseHistory: boolean;
    canUseAnalytics: boolean;
    canUseSavedSearches: boolean;
    canUseCollections: boolean;
    canUseBookmarks: boolean;
    maxSearchesPerDay: number;
    maxDocumentsPerDay: number;
    maxAIChatsPerDay: number;
  };
  login: (email: string, password: string) => Promise<AuthResponse>;
  signup: (email: string, password: string) => Promise<void>;
  loginAsGuest: () => Promise<void>;
  logout: () => Promise<void>;
  logoutAll: () => Promise<void>;
  refreshUser: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<UserInfo | GuestUser | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  const isAuthenticated = !!user;
  const isGuest = user?.role === 'guest';

  const guestFeatures = {
    canUseAIChat: false,
    canUseDocuments: false,
    canUseHistory: true,
    canUseAnalytics: false,
    canUseSavedSearches: false,
    canUseCollections: false,
    canUseBookmarks: false,
    maxSearchesPerDay: Infinity,
    maxDocumentsPerDay: 0,
    maxAIChatsPerDay: 0,
  };

  const refreshUser = async () => {
    try {
      const userData = await apiClient.getCurrentUser();
      setUser(userData);
    } catch (error) {
      console.error('Failed to refresh user:', error);
      setUser(null);
    }
  };

  const loginAsGuest = async () => {
    const guestUser: GuestUser = {
      email: 'guest@nebula.search',
      role: 'guest',
      isGuest: true,
    };
    setUser(guestUser);
    localStorage.setItem('guest_mode', 'true');
    localStorage.removeItem('access_token');
  };

  useEffect(() => {
    const initAuth = async () => {
      const token = localStorage.getItem('access_token');
      const isGuestMode = localStorage.getItem('guest_mode') === 'true';
      
      if (isGuestMode) {
        const guestUser: GuestUser = {
          email: 'guest@nebula.search',
          role: 'guest',
          isGuest: true,
        };
        setUser(guestUser);
        setIsLoading(false);
      } else if (token) {
        await refreshUser();
        setIsLoading(false);
      } else {
        setIsLoading(false);
      }
    };

    initAuth();
  }, []);

  const login = async (email: string, password: string): Promise<AuthResponse> => {
    const response = await apiClient.login(email, password);
    await refreshUser();
    return response;
  };

  const signup = async (email: string, password: string): Promise<void> => {
    await apiClient.signup(email, password);
  };

  const logout = async () => {
    await apiClient.logout();
    setUser(null);
    localStorage.removeItem('guest_mode');
  };

  const logoutAll = async () => {
    await apiClient.logoutAll();
    setUser(null);
    localStorage.removeItem('guest_mode');
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        isLoading,
        isAuthenticated,
        isGuest,
        guestFeatures,
        login,
        signup,
        loginAsGuest,
        logout,
        logoutAll,
        refreshUser,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

// Check if user is in guest mode
export const isGuestMode = (): boolean => {
  return localStorage.getItem('guest_mode') === 'true';
};
