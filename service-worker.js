const cacheName = "ginkobus-cache-v1";

const contentToCache = [
    "./manifest.json"
]

self.addEventListener("install", (e) => {
    console.log("[Service Worker] Install");
    e.waitUntil(
      (async () => {
        const cache = await caches.open(cacheName);
        console.log("[Service Worker] Caching all: app shell and content");
        await cache.addAll(contentToCache);
      })(),
    );
});

self.addEventListener("fetch", (e) => {
    if(!e.request.url.startsWith("http")){return;}
    e.respondWith(
            fetch(e.request).then(async(response) => {
                const cache = await caches.open(cacheName);
                console.log(`[Service Worker] Fetched from network, caching new ressource: ${e.request.url}`);
                cache.put(e.request, response.clone());
                return response;
            })
            .catch(async () => {
                const r = await caches.match(e.request);
                console.log(`[Service Worker] Fetching resource from cache: ${e.request.url}`);
                return r;
            }))
});