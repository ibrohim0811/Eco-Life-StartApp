const CACHE_NAME = 'eco-video-v1';
const VIDEOS_TO_CACHE = [
    '/static/videos/eco_logo.mp4' // Videongning aniq yo'li
];

self.addEventListener('install', (event) => {
    event.waitUntil(
        caches.open(CACHE_NAME).then((cache) => {
            console.log('Video keshlanmoqda...');
            return cache.addAll(VIDEOS_TO_CACHE);
        })
    );
});

// So'rov bo'lganda keshdan tekshiramiz
self.addEventListener('fetch', (event) => {
    if (event.request.url.includes('.mp4')) {
        event.respondWith(
            caches.match(event.request).then((response) => {
                // Agar keshda bo'lsa keshdan, bo'lmasa tarmoqdan (network) oladi
                return response || fetch(event.request);
            })
        );
    }
});