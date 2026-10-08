/**
 * JADOTA AI — Service Worker
 *
 * Strategy:
 *   - Network-first for /api/* (never cache API responses)
 *   - Cache-first for static assets (JS, CSS, images, fonts)
 *   - Fallback to index.html for navigation requests when offline
 */

const CACHE_NAME = 'jadota-v1';
const STATIC_CACHE = 'jadota-static-v1';

// Assets to precache on install
const PRECACHE_ASSETS = [
  '/',
  '/index.html',
  '/manifest.json',
  '/jadota-icon.png',
];

// ============================================
// Install
// ============================================
self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(STATIC_CACHE).then((cache) => {
      return cache.addAll(PRECACHE_ASSETS).catch((err) => {
        console.warn('[SW] Precaching failed (safe to ignore):', err);
      });
    })
  );
  self.skipWaiting();
});

// ============================================
// Activate — clean old caches
// ============================================
self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(
        keys
          .filter((k) => k !== CACHE_NAME && k !== STATIC_CACHE)
          .map((k) => caches.delete(k))
      )
    )
  );
  self.clients.claim();
});

// ============================================
// Fetch handler
// ============================================
self.addEventListener('fetch', (event) => {
  const { request } = event;
  const url = new URL(request.url);

  // Skip non-GET requests
  if (request.method !== 'GET') return;

  // Skip API calls and auth — always go to network
  if (url.pathname.startsWith('/api/') || url.origin !== self.location.origin) {
    return;
  }

  // Navigation requests (SPA routes) — network first, fallback to cached index
  if (request.mode === 'navigate') {
    event.respondWith(
      fetch(request)
        .then((response) => {
          const copy = response.clone();
          caches.open(CACHE_NAME).then((cache) => cache.put('/index.html', copy));
          return response;
        })
        .catch(() => caches.match('/index.html'))
    );
    return;
  }

  // Static assets — cache first, then network
  event.respondWith(
    caches.match(request).then((cached) => {
      if (cached) return cached;
      return fetch(request).then((response) => {
        // Cache successful GET responses for static assets
        if (
          response.ok &&
          (url.pathname.match(/\.(js|css|png|jpg|jpeg|svg|woff2?|ttf)$/) ||
            url.pathname.startsWith('/assets/'))
        ) {
          const copy = response.clone();
          caches.open(STATIC_CACHE).then((cache) => cache.put(request, copy));
        }
        return response;
      });
    })
  );
});