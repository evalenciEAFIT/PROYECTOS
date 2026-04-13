// =============================================================================
// CLIENTSIDE JAVASCRIPT - INTERACCIONES DEL NAVEGADOR
// =============================================================================
// Este archivo contiene lógica JavaScript que se ejecuta en el navegador del cliente
// para mejorar la interactividad sin necesidad de comunicación con el servidor.

// -----------------------------------------------------------------------------
// MANEJO DE TECLADO - Tecla ESC para cerrar modales
// -----------------------------------------------------------------------------
document.addEventListener('keydown', function (event) {
    // Detectar si se presionó la tecla Escape (compatibilidad cross-browser)
    if (event.key === 'Escape' || event.key === 'Esc') {
        // Buscar el botón de cierre del modal de ayuda
        const btn = document.getElementById('close-help-esc');
        // Si existe, simular un click para cerrar el modal
        if (btn) btn.click();
    }
});

// -----------------------------------------------------------------------------
// DASH EXTENSIONS - Funciones para componentes Dash Leaflet
// -----------------------------------------------------------------------------
// Estas funciones se inyectan en el objeto global de Dash para personalizar
// el comportamiento de los mapas interactivos.

window.dash_props = Object.assign({}, window.dash_props, {
    module: {
        /**
         * style_handle: Función para aplicar estilos dinámicos a features del mapa
         * @param {Object} feature - Feature GeoJSON con propiedades
         * @param {Object} context - Contexto del mapa (no usado actualmente)
         * @returns {Object} Objeto de estilo CSS para el polígono
         * 
         * Esta función lee el estilo pre-calculado en el servidor (color, peso, opacidad)
         * y lo aplica a cada polígono del mapa. Evita cálculos pesados en el cliente.
         */
        style_handle: function (feature, context) {
            return feature.properties.style;
        },

        /**
         * on_each_feature: Función ejecutada para cada feature al cargar el mapa
         * @param {Object} feature - Feature GeoJSON
         * @param {Object} layer - Capa Leaflet correspondiente
         * 
         * Configura tooltips (cuadros informativos al hover) si la feature
         * tiene la propiedad 'tooltip' definida.
         */
        on_each_feature: function (feature, layer) {
            if (feature.properties.tooltip) {
                // En lugar de usar bindTooltip (que queda atrapado en el transform de Leaflet),
                // usamos eventos nativos para mostrar un panel fijo en el body.
                layer.on('mouseover', function (e) {
                    let tooltipBox = document.getElementById('dagran-fixed-tooltip');
                    if (!tooltipBox) {
                        tooltipBox = document.createElement('div');
                        tooltipBox.id = 'dagran-fixed-tooltip';
                        tooltipBox.className = 'custom-tooltip fixed-right-tooltip';
                        document.body.appendChild(tooltipBox);
                    }
                    tooltipBox.innerHTML = feature.properties.tooltip;
                    tooltipBox.style.display = 'block';
                });

                layer.on('mouseout', function (e) {
                    let tooltipBox = document.getElementById('dagran-fixed-tooltip');
                    if (tooltipBox) {
                        tooltipBox.style.display = 'none';
                    }
                });
            }
        }
    }
});
