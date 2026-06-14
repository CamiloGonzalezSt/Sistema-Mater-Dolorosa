{% load static %}// Service Worker — Colegio Mater Dolorosa
const CACHE = 'md-cache-v1';
const SHELL = [
  '/',
  '{% static "css/base.css" %}',
  '{% static "css/publica.css" %}',
  '{% static "css/tabler-icons.subset.css" %}',
  '{% static "css/fonts/tabler-icons.subset.woff2" %}',
  '{% static "img/logo_t.png" %}',
];

self.addEventListener('install', (e) => {
  e.waitUntil(
    caches.open(CACHE).then((c) => c.addAll(SHELL).catch(() => {})).then(() => self.skipWaiting())
  );
});

self.addEventListener('activate', (e) => {
  e.waitUntil(
    caches.keys()
      .then((keys) => Promise.all(keys.filter((k) => k !== CACHE).map((k) => caches.delete(k))))
      .then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', (e) => {
  const req = e.request;
  if (req.method !== 'GET') return;

  // Navegación: red primero (evita páginas obsoletas), cae a caché offline.
  if (req.mode === 'navigate') {
    e.respondWith(fetch(req).catch(() => caches.match('/')));
    return;
  }

  // Estáticos: caché primero, y se guarda lo nuevo al vuelo.
  if (req.url.includes('/static/')) {
    e.respondWith(
      caches.match(req).then((hit) => hit || fetch(req).then((resp) => {
        const copy = resp.clone();
        caches.open(CACHE).then((c) => c.put(req, copy));
        return resp;
      }))
    );
  }
});
