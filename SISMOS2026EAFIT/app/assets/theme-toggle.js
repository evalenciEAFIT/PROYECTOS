/**
 * =============================================================================
 * THEME TOGGLE - VISOR CARTOGRÁFICO
 * =============================================================================
 * Maneja el cambio entre modo claro y oscuro.
 * - Respeta la preferencia del sistema
 * - Persiste la selección del usuario en localStorage
 * - Transiciones suaves entre temas
 * =============================================================================
 */

(function () {
    'use strict';

    // Constantes
    const THEME_KEY = 'visor-cartografico-theme';
    const THEME_LIGHT = 'light';
    const THEME_DARK = 'dark';

    /**
     * Obtiene el tema guardado o detecta la preferencia del sistema
     */
    function getInitialTheme() {
        // 1. Verificar si hay tema guardado
        const savedTheme = localStorage.getItem(THEME_KEY);
        if (savedTheme) {
            return savedTheme;
        }

        // 2. Detectar preferencia del sistema
        if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
            return THEME_DARK;
        }

        // 3. Default: light
        return THEME_LIGHT;
    }

    /**
     * Aplica el tema al documento
     */
    function applyTheme(theme) {
        const root = document.documentElement;

        if (theme === THEME_DARK) {
            root.setAttribute('data-theme', 'dark');
        } else {
            root.removeAttribute('data-theme');
        }

        // Guardar preferencia
        localStorage.setItem(THEME_KEY, theme);

        // Emitir evento personalizado para que otros componentes reaccionen
        window.dispatchEvent(new CustomEvent('themeChanged', { detail: { theme } }));

        console.log(`[Theme] Aplicado: ${theme}`);
    }

    /**
     * Alterna entre temas
     */
    function toggleTheme() {
        const currentTheme = document.documentElement.getAttribute('data-theme') === 'dark'
            ? THEME_DARK
            : THEME_LIGHT;

        const newTheme = currentTheme === THEME_DARK ? THEME_LIGHT : THEME_DARK;

        applyTheme(newTheme);
        updateToggleButton(newTheme);

        return newTheme;
    }

    /**
     * Actualiza el estado visual del botón toggle
     */
    function updateToggleButton(theme) {
        const toggleButtons = document.querySelectorAll('.theme-toggle-btn');

        toggleButtons.forEach(btn => {
            if (theme === THEME_DARK) {
                btn.setAttribute('aria-label', 'Cambiar a modo claro');
                btn.classList.add('dark-mode');
            } else {
                btn.setAttribute('aria-label', 'Cambiar a modo oscuro');
                btn.classList.remove('dark-mode');
            }
        });
    }

    /**
     * Crea el botón de toggle si no existe
     */
    function createToggleButton() {
        // Opción de cambio de contraste deshabilitada
        return;

        // Verificar si ya existe
        if (document.querySelector('.theme-toggle-btn')) {
            return;
        }

        const currentTheme = getInitialTheme();

        // Crear botón
        const button = document.createElement('button');
        button.className = 'theme-toggle-btn';
        button.setAttribute('aria-label',
            currentTheme === THEME_DARK ? 'Cambiar a modo claro' : 'Cambiar a modo oscuro'
        );
        button.innerHTML = `
            <div class="theme-toggle">
                <div class="theme-toggle-slider"></div>
            </div>
        `;

        // Event listener
        button.addEventListener('click', function (e) {
            e.preventDefault();
            toggleTheme();

            // Animación de feedback
            this.classList.add('clicked');
            setTimeout(() => this.classList.remove('clicked'), 300);
        });

        // Insertar en el header (buscar el contenedor apropiado)
        const headerContainer = document.querySelector('.float-pill') ||
            document.querySelector('.floating-header-container') ||
            document.body;

        if (headerContainer) {
            headerContainer.appendChild(button);
        }

        updateToggleButton(currentTheme);
    }

    /**
     * Escucha cambios en la preferencia del sistema
     */
    function watchSystemTheme() {
        if (!window.matchMedia) return;

        const darkModeQuery = window.matchMedia('(prefers-color-scheme: dark)');

        darkModeQuery.addEventListener('change', (e) => {
            // Solo aplicar si el usuario no ha seleccionado manualmente
            const savedTheme = localStorage.getItem(THEME_KEY);
            if (!savedTheme) {
                const newTheme = e.matches ? THEME_DARK : THEME_LIGHT;
                applyTheme(newTheme);
                updateToggleButton(newTheme);
            }
        });
    }

    /**
     * Actualiza los gráficos de Plotly para el tema actual
     */
    function updatePlotlyTheme(theme) {
        // Buscar todos los gráficos de Plotly
        const plotlyGraphs = document.querySelectorAll('.plotly-graph-div');

        plotlyGraphs.forEach(graph => {
            if (window.Plotly && graph.data) {
                const update = {
                    'paper_bgcolor': theme === THEME_DARK ? '#2d3748' : '#ffffff',
                    'plot_bgcolor': theme === THEME_DARK ? '#1a1f26' : '#ffffff',
                    'font.color': theme === THEME_DARK ? '#e4e6eb' : '#0a2240'
                };

                try {
                    window.Plotly.relayout(graph, update);
                } catch (e) {
                    console.warn('[Theme] No se pudo actualizar gráfico Plotly:', e);
                }
            }
        });
    }

    /**
     * Actualiza los tiles del mapa Leaflet
     */
    function updateMapTheme(theme) {
        // Este método debe ser llamado desde el código Python/Dash
        // Aquí solo emitimos el evento
        window.dispatchEvent(new CustomEvent('mapThemeChange', {
            detail: { theme }
        }));
    }

    /**
     * Inicialización
     */
    function init() {
        console.log('[Theme] Inicializando sistema de temas...');

        // Aplicar tema inicial inmediatamente (antes del render)
        const initialTheme = getInitialTheme();
        applyTheme(initialTheme);

        // Esperar a que el DOM esté listo
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', function () {
                createToggleButton();
                watchSystemTheme();
            });
        } else {
            createToggleButton();
            watchSystemTheme();
        }

        // Escuchar cambios de tema para actualizar componentes
        window.addEventListener('themeChanged', function (e) {
            const theme = e.detail.theme;

            // Actualizar gráficos con un pequeño delay
            setTimeout(() => {
                updatePlotlyTheme(theme);
                updateMapTheme(theme);
            }, 300);
        });
    }

    // Exponer API pública
    window.ThemeManager = {
        toggle: toggleTheme,
        apply: applyTheme,
        getCurrent: () => {
            return document.documentElement.getAttribute('data-theme') === 'dark'
                ? THEME_DARK
                : THEME_LIGHT;
        },
        LIGHT: THEME_LIGHT,
        DARK: THEME_DARK
    };

    // Iniciar
    init();

})();

/**
 * =============================================================================
 * ESTILOS ADICIONALES PARA EL BOTÓN DE TOGGLE
 * =============================================================================
 */

// Inyectar estilos si no están en CSS
(function injectToggleStyles() {
    const styleId = 'theme-toggle-styles';

    if (document.getElementById(styleId)) return;

    const styles = `
        .theme-toggle-btn {
            background: none;
            border: none;
            cursor: pointer;
            padding: 5px;
            margin-left: 10px;
            transition: transform 0.2s ease;
        }
        
        .theme-toggle-btn:hover {
            transform: scale(1.05);
        }
        
        .theme-toggle-btn.clicked {
            transform: scale(0.95);
        }
        
        .theme-toggle-btn:focus-visible {
            outline: 2px solid var(--dagran-gold);
            outline-offset: 2px;
            border-radius: 20px;
        }
        
        /* Responsive */
        @media (max-width: 768px) {
            .theme-toggle-btn {
                margin-left: 5px;
            }
            
            .theme-toggle {
                width: 50px;
                height: 25px;
            }
            
            .theme-toggle-slider {
                width: 18px;
                height: 18px;
            }
            
            :root[data-theme="dark"] .theme-toggle-slider {
                transform: translateX(25px);
            }
        }
    `;

    const styleElement = document.createElement('style');
    styleElement.id = styleId;
    styleElement.textContent = styles;
    document.head.appendChild(styleElement);
})();

console.log('[Theme Toggle] Script cargado correctamente');
