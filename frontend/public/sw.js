// Nebula Search Engine - Service Worker
// Version: 1.0.0
// Provides offline caching and PWA reliability

const CACHE_VERSION = 'v1';
const STATIC_CACHE = `nebula-static-${CACHE_VERSION}`;
const DYNAMIC_CACHE = `nebula-dynamic-${CACHE_VERSION}`;
const ASSET_CACHE = `nebula-assets-${CACHE_VERSION}`;

// Assets to pre-cache on install
const PRECACHE_ASSETS = [
  '/',
  '/index.html',
];

// API routes to cache (GET requests only)
const API_CACHE_ROUTES = [
  '/api/v1/search',
  '/api/v1/autocomplete',
  '/api/v1/spell',
  '/api/v1/suggestions',
  '/api/v1/documents',
  '/api/v1/notifications',
  '/api/v1/saved-searches',
  '/api/v1/analytics',
];

// Install event - pre-cache critical assets
self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(STATIC_CACHE).then((cache) => {
      return cache.addAll(PRECACHE_ASSETS);
    })
  );
  self.skipWaiting();
});

// Activate event - clean old caches
self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((cacheNames) => {
      return Promise.all(
        cacheNames
          .filter((name) => {
            return name.startsWith('nebula-') && name !== STATIC_CACHE && name !== DYNAMIC_CACHE && name !== ASSET_CACHE;
          })
          .map((name) => caches.delete(name))
      );
    })
  );
  self.clients.claim();
});

// Helper: check if URL should be cached
function shouldCache(url) {
  const urlObj = new URL(url);
  
  // Cache static assets
  if (urlObj.pathname.match(/\.(js|css|png|jpg|jpeg|gif|svg|ico|woff2?|ttf|eot)$/)) {
    return 'asset';
  }
  
  // Cache API GET requests
  if (urlObj.pathname.startsWith('/api/') && !urlObj.pathname.match(/\.(ico|png)$/)) {
    return 'api';
  }
  
  // Cache navigation requests
  if (urlObj.origin === self.location.origin && !urlObj.pathname.startsWith('/api/')) {
    return 'navigation';
  }
  
  return false;
}

// Network-first strategy for API calls
async function networkFirst(request) {
  try {
    const networkResponse = await fetch(request);
    if (networkResponse.ok) {
      const cache = await caches.open(DYNAMIC_CACHE);
      cache.put(request, networkResponse.clone());
    }
    return networkResponse;
  } catch (error) {
    const cachedResponse = await caches.match(request);
    if (cachedResponse) {
      return cachedResponse;
    }
    // Return offline fallback for API
    return new Response(
      JSON.stringify({ status: 'error', message: 'You are offline' }),
      { headers: { 'Content-Type': 'application/json' } }
    );
  }
}

// Cache-first strategy for assets
async function cacheFirst(request) {
  const cachedResponse = await caches.match(request);
  if (cachedResponse) {
    return cachedResponse;
  }
  try {
    const networkResponse = await fetch(request);
    if (networkResponse.ok) {
      const cache = await caches.open(ASSET_CACHE);
      cache.put(request, networkResponse.clone());
    }
    return networkResponse;
  } catch (error) {
    return new Response('Offline', { status: 503 });
  }
}

// Network-first for navigation (with offline fallback)
async function navigationFirst(request) {
  try {
    const networkResponse = await fetch(request);
    if (networkResponse.ok) {
      const cache = await caches.open(STATIC_CACHE);
      cache.put(request, networkResponse.clone());
    }
    return networkResponse;
  } catch (error) {
    const cachedResponse = await caches.match(request);
    if (cachedResponse) {
      return cachedResponse;
    }
    // Return cached index.html for SPA routing
    const indexResponse = await caches.match('/index.html');
    if (indexResponse) {
      return indexResponse;
    }
    return new Response('Offline', { status: 503 });
  }
}

// Fetch event - apply caching strategies
self.addEventListener('fetch', (event) => {
  const cacheType = shouldCache(event.request.url);
  
  if (!cacheType) {
    return;
  }
  
  // Skip non-GET requests
  if (event.request.method !== 'GET') {
    return;
  }
  
  switch (cacheType) {
    case 'asset':
      event.respondWith(cacheFirst(event.request));
      break;
    case 'api':
      event.respondWith(networkFirst(event.request));
      break;
    case 'navigation':
      event.respondWith(navigationFirst(event.request));
      break;
  }
});

// Listen for messages from the client
self.addEventListener('message', (event) => {
  if (event.data === 'skipWaiting') {
    self.skipWaiting();
  }
});