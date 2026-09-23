import axios, { AxiosError, AxiosInstance, AxiosResponse, InternalAxiosRequestConfig } from 'axios';
import { AuthResponse, APIError } from '@/types';

// ============================================
// API Client Configuration
// ============================================
// Detect desktop environment (Electron) and use the bridge-provided API URL
declare global {
  interface Window {
    nebula?: {
      getApiBaseUrl?: () => Promise<string>;
      isDesktop?: boolean;
    };
  }
}

const getDesktopApiBaseUrl = async (): Promise<string | null> => {
  try {
    if (window.nebula?.getApiBaseUrl) {
      const base = await window.nebula.getApiBaseUrl();
      if (base) return `${base}/api/v1`;
    }
  } catch {
    // Fall through to default
  }
  return null;
};

export const API_BASE_URL = (import.meta.env && import.meta.env.VITE_API_URL) || '/api/v1';
const API_TIMEOUT = 30000;
const MAX_RETRIES = 3;
const RETRY_DELAY = 1000;

class APIClient {
  private client: AxiosInstance;
  private refreshTokenPromise: Promise<string> | null = null;
  private isOnline: boolean = true;

  constructor() {
    this.client = axios.create({
      baseURL: API_BASE_URL,
      timeout: API_TIMEOUT,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    this.setupInterceptors();
    this.setupNetworkListeners();
    this.initDesktopApiUrl();
  }

  private async initDesktopApiUrl(): Promise<void> {
    const desktopBase = await getDesktopApiBaseUrl();
    if (desktopBase) {
      this.client.defaults.baseURL = desktopBase;
    }
  }

  private setupNetworkListeners(): void {
    // Initialize online status
    this.isOnline = navigator.onLine;

    // Track online/offline status
    const updateOnlineStatus = () => {
      this.isOnline = navigator.onLine;
      if (this.isOnline) {
        this.processOfflineQueue();
      }
    };

    window.addEventListener('online', updateOnlineStatus);
    window.addEventListener('offline', updateOnlineStatus);
  }

  private async processOfflineQueue(): Promise<void> {
    const queue = this.getOfflineQueue();
    for (const action of queue) {
      try {
        await this.executeQueuedAction(action);
        this.removeFromOfflineQueue(action.id);
      } catch (error) {
        console.error('Failed to process queued action:', error);
      }
    }
  }

  private async executeQueuedAction(action: any): Promise<void> {
    switch (action.type) {
      case 'search':
        await this.post('/v2/search', action.payload);
        break;
      case 'chat':
        await this.post('/ai/ask', action.payload);
        break;
      default:
        console.warn('Unknown queued action type:', action.type);
    }
  }

  private getOfflineQueue(): any[] {
    try {
      const queue = localStorage.getItem('offline_queue');
      return queue ? JSON.parse(queue) : [];
    } catch {
      return [];
    }
  }

  private removeFromOfflineQueue(id: string): void {
    const queue = this.getOfflineQueue().filter((item) => item.id !== id);
    localStorage.setItem('offline_queue', JSON.stringify(queue));
  }

  private setupInterceptors(): void {
    // Request interceptor to add auth token
    this.client.interceptors.request.use(
      (config: InternalAxiosRequestConfig) => {
        const token = this.getAccessToken();
        if (token && config.headers) {
          config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
      },
      (error: AxiosError) => Promise.reject(error)
    );

    // Response interceptor to handle token refresh and retries
    this.client.interceptors.response.use(
      (response: AxiosResponse) => response,
      async (error: AxiosError<APIError>) => {
        const originalRequest = error.config as InternalAxiosRequestConfig & { _retry?: boolean; _retryCount?: number };

        // Handle network errors
        if (!error.response) {
          if (this.isOnline) {
            return Promise.reject(error);
          }
          
          // Queue request for later if offline
          if (originalRequest.method && originalRequest.url && !originalRequest.url.includes('/auth/')) {
            this.queueOfflineAction(originalRequest);
          }
          
          return Promise.reject(new Error('Network error - request queued for retry'));
        }

        // If error is 401 and we haven't retried yet
        if (error.response.status === 401 && !originalRequest._retry) {
          originalRequest._retry = true;

          try {
            const newToken = await this.refreshAccessToken();
            if (newToken && originalRequest.headers) {
              originalRequest.headers.Authorization = `Bearer ${newToken}`;
              return this.client(originalRequest);
            }
          } catch (refreshError) {
            // Refresh failed, clear auth and redirect to login
            this.clearTokens();
            window.location.href = '/login';
            return Promise.reject(refreshError);
          }
        }

        // Retry on 5xx errors
        if (error.response.status >= 500 && !originalRequest._retry) {
          originalRequest._retryCount = (originalRequest._retryCount || 0) + 1;
          
          if (originalRequest._retryCount < MAX_RETRIES) {
            await this.delay(RETRY_DELAY * originalRequest._retryCount);
            return this.client(originalRequest);
          }
        }

        return Promise.reject(error);
      }
    );
  }

  private queueOfflineAction(config: InternalAxiosRequestConfig): void {
    try {
      const queue = this.getOfflineQueue();
      queue.push({
        id: crypto.randomUUID(),
        type: 'generic',
        method: config.method,
        url: config.url,
        data: config.data,
        timestamp: Date.now(),
        retries: 0,
      });
      localStorage.setItem('offline_queue', JSON.stringify(queue));
    } catch (error) {
      console.error('Failed to queue offline action:', error);
    }
  }

  private delay(ms: number): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, ms));
  }

  private getAccessToken(): string | null {
    return localStorage.getItem('access_token');
  }

  private getRefreshToken(): string | null {
    return localStorage.getItem('refresh_token');
  }

  private setTokens(accessToken: string, refreshToken: string): void {
    localStorage.setItem('access_token', accessToken);
    localStorage.setItem('refresh_token', refreshToken);
  }

  private clearTokens(): void {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
  }

  private async refreshAccessToken(): Promise<string | null> {
    // Prevent multiple refresh requests
    if (this.refreshTokenPromise) {
      return this.refreshTokenPromise;
    }

    const refreshToken = this.getRefreshToken();
    if (!refreshToken) {
      return null;
    }

    this.refreshTokenPromise = this.client
      .post<AuthResponse>('/auth/refresh', { refresh_token: refreshToken })
      .then((response) => {
        const { access_token, refresh_token } = response.data;
        this.setTokens(access_token, refresh_token);
        return access_token;
      })
      .catch((error) => {
        this.clearTokens();
        throw error;
      })
      .finally(() => {
        this.refreshTokenPromise = null;
      });

    return this.refreshTokenPromise;
  }

  public async login(email: string, password: string): Promise<AuthResponse> {
    const response = await this.client.post<AuthResponse>('/auth/login', {
      email,
      password,
    });
    
    const { access_token, refresh_token } = response.data;
    this.setTokens(access_token, refresh_token);
    
    return response.data;
  }

  public async signup(email: string, password: string): Promise<void> {
    await this.client.post('/auth/signup', {
      email,
      password,
    });
  }

  public async logout(): Promise<void> {
    try {
      await this.client.post('/auth/logout', {
        refresh_token: this.getRefreshToken(),
      });
    } finally {
      this.clearTokens();
    }
  }

  public async logoutAll(): Promise<void> {
    try {
      await this.client.post('/auth/logout-all');
    } finally {
      this.clearTokens();
    }
  }

  public async getCurrentUser(): Promise<{ email: string; role: string; email_verified: boolean }> {
    const response = await this.client.get('/auth/me');
    return response.data;
  }

  public isAuthenticated(): boolean {
    return !!this.getAccessToken();
  }

  // Generic request methods
  public async get<T>(url: string, params?: Record<string, any>): Promise<T> {
    const response = await this.client.get<T>(url, { params });
    return response.data;
  }

  public async post<T>(url: string, data?: any, config?: { params?: Record<string, any> }): Promise<T> {
    const response = await this.client.post<T>(url, data, config ? { params: config.params } : undefined);
    return response.data;
  }

  public async put<T>(url: string, data?: any): Promise<T> {
    const response = await this.client.put<T>(url, data);
    return response.data;
  }

  public async delete<T>(url: string): Promise<T> {
    const response = await this.client.delete<T>(url);
    return response.data;
  }

  public async upload<T>(url: string, file: File, onProgress?: (progress: number) => void): Promise<T> {
    const formData = new FormData();
    formData.append('file', file);

    const response = await this.client.post<T>(url, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      onUploadProgress: (progressEvent) => {
        if (onProgress && progressEvent.total) {
          const progress = Math.round((progressEvent.loaded * 100) / progressEvent.total);
          onProgress(progress);
        }
      },
    });

    return response.data;
  }

  // Push Notifications
  public async registerPushToken(token: string, platform: 'ios' | 'android' | 'web', deviceId?: string): Promise<void> {
    await this.client.post('/notifications/push/register', {
      token,
      platform,
      device_id: deviceId,
    });
  }

  public async unregisterPushToken(): Promise<void> {
    await this.client.delete('/notifications/push/unregister');
  }

  public async getPushStatus(): Promise<{ enabled: boolean; registered: boolean; platform?: string; updated_at?: string }> {
    const response = await this.client.get('/notifications/push/status');
    return response.data;
  }
}

// Export singleton instance
export const apiClient = new APIClient();
export default apiClient;