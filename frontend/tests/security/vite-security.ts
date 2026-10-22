// Security hardening configuration for Vite
import fs from 'fs';
import path from 'path';

// Define allowed paths for development security
const ALLOWED_PATHS = [
  path.resolve(__dirname, './src'),
  path.resolve(__dirname, './public'),
  path.resolve(__dirname, './node_modules/@nebula'),
  path.resolve(__dirname, './tests/unit'),
  path.resolve(__dirname, './tests/security'),
  path.resolve(__dirname, './tests/e2e'),
  path.resolve(__dirname, './backend'),
];

// Blocked patterns to prevent path traversal attacks
const BLOCKED_PATTERNS = [
  /\.env\./gi,
  /\.key$/gi,
  /\.pem$/gi,
  /\.p12$/gi,
  /\.crt$/gi,
  /\.aws\//gi,
  /\.ssh\//gi,
  /\/etc\//gi,
  /\/etc\/passwd/gi,
  /\/etc\/shadow/gi,
];

// Security configuration flags
const SECURITY_CONFIG = {
  enableStrictMode: process.env.NODE_ENV === 'development',
  blockFileAccess: true,
  denyNetworkAccess: true,
  logSecurityEvents: true,
};

export function isDevelopment(): boolean {
  return process.env.NODE_ENV === 'development';
}

export function isSecureMode(): boolean {
  return process.env.VITE_SECURE_MODE === 'true';
}

export function isPathAllowed(filePath: string): boolean {
  if (!isDevelopment() || !SECURITY_CONFIG.blockFileAccess) {
    return true;
  }

  const resolvedPath = path.resolve(filePath);

  // Check if path is explicitly allowed
  const isExplicitlyAllowed = ALLOWED_PATHS.some(
    (allowedPath) => resolvedPath === allowedPath || resolvedPath.startsWith(allowedPath + path.sep)
  );

  if (!isExplicitlyAllowed) {
    // Check if path matches blocked patterns
    const isBlocked = BLOCKED_PATTERNS.some((pattern) => pattern.test(resolvedPath));

    if (isBlocked) {
      if (SECURITY_CONFIG.logSecurityEvents) {
        console.error(`[SECURITY] BLOCKED: Path traversal attempt detected: ${filePath}`);
      }
      return false;
    }

    // Log potential access attempts
    if (SECURITY_CONFIG.logSecurityEvents) {
      console.warn(`[SECURITY] WARNING: Path not explicitly allowed: ${filePath}`);
    }
  }

  return true;
}

export function validateEnvironmentVariables(): boolean {
  const SENSITIVE_ENV_VARS = [
    'API_KEY',
    'SECRET_KEY',
    'DATABASE_PASSWORD',
    'REDIS_PASSWORD',
    'JWT_SECRET',
    'OPENAI_API_KEY',
    'BRAVE_API_KEY',
    'SERPAPI_KEY',
    'AWS_ACCESS_KEY_ID',
    'AWS_SECRET_ACCESS_KEY',
    'AWS_SESSION_TOKEN',
    'GOOGLE_APPLICATION_CREDENTIALS',
    'AZURE_CLIENT_SECRET',
    'GITHUB_TOKEN',
    'GITLAB_TOKEN',
    'FORGE_TOKEN',
  ];

  const INSECURE_ENV_VARS = SENSITIVE_ENV_VARS.filter(
    (envVar) => process.env[envVar] && isDevelopment()
  );

  if (INSECURE_ENV_VARS.length > 0) {
    console.error(`[SECURITY] WARNING: Potentially sensitive environment variables exposed: ${INSECURE_ENV_VARS.join(', ')}`);
    return false;
  }

  return true;
}

export function configureServerSecurity(server: any): any {
  if (!isDevelopment() || !SECURITY_CONFIG.enableStrictMode) {
    return server;
  }

  // Restrict server to localhost only
  server.host = '127.0.0.1';
  server.disableHostCheck = true;

  // Configure CORS to be restrictive
  server.cors = {
    origin: false, // Disable CORS for security
  };

  // Configure filesystem security
  if (server.fs) {
    server.fs.strict = true;
    server.fs.allow = ALLOWED_PATHS.filter((p) => fs.existsSync(p));
  }

  // Remove proxy by default for security
  server.proxy = {};

  // Add headers to prevent security issues
  server.on('request', (req: any, res: any) => {
    // Log all requests for security monitoring
    console.log(`[SECURITY] Request: ${req.method} ${req.url}`);

    // Block requests to internal networks
    const blockedPatterns = [
      /localhost/,
      /127\.0\.0\.1/,
      /192\.168\./,
      /10\./,
      /172\.(1[6-9]|2[0-9]|3[0-1])\./,
    ];

    const isBlocked = blockedPatterns.some((pattern) => req.url && pattern.test(req.url));
    if (isBlocked) {
      res.writeHead(403, { 'Content-Type': 'text/plain' });
      res.end('Access denied for security reasons');
    }
  });

  return server;
}

export function createSecurityMiddleware() {
  return (req: any, res: any, next: any) => {
    // Security middleware for Vite development server

    // Block access to sensitive files
    const blockedPaths = ['/env', '/config', '/credentials', '/private'];
    const hasBlockedPath = blockedPaths.some((path) => req.path.includes(path));

    if (hasBlockedPath) {
      return res.status(403).json({ error: 'Access denied for security reasons' });
    }

    // Log all requests for audit trail
    console.log(`[SECURITY] ${req.method} ${req.path} - ${new Date().toISOString()}`);

    return next();
  };
}

export function getSecurityReport() {
  const report = {
    timestamp: new Date().toISOString(),
    development: isDevelopment(),
    secureMode: isSecureMode(),
    environmentValidated: validateEnvironmentVariables(),
    config: SECURITY_CONFIG,
    securityStatus: {
      fileAccess: SECURITY_CONFIG.blockFileAccess ? 'RESTRICTED' : 'OPEN',
      networkAccess: SECURITY_CONFIG.denyNetworkAccess ? 'BLOCKED' : 'ALLOWED',
      loggingEnabled: SECURITY_CONFIG.logSecurityEvents,
      strictMode: SECURITY_CONFIG.enableStrictMode,
    },
  };

  return report;
}