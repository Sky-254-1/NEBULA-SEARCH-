// ============================================
// NEBULA SEARCH - TypeScript Type Definitions
// ============================================

// ============================================
// Authentication Types
// ============================================
export interface AuthRequest {
  email: string;
  password: string;
}

export interface AuthResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
}

export interface RefreshRequest {
  refresh_token?: string;
}

export interface UserInfo {
  email: string;
  role: string;
  email_verified: boolean;
  created_at?: string;
  last_login?: string;
}

export interface UserProfile {
  id: number;
  email: string;
  role: string;
  first_name?: string;
  last_name?: string;
  phone_number?: string;
  avatar_url?: string;
  email_verified: boolean;
  two_factor_enabled: boolean;
  created_at: string;
  last_login?: string;
}

export interface UpdateProfileRequest {
  first_name?: string;
  last_name?: string;
  phone_number?: string;
}

export interface UserPreferences {
  user_id: number;
  preferences: Record<string, any>;
  updated_at: string;
}

export interface ActivityItem {
  id: number;
  action: string;
  resource_type?: string;
  resource_id?: number;
  ip_address?: string;
  created_at: string;
}

export interface ActivityResponse {
  activities: ActivityItem[];
  total: number;
}

// ============================================
// Search Types
// ============================================
export interface SearchResult {
  // Vector / document result fields
  document_id?: number;
  chunk_id?: number;
  filename?: string;
  content?: string;
  vector_score?: number;
  keyword_score?: number;
  // Web result fields
  title?: string;
  url?: string;
  snippet?: string;
  // Shared ranking field — present on both shapes
  score: number;
  combined_score?: number;
  semantic_score?: number;
}

export interface OrchestratedSearchResponse {
  query: string;
  results: SearchResult[];
  backends_used: string[];
  total: number;
}

// Search v2 Types
export interface IntelligentSearchResponse {
  query: string;
  original_query: string;
  results: SearchResult[];
  total: number;
  page: number;
  page_size: number;
  spell_corrected: boolean;
  intent: string;
  backends: string[];
  features: {
    semantic_enabled: boolean;
    personalization_enabled: boolean;
    diversity_enabled: boolean;
  };
}

export interface SearchSuggestion {
  text: string;
  score: number;
  source: string;
  metadata?: Record<string, any>;
}

export interface SuggestionsResponse {
  query: string;
  suggestions: SearchSuggestion[];
}

export interface AutocompleteResponse {
  query: string;
  completions: string[];
}

export interface SpellCheckResponse {
  original: string;
  corrected: string;
  was_corrected: boolean;
}

export interface TrendingQuery {
  query: string;
  count: number;
}

export interface TrendingResponse {
  trending: TrendingQuery[];
  period_hours: number;
}

export interface PopularResponse {
  popular: TrendingQuery[];
}

export interface SearchProfile {
  profile: Record<string, any>;
  recent_searches: SearchHistoryItem[];
}

export interface SearchHistoryItem {
  id: number;
  query: string;
  backend: string;
  result_count: number;
  created_at: string;
}

// ============================================
// AI Types
// ============================================
export interface AIRequest {
  prompt: string;
}

export interface AIResponse {
  answer: string;
  provider: string;
}

export interface SynthesizeRequest {
  query: string;
  snippets: string[];
}

export interface SynthesizeResponse {
  synthesis: string;
  sources: string[];
}

export interface ChatMessage {
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp?: string;
}

export interface ChatHistoryResponse {
  messages: ChatMessage[];
}

// ============================================
// Vector Types
// ============================================
export interface VectorSearchRequest {
  query: string;
  top_k?: number;
  filters?: Record<string, any>;
}

export interface VectorSearchResult {
  document_id?: number;
  chunk_id?: number;
  filename: string;
  content: string;
  score: number;
  vector_score?: number;
  keyword_score?: number;
}

export interface VectorSearchResponse {
  query: string;
  results: VectorSearchResult[];
  total: number;
}

export interface Citation {
  id: number;
  document_id?: number;
  chunk_id?: number;
  query: string;
  snippet: string;
  score: number;
  created_at: string;
}

export interface VectorAskRequest {
  query: string;
  top_k?: number;
}

export interface VectorAskResponse {
  query: string;
  answer: string;
  citations: Citation[];
  sources: string[];
}

export interface DocumentIndexStatusResponse {
  id: number;
  filename: string;
  status: 'pending' | 'processing' | 'indexed' | 'failed';
  indexed_at?: string;
  error_message?: string;
}

// ============================================
// Storage/Document Types
// ============================================
export interface DocumentResponse {
  id: number;
  filename: string;
  content_type?: string;
  created_at: string;
  indexed_at?: string;
}

export interface DocumentListResponse {
  documents: DocumentResponse[];
  pagination?: PaginationMeta;
}

export interface ExportCreateRequest {
  export_type: string;
  data?: Record<string, any>;
}

export interface ExportResponse {
  id: number;
  export_type: string;
  storage_path: string;
  created_at: string;
}

export interface ExportListResponse {
  exports: ExportResponse[];
  pagination?: PaginationMeta;
}

export interface SettingsResponse {
  settings: Record<string, any>;
}

export interface SettingsUpdateRequest {
  settings: Record<string, any>;
}

// ============================================
// Analytics Types
// ============================================
export interface UsageStats {
  total_searches: number;
  total_documents: number;
  total_ai_queries: number;
  period_days: number;
  daily_average: number;
}

export interface SearchAnalytics {
  total_queries: number;
  unique_queries: number;
  avg_response_time_ms: number;
  backends_used: Record<string, number>;
  top_queries: Array<{ query: string; count: number }>;
  period_days: number;
}

export interface PerformanceMetrics {
  avg_latency_ms: number;
  p95_latency_ms: number;
  p99_latency_ms: number;
  cache_hit_ratio: number;
  error_rate: number;
  period_days: number;
}

export interface AnalyticsExport {
  export_id: number;
  export_type: string;
  download_url: string;
  created_at: string;
}

// ============================================
// Features Types (Saved Searches, Collections, Bookmarks, Notifications)
// ============================================
export interface SavedSearchCreate {
  query: string;
  filters?: Record<string, any>;
  label?: string;
}

export interface SavedSearchResponse {
  id: number;
  user_id: number;
  query: string;
  filters?: Record<string, any>;
  label?: string;
  created_at: string;
  updated_at: string;
}

export interface SavedSearchListResponse {
  saved_searches: SavedSearchResponse[];
}

export interface CollectionCreate {
  name: string;
  description?: string;
  is_public: boolean;
}

export interface CollectionUpdate {
  name?: string;
  description?: string;
  is_public?: boolean;
}

export interface CollectionResponse {
  id: number;
  user_id: number;
  name: string;
  description?: string;
  is_public: boolean;
  created_at: string;
  updated_at: string;
}

export interface CollectionListResponse {
  collections: CollectionResponse[];
}

export interface CollectionItemCreate {
  document_id?: number;
  search_result_id?: number;
  note?: string;
}

export interface CollectionItemResponse {
  id: number;
  collection_id: number;
  document_id?: number;
  search_result_id?: number;
  note?: string;
  created_at: string;
}

export interface BookmarkCreate {
  title: string;
  url: string;
  snippet?: string;
  tags?: string[];
}

export interface BookmarkUpdate {
  title?: string;
  snippet?: string;
  tags?: string[];
}

export interface BookmarkResponse {
  id: number;
  user_id: number;
  title: string;
  url: string;
  snippet?: string;
  tags?: string[];
  created_at: string;
  updated_at: string;
}

export interface BookmarkListResponse {
  bookmarks: BookmarkResponse[];
}

export interface NotificationResponse {
  id: number;
  user_id: number;
  type: string;
  title: string;
  message: string;
  data?: Record<string, any>;
  is_read: boolean;
  created_at: string;
}

export interface NotificationListResponse {
  notifications: NotificationResponse[];
  unread_count: number;
}

// ============================================
// Pagination Types
// ============================================
export interface PaginationMeta {
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
  has_next: boolean;
  has_previous: boolean;
}

// ============================================
// API Response Types
// ============================================
export interface APIResponse<T = any> {
  status: 'success' | 'error';
  message: string;
  data?: T;
  metadata?: Record<string, any>;
  timestamp: number;
}

export interface APIError {
  status: 'error';
  error_code: string;
  message: string;
  validation_errors?: Array<{
    field: string;
    message: string;
  }>;
  request_id?: string;
  timestamp: number;
}

// ============================================
// Common Types
// ============================================
export interface PaginationParams {
  page: number;
  page_size: number;
  offset: number;
  limit: number;
}

export type Theme = 'light' | 'dark' | 'system';

export type UserRole = 'user' | 'admin' | 'moderator';

export interface AppError {
  code: string;
  message: string;
  details?: Record<string, any>;
}

// ============================================
// Offline/Queue Types
// ============================================
export interface QueuedAction {
  id: string;
  type: 'search' | 'upload' | 'chat' | 'bookmark' | 'collection';
  payload: Record<string, any>;
  timestamp: number;
  retries: number;
  status: 'pending' | 'processing' | 'completed' | 'failed';
}

// ============================================
// Dashboard Types
// ============================================
export interface DashboardStats {
  total_searches: number;
  total_documents: number;
  total_ai_queries: number;
  storage_used: number;
  vector_count: number;
  recent_searches: SearchHistoryItem[];
  recent_uploads: DocumentResponse[];
  top_queries: Array<{ query: string; count: number }>;
}