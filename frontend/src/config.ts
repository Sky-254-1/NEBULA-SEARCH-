// ============================================
// NEBULA SEARCH - Frontend Environment Configuration
// ============================================
// This module validates required environment variables at startup
// to fail fast if critical configuration is missing.

// ============================================
// Environment Variable Schemas
// ============================================

interface EnvironmentVariables {
  // Required: API Configuration
  VITE_API_URL: string;
  VITE_API_BASE_URL: string;
  
  // Required: Application Metadata
  VITE_APP_ENV: 'development' | 'production' | 'staging';
  VITE_APP_NAME: string;
  VITE_APP_VERSION: string;
  
  // Optional: Authentication
  VITE_AUTH_COOKIE_MODE?: 'true' | 'false';
  VITE_ENABLE_2FA?: 'true' | 'false';
  VITE_ENABLE_WEBAUTHN?: 'true' | 'false';
  VITE_REQUIRE_EMAIL_VERIFICATION?: 'true' | 'false';
  
  // Optional: PWA
  VITE_PWA_ENABLED?: 'true' | 'false';
  VITE_OFFLINE_SUPPORT?: 'true' | 'false';
  
  // Optional: Analytics & Monitoring
  VITE_GA_ID?: string;
  VITE_SENTRY_DSN?: string;
  
  // Optional: OAuth Providers (required only if OAuth is configured)
  VITE_GOOGLE_OAUTH_CLIENT_ID?: string;
  VITE_GITHUB_OAUTH_CLIENT_ID?: string;
  
  // Optional: Upload limits
  VITE_MAX_UPLOAD_SIZE_MB?: string;
  
  // Optional: UI settings
  VITE_DEFAULT_PAGE_SIZE?: string;
  VITE_SEARCH_DEBOUNCE_MS?: string;
  
  // Optional: WebSocket
  VITE_WS_URL?: string;
}

// ============================================
// Required Variables List
// ============================================

const REQUIRED_VARS = [
  'VITE_API_URL',
  'VITE_API_BASE_URL',
  'VITE_APP_ENV',
  'VITE_APP_NAME',
  'VITE_APP_VERSION',
] as const;

type RequiredVar = typeof REQUIRED_VARS[number];

// ============================================
// Validation Logic
// ============================================

const env = import.meta.env as unknown as EnvironmentVariables;

/**
 * Validates that all required environment variables are set.
 * Throws an error with details about missing variables if any are missing.
 */
function validateEnvironment(): void {
  const missingVars: string[] = [];
  
  for (const varName of REQUIRED_VARS) {
    const value = env[varName];
    
    // Check if variable exists and is not empty
    if (value === undefined || value === '') {
      missingVars.push(varName);
    }
  }
  
  if (missingVars.length > 0) {
    const errorMessages = [
      '\n❌ Frontend environment validation failed.',
      '   Required environment variables are missing:\n',
      ...missingVars.map(v => `   - ${v}`),
      '\n   Please check frontend/.env.example and create your environment file.',
      '\n   If using Vite, ensure the file is named ".env" (not ".env.local" or other variants).\n',
    ].join('\n');
    
    console.error(errorMessages);
    throw new Error(`Missing required environment variables: ${missingVars.join(', ')}`);
  }
}

/**
 * Validates that a variable matches expected values.
 */
function assertOneOf<T extends string>(
  varName: string,
  value: string | undefined,
  allowedValues: T[]
): value is T {
  if (value === undefined || value === '') {
    return false;
  }
  
  if (!allowedValues.includes(value as T)) {
    console.warn(
      `[WARNING] ${varName}="${value}" is not one of the expected values: [${allowedValues.join(', ')}]`
    );
  }
  
  return true;
}

/**
 * Parses numeric environment variables with validation.
 */
function parseNumericVar(varName: string, value: string | undefined, defaultValue?: number): number {
  if (value === undefined || value === '') {
    if (defaultValue !== undefined) {
      return defaultValue;
    }
    throw new Error(`Missing required numeric environment variable: ${varName}`);
  }
  
  const parsed = Number(value);
  if (isNaN(parsed)) {
    throw new Error(`Invalid numeric value for ${varName}: "${value}"`);
  }
  
  return parsed;
}

// ============================================
// Export Configuration
// ============================================

// Validate on module import (fail fast)
validateEnvironment();

// Assert optional string variables
const AUTH_COOKIE_MODE = env.VITE_AUTH_COOKIE_MODE === 'true';
const ENABLE_2FA = env.VITE_ENABLE_2FA === 'true';
const ENABLE_WEBAUTHN = env.VITE_ENABLE_WEBAUTHN === 'true';
const REQUIRE_EMAIL_VERIFICATION = env.VITE_REQUIRE_EMAIL_VERIFICATION === 'true';
const PWA_ENABLED = env.VITE_PWA_ENABLED === 'true';
const OFFLINE_SUPPORT = env.VITE_OFFLINE_SUPPORT === 'true';

// Assert numeric variables
const MAX_UPLOAD_SIZE_MB = parseNumericVar('VITE_MAX_UPLOAD_SIZE_MB', env.VITE_MAX_UPLOAD_SIZE_MB, 100);
const DEFAULT_PAGE_SIZE = parseNumericVar('VITE_DEFAULT_PAGE_SIZE', env.VITE_DEFAULT_PAGE_SIZE, 20);
const SEARCH_DEBOUNCE_MS = parseNumericVar('VITE_SEARCH_DEBOUNCE_MS', env.VITE_SEARCH_DEBOUNCE_MS, 300);

// Assert one-of variables
assertOneOf('VITE_APP_ENV', env.VITE_APP_ENV, ['development', 'production', 'staging']);

// ============================================
// Configuration Object
// ============================================

export const config = {
  // Required: API Configuration
  apiUrl: env.VITE_API_URL,
  apiBaseUrl: env.VITE_API_BASE_URL,
  
  // Required: Application Metadata
  appEnv: env.VITE_APP_ENV,
  appName: env.VITE_APP_NAME,
  appVersion: env.VITE_APP_VERSION,
  
  // Optional: Authentication
  authCookieMode: AUTH_COOKIE_MODE,
  enable2FA: ENABLE_2FA,
  enableWebAuthn: ENABLE_WEBAUTHN,
  requireEmailVerification: REQUIRE_EMAIL_VERIFICATION,
  
  // Optional: PWA
  pwaEnabled: PWA_ENABLED,
  offlineSupport: OFFLINE_SUPPORT,
  
  // Optional: Analytics & Monitoring
  gaId: env.VITE_GA_ID,
  sentryDsn: env.VITE_SENTRY_DSN,
  
  // Optional: OAuth Providers
  googleOAuthClientId: env.VITE_GOOGLE_OAUTH_CLIENT_ID,
  githubOAuthClientId: env.VITE_GITHUB_OAUTH_CLIENT_ID,
  
  // Optional: Upload limits
  maxUploadSizeMB: MAX_UPLOAD_SIZE_MB,
  
  // Optional: UI settings
  defaultPageSize: DEFAULT_PAGE_SIZE,
  searchDebounceMs: SEARCH_DEBOUNCE_MS,
  
  // Optional: WebSocket
  wsUrl: env.VITE_WS_URL,
};

// ============================================
// Type Export for Configuration
// ============================================

export interface AppConfig {
  apiUrl: string;
  apiBaseUrl: string;
  appEnv: 'development' | 'production' | 'staging';
  appName: string;
  appVersion: string;
  authCookieMode: boolean;
  enable2FA: boolean;
  enableWebAuthn: boolean;
  requireEmailVerification: boolean;
  pwaEnabled: boolean;
  offlineSupport: boolean;
  gaId?: string;
  sentryDsn?: string;
  googleOAuthClientId?: string;
  githubOAuthClientId?: string;
  maxUploadSizeMB: number;
  defaultPageSize: number;
  searchDebounceMs: number;
  wsUrl?: string;
}

export default config;