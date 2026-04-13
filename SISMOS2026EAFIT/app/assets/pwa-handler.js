/**
 * =============================================================================
 * PWA HANDLER - VISOR CARTOGRÁFICO
 * =============================================================================
 * Registra el Service Worker y maneja la instalación de PWA.
 * =============================================================================
 */

(function () {
    'use strict';

    let deferredPrompt;
    let installButton;

    /**
     * Registrar Service Worker
     */
    async function registerServiceWorker() {
        if ('serviceWorker' in navigator) {
            try {
                const registration = await navigator.serviceWorker.register('/assets/service-worker.js', {
                    scope: '/assets/'
                });

                console.log('[PWA] Service Worker registrado:', registration.scope);

                // Verificar actualizaciones
                registration.addEventListener('updatefound', () => {
                    const newWorker = registration.installing;

                    newWorker.addEventListener('statechange', () => {
                        if (newWorker.state === 'installed' && navigator.serviceWorker.controller) {
                            // Hay una nueva versión disponible
                            showUpdateNotification();
                        }
                    });
                });

                return registration;
            } catch (error) {
                console.error('[PWA] Error al registrar Service Worker:', error);
            }
        } else {
            console.warn('[PWA] Service Workers no soportados en este navegador');
        }
    }

    /**
     * Mostrar notificación de actualización disponible
     */
    function showUpdateNotification() {
        const notification = document.createElement('div');
        notification.className = 'pwa-update-notification';
        notification.innerHTML = `
            <div class="pwa-notification-content">
                <i class='bx bx-info-circle'></i>
                <span>Nueva versión disponible</span>
                <button class="btn-update">Actualizar</button>
                <button class="btn-dismiss">×</button>
            </div>
        `;

        document.body.appendChild(notification);

        // Animar entrada
        setTimeout(() => notification.classList.add('show'), 100);

        // Event listeners
        notification.querySelector('.btn-update').addEventListener('click', () => {
            window.location.reload();
        });

        notification.querySelector('.btn-dismiss').addEventListener('click', () => {
            notification.classList.remove('show');
            setTimeout(() => notification.remove(), 300);
        });
    }

    /**
     * Manejar evento de instalación de PWA
     */
    function handleInstallPrompt() {
        window.addEventListener('beforeinstallprompt', (e) => {
            // Prevenir el prompt automático
            e.preventDefault();

            // Guardar el evento para usarlo después
            deferredPrompt = e;

            // Mostrar botón de instalación personalizado
            showInstallButton();

            console.log('[PWA] Prompt de instalación capturado');
        });
    }

    /**
     * Mostrar botón de instalación
     */
    function showInstallButton() {
        // Buscar contenedor para el botón
        const container = document.querySelector('.float-pill') ||
            document.querySelector('.floating-header-container');

        if (!container || document.querySelector('.pwa-install-btn')) {
            return;
        }

        installButton = document.createElement('button');
        installButton.className = 'pwa-install-btn';
        installButton.setAttribute('aria-label', 'Instalar aplicación');
        installButton.innerHTML = `
            <i class='bx bx-download'></i>
            <span class="hide-mobile">Instalar</span>
        `;

        installButton.addEventListener('click', installPWA);

        container.appendChild(installButton);
    }

    /**
     * Instalar PWA
     */
    async function installPWA() {
        if (!deferredPrompt) {
            console.warn('[PWA] No hay prompt de instalación disponible');
            return;
        }

        // Mostrar el prompt
        deferredPrompt.prompt();

        // Esperar la respuesta del usuario
        const { outcome } = await deferredPrompt.userChoice;

        console.log(`[PWA] Usuario ${outcome === 'accepted' ? 'aceptó' : 'rechazó'} la instalación`);

        if (outcome === 'accepted') {
            // Ocultar botón de instalación
            if (installButton) {
                installButton.style.display = 'none';
            }
        }

        // Limpiar el prompt
        deferredPrompt = null;
    }

    /**
     * Detectar si la app ya está instalada
     */
    function detectInstalled() {
        window.addEventListener('appinstalled', () => {
            console.log('[PWA] Aplicación instalada exitosamente');

            // Ocultar botón de instalación
            if (installButton) {
                installButton.remove();
            }

            // Mostrar mensaje de éxito
            showInstallSuccessMessage();
        });
    }

    /**
     * Mostrar mensaje de instalación exitosa
     */
    function showInstallSuccessMessage() {
        const message = document.createElement('div');
        message.className = 'pwa-success-message';
        message.innerHTML = `
            <div class="pwa-message-content">
                <i class='bx bx-check-circle'></i>
                <span>¡Aplicación instalada correctamente!</span>
            </div>
        `;

        document.body.appendChild(message);

        setTimeout(() => message.classList.add('show'), 100);

        setTimeout(() => {
            message.classList.remove('show');
            setTimeout(() => message.remove(), 300);
        }, 3000);
    }

    /**
     * Verificar si está corriendo como PWA
     */
    function isPWA() {
        return window.matchMedia('(display-mode: standalone)').matches ||
            window.navigator.standalone === true;
    }

    /**
     * Inyectar estilos para componentes PWA
     */
    function injectStyles() {
        const styleId = 'pwa-styles';

        if (document.getElementById(styleId)) return;

        const styles = `
            /* Botón de instalación */
            .pwa-install-btn {
                background-color: var(--dagran-gold);
                color: var(--dagran-navy);
                border: none;
                padding: 8px 16px;
                border-radius: 8px;
                font-weight: 600;
                cursor: pointer;
                display: flex;
                align-items: center;
                gap: 8px;
                transition: all 0.3s ease;
                font-family: 'Poppins', sans-serif;
                font-size: 0.9rem;
                margin-left: 10px;
            }
            
            .pwa-install-btn:hover {
                background-color: var(--dagran-gold-hover);
                transform: translateY(-2px);
                box-shadow: 0 4px 12px rgba(245, 200, 0, 0.4);
            }
            
            .pwa-install-btn i {
                font-size: 1.2rem;
            }
            
            /* Notificación de actualización */
            .pwa-update-notification {
                position: fixed;
                bottom: -100px;
                left: 50%;
                transform: translateX(-50%);
                background: var(--bg-elevated, white);
                padding: 16px 24px;
                border-radius: 12px;
                box-shadow: 0 10px 30px rgba(0, 0, 0, 0.2);
                z-index: 10000;
                transition: bottom 0.3s ease;
                border: 2px solid var(--dagran-gold);
            }
            
            .pwa-update-notification.show {
                bottom: 20px;
            }
            
            .pwa-notification-content {
                display: flex;
                align-items: center;
                gap: 12px;
                color: var(--text-primary, #0a2240);
            }
            
            .pwa-notification-content i {
                font-size: 1.5rem;
                color: var(--dagran-gold);
            }
            
            .pwa-notification-content .btn-update {
                background-color: var(--dagran-gold);
                color: var(--dagran-navy);
                border: none;
                padding: 6px 16px;
                border-radius: 6px;
                font-weight: 600;
                cursor: pointer;
                transition: all 0.2s ease;
            }
            
            .pwa-notification-content .btn-update:hover {
                background-color: var(--dagran-gold-hover);
            }
            
            .pwa-notification-content .btn-dismiss {
                background: none;
                border: none;
                font-size: 1.5rem;
                cursor: pointer;
                color: var(--text-secondary, #666);
                padding: 0 8px;
            }
            
            /* Mensaje de éxito */
            .pwa-success-message {
                position: fixed;
                top: -100px;
                left: 50%;
                transform: translateX(-50%);
                background: var(--success-color, #10b981);
                color: white;
                padding: 16px 24px;
                border-radius: 12px;
                box-shadow: 0 10px 30px rgba(0, 0, 0, 0.2);
                z-index: 10000;
                transition: top 0.3s ease;
            }
            
            .pwa-success-message.show {
                top: 20px;
            }
            
            .pwa-message-content {
                display: flex;
                align-items: center;
                gap: 12px;
                font-weight: 600;
            }
            
            .pwa-message-content i {
                font-size: 1.5rem;
            }
            
            /* Responsive */
            @media (max-width: 768px) {
                .pwa-install-btn {
                    padding: 6px 12px;
                    font-size: 0.85rem;
                }
                
                .pwa-update-notification,
                .pwa-success-message {
                    width: 90%;
                    max-width: 400px;
                }
            }
        `;

        const styleElement = document.createElement('style');
        styleElement.id = styleId;
        styleElement.textContent = styles;
        document.head.appendChild(styleElement);
    }

    /**
     * Inicialización
     */
    function init() {
        console.log('[PWA] Inicializando PWA Handler...');

        // Inyectar estilos
        injectStyles();

        // Registrar Service Worker
        registerServiceWorker();

        // Manejar instalación
        handleInstallPrompt();
        detectInstalled();

        // Verificar si ya está instalado
        if (isPWA()) {
            console.log('[PWA] Aplicación corriendo como PWA');
            document.body.classList.add('pwa-mode');
        }
    }

    // Iniciar cuando el DOM esté listo
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }

    // Exponer API pública
    window.PWAHandler = {
        install: installPWA,
        isPWA: isPWA
    };

})();

console.log('[PWA Handler] Script cargado correctamente');
