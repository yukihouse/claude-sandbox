// Service Worker for 氷原の烽火: lets the game start and play offline.
//
// - The game itself (one HTML file plus manifest and icons) is network-first:
//   online players always get the latest build, offline players get the copy
//   saved on their last visit. A slow network falls back to that copy after
//   a few seconds.
// - Google Fonts are cache-first: font files never change at a given URL.
//   Japanese fonts are split into many small files, so only the characters
//   already seen online are kept; anything else uses the system font offline.

const CACHE = 'hyogen-no-hoka-v1';
const CORE = ['./', './manifest.webmanifest', './icon.svg', './icon-192.png', './icon-512.png'];
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
    event.respondWith(networkFirst(req));
  }
});

async function cacheFirst(req) {
  const cached = await caches.match(req);
  if (cached) return cached;
  const res = await fetch(req);
  if (res.ok || res.type === 'opaque') {
    const cache = await caches.open(CACHE);
    await cache.put(req, res.clone());
  }
  return res;
}

async function networkFirst(req) {
  const cache = await caches.open(CACHE);
  const network = fetch(req).then(async (res) => {
    if (res.ok) await cache.put(req, res.clone());
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
  const cached =
    (await cache.match(req, { ignoreSearch: true })) ??
    (req.mode === 'navigate' ? await cache.match('./') : undefined);
  return cached ?? network;
}
