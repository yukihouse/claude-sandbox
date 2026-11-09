// Service Worker for 氷原の烽火: lets the game start and play offline.
//
// - The game itself (one HTML file plus manifest and icons) is network-first:
//   online players always get the latest build, offline players get the copy
//   saved on their last visit. A slow network falls back to that copy after
//   a few seconds. Entries are keyed without the query string, so links with
//   tracking parameters do not pile up extra copies.
// - Google Fonts are cache-first: font files never change at a given URL.
//   Only successful CORS responses are kept (the stylesheet <link> has
//   crossorigin), so an error page is never stored. The page asks for the
//   pieces covering all game text once this worker controls it (src/pwa.ts).
// - Failing to store a response (e.g. storage quota) never fails the request.

const CACHE = 'hyogen-no-hoka-v1';
const CORE = [
  './',
  './manifest.webmanifest',
  './icon.svg',
  './icon-192.png',
  './icon-512.png',
  './apple-touch-icon.png',
];
const FONT_HOSTS = ['fonts.googleapis.com', 'fonts.gstatic.com'];
const NETWORK_TIMEOUT_MS = 4000;

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches
      .open(CACHE)
      .then((cache) => cache.addAll(CORE))
      .then(() => self.skipWaiting()),
  );
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches
      .keys()
      .then((keys) => Promise.all(keys.filter((k) => k !== CACHE).map((k) => caches.delete(k))))
      .then(() => self.clients.claim()),
  );
});

self.addEventListener('fetch', (event) => {
  const req = event.request;
  if (req.method !== 'GET') return;
  const url = new URL(req.url);
  if (FONT_HOSTS.includes(url.hostname)) {
    event.respondWith(cacheFirst(req));
  } else if (url.origin === self.location.origin) {
    event.respondWith(networkFirst(req, url));
  }
});

/** Store a response without letting a storage failure reach the caller. */
async function store(key, res) {
  try {
    const cache = await caches.open(CACHE);
    await cache.put(key, res);
  } catch {
    // storage full or unavailable: the game still works online
  }
}

async function cacheFirst(req) {
  const cached = await caches.match(req);
  if (cached) return cached;
  const res = await fetch(req);
  if (res.ok) void store(req, res.clone());
  return res;
}

async function networkFirst(req, url) {
  // one entry per page, whatever the query string
  const key = req.mode === 'navigate' ? './' : url.origin + url.pathname;
  const network = fetch(req).then((res) => {
    if (res.ok) void store(key, res.clone());
    return res;
  });
  // if the timeout wins, a later network failure must not be reported as unhandled
  network.catch(() => {});
  const timeout = new Promise((resolve) => setTimeout(resolve, NETWORK_TIMEOUT_MS));
  try {
    const res = await Promise.race([network, timeout]);
    if (res) return res;
  } catch {
    // offline: fall through to the saved copy
  }
  const cached = await caches.match(key);
  return cached ?? network;
}
