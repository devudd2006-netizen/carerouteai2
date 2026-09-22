/* CareRoute AI service worker — offline support for the Find Care page.
 *
 * Strategies (single fetch handler):
 *  - Navigations: network-first, fall back to the cached SPA shell offline.
 *  - Map tiles (openstreetmap): cache-first. Tiles are immutable per URL, so
 *    once a tile is cached the map renders fully offline. Cache is capped.
 *  - Same-origin assets (JS/CSS bundles): stale-while-revalidate — serve the
 *    cached copy instantly, refresh it in the background.
 *  - /api GETs: network-first with cache fallback. Successful GET responses
 *    (facilities, profile, timeline…) are cached, so offline the Find Care
 *    page shows last-known hospitals (flagged `__offline`) instead of erroring.
 *  - Everything else (POST/PUT/PATCH/DELETE, OSRM, Overpass): online only —
 *    the pages already degrade gracefully when those are unreachable.
 */
const VERSION = 'v1';
const TILE_CACHE = `cr-tiles-${VERSION}`;
const SHELL_CACHE = `cr-shell-${VERSION}`;
const API_CACHE = `cr-api-${VERSION}`;
const TILE_LIMIT = 2000;

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(SHELL_CACHE).then((c) => c.addAll(['/', '/index.html']).catch(() => {}))
  );
  self.skipWaiting();
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(
        keys
          .filter((k) => ![TILE_CACHE, SHELL_CACHE, API_CACHE].includes(k))
          .map((k) => caches.delete(k))
      )
    ).then(() => self.clients.claim())
  );
});

async function trimCache(name, maxEntries) {
  const cache = await caches.open(name);
  const keys = await cache.keys();
  if (keys.length > maxEntries) {
    await Promise.all(keys.slice(0, keys.length - maxEntries).map((k) => cache.delete(k)));
  }
}

self.addEventListener('fetch', (event) => {
  const req = event.request;
  if (req.method !== 'GET') return;
  const url = new URL(req.url);

  // Navigations: network-first, cached SPA shell offline.
  if (req.mode === 'navigate') {
    event.respondWith(
      fetch(req).catch(() =>
        caches.match('/index.html').then((r) => r || new Response('Offline', { status: 503 }))
      )
    );
    return;
  }

  // Map tiles: cache-first — the map renders from cache when offline.
  if (/(^|\.)tile\.openstreetmap\.org$/.test(url.hostname)) {
    event.respondWith(
      caches.open(TILE_CACHE).then(async (cache) => {
        const hit = await cache.match(req);
        if (hit) return hit;
        try {
          const res = await fetch(req);
          if (res.ok) {
            cache.put(req, res.clone());
            trimCache(TILE_CACHE, TILE_LIMIT);
          }
          return res;
        } catch (e) {
          return new Response('', { status: 504, statusText: 'Tile offline' });
        }
      })
    );
    return;
  }

  // Same-origin assets: stale-while-revalidate.
  if (url.origin === self.location.origin) {
    event.respondWith(
      caches.open(SHELL_CACHE).then(async (cache) => {
        const hit = await cache.match(req);
        const network = fetch(req)
          .then((res) => {
            if (res.ok) cache.put(req, res.clone());
            return res;
          })
          .catch(() => hit);
        return hit || network;
      })
    );
    return;
  }

  // Backend API GETs: network-first, last-known data when offline.
  if (url.pathname.startsWith('/api/')) {
    event.respondWith(
      caches.open(API_CACHE).then(async (cache) => {
        try {
          const res = await fetch(req);
          if (res.ok) cache.put(req, res.clone());
          return res;
        } catch (e) {
          const hit = await cache.match(req);
          if (hit) {
            const body = await hit.json();
            return new Response(JSON.stringify({ ...body, __offline: true }), {
              status: 200,
              headers: { 'Content-Type': 'application/json' },
            });
          }
          throw e;
        }
      })
    );
    return;
  }
});
