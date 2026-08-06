import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import { VitePWA } from 'vite-plugin-pwa';
import fs from 'fs';
import path from 'path';

// Security: Define allowed paths for development
const ALLOWED_PATHS = [
  path.resolve(__dirname, 'src'),
  path.resolve(__dirname, 'public'),
  path.resolve(__dirname, 'node_modules'),
  path.resolve(__dirname, 'tests'),
];

// Security: Blocked patterns to prevent path traversal
const BLOCKED_PATTERNS = [
  /\.env\./gi,
  /\.key$/gi,
  /\.pem$/gi,
  /\.p12$/gi,
  /\.crt$/gi,
  /\.aws\//gi,
  /\.ssh\//gi,
  /\/etc\//gi,
  /\/proc\//gi,
  /\/var\//gi,
  /\/sys\//gi,
  /\/dev\//gi,
  /\/etc\/passwd/gi,
  /\/etc\/shadow/gi,
];

// Security: Secure development environment detection
const isDevelopment = process.env.NODE_ENV === 'development';
const isSecureMode = process.env.VITE_SECURE_MODE === 'true';

function isPathAllowed(filePath: string): boolean {
  if (!isDevelopment) return true;
  
  // Skip Vite virtual modules (e.g., /@react-refresh, /@vite-client)
  if (filePath.startsWith('/@') || filePath.startsWith('virtual:') || filePath.startsWith('\0')) {
    return true;
  }
  
  const resolvedPath = path.resolve(filePath);
  
  // Check if path is explicitly allowed
  const isAllowed = ALLOWED_PATHS.some((allowedPath) => 
    resolvedPath === allowedPath || resolvedPath.startsWith(allowedPath + path.sep)
  );
  
  if (!isAllowed) {
    // Check if path matches blocked patterns
    const isBlocked = BLOCKED_PATTERNS.some((pattern) => 
      pattern.test(resolvedPath) || pattern.test(filePath)
    );
    
    if (isBlocked) {
      console.error(`[SECURITY] BLOCKED: Path traversal attempt: ${filePath}`);
      return false;
    }
  }
  
  return true;
}

function secureConfigureServer(server: any): any {
  if (!isDevelopment) return server;
  
  // Only apply strict fs restrictions when explicitly enabled via VITE_SECURE_MODE
  if (isSecureMode && server.fs) {
    server.fs.strict = true;
    server.fs.allow = ALLOWED_PATHS.filter(p => fs.existsSync(p));
  }
  
  server.host = '127.0.0.1';
  
  return server;
}

export default defineConfig({
  plugins: [
    react(),
    VitePWA({
      registerType: 'autoUpdate',
      includeAssets: ['favicon.ico', 'apple-touch-icon.png', 'mask-icon.svg'],
      manifest: {
        name: 'Nebula Search',
        short_name: 'Nebula',
        description: 'AI-Powered Search Engine',
        theme_color: '#0f172a',
        background_color: '#0f172a',
        display: 'standalone',
        icons: [
          {
            src: 'pwa-192x192.png',
            sizes: '192x192',
            type: 'image/png',
          },
          {
            src: 'pwa-512x512.png',
            sizes: '512x512',
            type: 'image/png',
          },
        ],
      },
      workbox: {
        globPatterns: ['**/*.{js,css,html,ico,png,svg,woff2}'],
        runtimeCaching: [
          {
            urlPattern: /^https:\/\/fonts\.googleapis\.com\/.*/i,
            handler: 'CacheFirst',
            options: {
              cacheName: 'google-fonts-cache',
              expiration: {
                maxEntries: 10,
                maxAgeSeconds: 60 * 60 * 24 * 365,
              },
            },
          },
          {
            urlPattern: /^https:\/\/fonts\.gstatic\.com\/.*/i,
            handler: 'CacheFirst',
            options: {
              cacheName: 'gstatic-fonts-cache',
              expiration: {
                maxEntries: 10,
                maxAgeSeconds: 60 * 60 * 24 * 365,
              },
            },
          },
        ],
      },
    }),
    { // Security plugin
      name: 'security-restrictions',
      configureServer(server) {
        secureConfigureServer(server);
      },
      transformIndexHtml(html) {
        if (isSecureMode) {
          html = html.replace(/<meta[^>]*>/g, (match) => 
            match.includes('viewport') || match.includes('theme-color') ? match : ''
          );
        }
        return html;
      },
    },
    { // File access validator — only active in secure mode (VITE_SECURE_MODE=true)
      name: 'file-access-validator',
      transform(src, id) {
        if (isDevelopment && isSecureMode && !isPathAllowed(id)) {
          console.log(`[SECURITY] Blocked file access: ${id}`);
          return { code: '', map: null };
        }
        return undefined;
      },
    },
  ],
  server: {
    port: 5173,
    proxy: isDevelopment ? {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        secure: false,
        rewrite: (path) => path,
      },
      '/health': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        secure: false,
      },
      '/metrics': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        secure: false,
      },
    } : {},
  },
  build: {
    outDir: 'dist',
    sourcemap: isDevelopment,
    rollupOptions: {
      output: {
        manualChunks: {
          vendor: ['react', 'react-dom', 'react-router-dom'],
          query: ['@tanstack/react-query'],
          ui: ['framer-motion', 'lucide-react', 'recharts'],
        },
      },
    },
  },
  resolve: {
    alias: {
      '@': '/src',
    },
    // Prefer TypeScript files over legacy JavaScript files
    // This prevents App.jsx (legacy) from overriding App.tsx (new)
    extensions: ['.tsx', '.ts', '.jsx', '.js', '.json'],
  },
  optimizeDeps: {
    esbuildOptions: {
      target: isDevelopment ? 'es2020' : 'es2015',
      supported: {
        'dynamic-import': false,
      },
    },
  },
});