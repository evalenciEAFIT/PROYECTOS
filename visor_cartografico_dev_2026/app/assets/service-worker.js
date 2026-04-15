/**
 * =============================================================================
 * SERVICE WORKER - VISOR CARTOGRÁFICO
 * =============================================================================
 * Proporciona funcionalidad offline básica y caché inteligente.
 * Estrategia: Network First con fallback a caché
 * =============================================================================
 */

const CACHE_VERSION = 'v1.0.0';
const CACHE_NAME = `visor-cartografico-${CACHE_VERSION}`;

// Archivos esenciales para cachear
const STATIC_ASSETS = [
    '/',
    '/assets/custom.css',
    '/assets/responsive.css',
    '/assets/dark-mode.css',
    '/assets/animations.css',
    '/assets/clientside.js',
    '/assets/theme-toggle.js',
    '/assets/logo.png',
    '/assets/Logo_EAFIT.png',
    '/assets/favicon.ico',
    '/assets/manifest.json'
];

// Recursos que se cachean bajo demanda
const RUNTIME_CACHE = 'visor-runtime-cache';

// Tiempo máximo de espera para network (ms)
const NETWORK_TIMEOUT = 3000;

/**
 * Instalación del Service Worker
 */
self.addEventListener('install', (event) => {
    console.log('[SW] Instalando Service Worker...');

    event.waitUntil(
        caches.open(CACHE_NAME)
            .then((cache) => {
                console.log('[SW] Cacheando archivos estáticos');
                return cache.addAll(STATIC_ASSETS);
            })
            .then(() => {
                console.log('[SW] Instalación completada');
                return self.skipWaiting();
            })
            .catch((error) => {
                console.error('[SW] Error en instalación:', error);
            })
    );
});

/**
 * Activación del Service Worker
 */
self.addEventListener('activate', (event) => {
    console.log('[SW] Activando Service Worker...');

    event.waitUntil(
        caches.keys()
            .then((cacheNames) => {
                return Promise.all(
                    cacheNames.map((cacheName) => {
                        // Eliminar cachés antiguos
                        if (cacheName !== CACHE_NAME && cacheName !== RUNTIME_CACHE) {
                            console.log('[SW] Eliminando caché antiguo:', cacheName);
                            return caches.delete(cacheName);
                        }
                    })
                );
            })
            .then(() => {
                console.log('[SW] Activación completada');
                return self.clients.claim();
            })
    );
});

/**
 * Interceptar peticiones de red
 */
self.addEventListener('fetch', (event) => {
    const { request } = event;
    const url = new URL(request.url);

    // Ignorar peticiones que no sean HTTP/HTTPS
    if (!url.protocol.startsWith('http')) {
        return;
    }

    // Ignorar peticiones a APIs externas de mapas
    if (url.hostname.includes('tile.openstreetmap.org') ||
        url.hostname.includes('cartodb.com') ||
        url.hostname.includes('arcgis.com')) {
        return;
    }

    // Estrategia: Network First con fallback a caché
    event.respondWith(
        networkFirstStrategy(request)
    );
});

/**
 * Estrategia: Network First
 * Intenta obtener de la red primero, si falla usa caché
 */
async function networkFirstStrategy(request) {
    try {
        // Intentar obtener de la red con timeout
        const networkResponse = await fetchWithTimeout(request, NETWORK_TIMEOUT);

        // Si es exitoso, actualizar caché
        if (networkResponse && networkResponse.status === 200) {
            const cache = await caches.open(RUNTIME_CACHE);
            cache.put(request, networkResponse.clone());
        }

        return networkResponse;
    } catch (error) {
        console.log('[SW] Network falló, buscando en caché:', request.url);

        // Buscar en caché
        const cachedResponse = await caches.match(request);

        if (cachedResponse) {
            return cachedResponse;
        }

        // Si no hay caché, retornar página offline
        if (request.mode === 'navigate') {
            return caches.match('/offline.html') ||
                new Response('Offline - No hay conexión disponible', {
                    status: 503,
                    statusText: 'Service Unavailable',
                    headers: new Headers({
                        'Content-Type': 'text/plain'
                    })
                });
        }

        // Para otros recursos, retornar error
        return new Response('Recurso no disponible offline', {
            status: 404,
            statusText: 'Not Found'
        });
    }
}

/**
 * Fetch con timeout
 */
function fetchWithTimeout(request, timeout) {
    return Promise.race([
        fetch(request),
        new Promise((_, reject) =>
            setTimeout(() => reject(new Error('Network timeout')), timeout)
        )
    ]);
}

/**
 * Estrategia: Cache First (alternativa, no usada actualmente)
 */
async function cacheFirstStrategy(request) {
    const cachedResponse = await caches.match(request);

    if (cachedResponse) {
        return cachedResponse;
    }

    try {
        const networkResponse = await fetch(request);

        if (networkResponse && networkResponse.status === 200) {
            const cache = await caches.open(RUNTIME_CACHE);
            cache.put(request, networkResponse.clone());
        }

        return networkResponse;
    } catch (error) {
        console.error('[SW] Fetch falló:', error);
        throw error;
    }
}

/**
 * Manejo de mensajes desde la aplicación
 */
self.addEventListener('message', (event) => {
    if (event.data && event.data.type === 'SKIP_WAITING') {
        self.skipWaiting();
    }

    if (event.data && event.data.type === 'CLEAR_CACHE') {
        event.waitUntil(
            caches.keys().then((cacheNames) => {
                return Promise.all(
                    cacheNames.map((cacheName) => caches.delete(cacheName))
                );
            })
        );
    }

    if (event.data && event.data.type === 'GET_VERSION') {
        event.ports[0].postMessage({ version: CACHE_VERSION });
    }
});

/**
 * Manejo de sincronización en segundo plano (opcional)
 */
self.addEventListener('sync', (event) => {
    if (event.tag === 'sync-data') {
        event.waitUntil(syncData());
    }
});

async function syncData() {
    console.log('[SW] Sincronizando datos...');
    // Implementar lógica de sincronización si es necesario
}

/**
 * Notificaciones Push (opcional)
 */
self.addEventListener('push', (event) => {
    const options = {
        body: event.data ? event.data.text() : 'Nueva actualización disponible',
        icon: '/assets/icons/icon-192x192.png',
        badge: '/assets/icons/badge-72x72.png',
        vibrate: [200, 100, 200],
        tag: 'visor-notification',
        requireInteraction: false
    };

    event.waitUntil(
        self.registration.showNotification('Visor Cartográfico', options)
    );
});

/**
 * Click en notificación
 */
self.addEventListener('notificationclick', (event) => {
    event.notification.close();

    event.waitUntil(
        clients.openWindow('/')
    );
});

console.log('[SW] Service Worker cargado correctamente');
