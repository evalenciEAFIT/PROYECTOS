// Configuraciones Globales
const API_PROXY = '/proxy/api';
let map, markersLayer;
let geoCircleLayer = null; // Capa para dibujar el círculo del filtro radio
let stationsData = [];
let variablesData = [];
let abortController = null;
let selectedStations = new Set(); // Guarda los station_code seleccionados explícitamente

// Toast config (SweetAlert2)
const Toast = Swal.mixin({
    toast: true,
    position: 'top-end',
    showConfirmButton: false,
    timer: 3000,
    timerProgressBar: true
});

// Inicialización al cargar la página
document.addEventListener('DOMContentLoaded', async () => {
    // Detección de dispositivos móviles o tabletas
    const isMobileDevice = /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent) || window.innerWidth < 992;
    if (isMobileDevice) {
        Swal.fire({
            title: 'Atención: Dispositivo Móvil Detectado',
            text: 'Esta aplicación web está orientada a la extracción y descarga de conjuntos de datos masivos hacia archivos (CSV, Excel). Para una experiencia óptima, te recomendamos acceder desde una computadora de escritorio.',
            icon: 'warning',
            confirmButtonText: 'Entendido',
            confirmButtonColor: '#0d6efd'
        });
    }

    // Activar tooltips de Bootstrap
    const tooltipTriggerList = document.querySelectorAll('[data-bs-toggle="tooltip"]');
    [...tooltipTriggerList].map(tooltipTriggerEl => new bootstrap.Tooltip(tooltipTriggerEl));

    initMap();
    initDates();
    await fetchVariables();
    await fetchStations();

    // Event Listener del Formulario Principal
    document.getElementById('filterForm').addEventListener('submit', (e) => {
        e.preventDefault();
        fetchMeasurements();
    });

    // Limpiar selección manual
    document.getElementById('clearSelectionBtn').addEventListener('click', () => {
        selectedStations.clear();
        updateSelectionUI();
        plotStationsOnMap(stationsData); // Redibujar todos normales
        Toast.fire({ icon: 'info', title: 'Selección limpiada' });
    });

    // Eventos on-change para dibujar el círculo del filtro geoespacial
    const drawCircleEvt = () => { drawGeoFilterCircle(); };
    document.getElementById('pointLat').addEventListener('input', drawCircleEvt);
    document.getElementById('pointLng').addEventListener('input', drawCircleEvt);
    document.getElementById('radiusKm').addEventListener('input', drawCircleEvt);

    // Event Listeners de Exportación
    document.getElementById('exportCsvBtn').addEventListener('click', () => exportData('csv'));
    document.getElementById('exportExcelBtn').addEventListener('click', () => exportData('excel'));
    document.getElementById('exportJsonBtn').addEventListener('click', () => exportData('json'));

    // Re-dibujar mapa si cambia el tipo de estación (filtro visual activo)
    document.getElementById('stationTypeSelect').addEventListener('change', () => {
        plotStationsOnMap(stationsData);
    });

    document.getElementById('regionSelect').addEventListener('change', () => {
        plotStationsOnMap(stationsData);
    });

    document.getElementById('municipioSelect').addEventListener('change', () => {
        plotStationsOnMap(stationsData);
    });

    // Accesibilidad
    document.getElementById('toggleContrastBtn').addEventListener('click', () => {
        document.body.classList.toggle('high-contrast');
    });

    let currentFontSize = 100;
    document.getElementById('increaseTextBtn').addEventListener('click', () => {
        if (currentFontSize < 130) {
            currentFontSize += 10;
            document.documentElement.style.fontSize = currentFontSize + '%';
        }
    });

    document.getElementById('decreaseTextBtn').addEventListener('click', () => {
        if (currentFontSize > 80) {
            currentFontSize -= 10;
            document.documentElement.style.fontSize = currentFontSize + '%';
        }
    });

    document.getElementById('toggleGrayscaleBtn').addEventListener('click', () => {
        document.body.classList.toggle('grayscale');
    });


    document.getElementById('toggleHighlightLinksBtn').addEventListener('click', () => {
        document.body.classList.toggle('highlight-links');
    });


    document.getElementById('accessibilityInfoBtn').addEventListener('click', () => {
        Swal.fire({
            title: 'Accesibilidad Web',
            html: '<p class="text-start">La accesibilidad web abarca todas las discapacidades que afectan el acceso a la Web, incluidas:</p>' +
                '<ul class="text-start">' +
                '<li>Auditivo</li>' +
                '<li>Cognitivo</li>' +
                '<li>Neurológico</li>' +
                '<li>Físico</li>' +
                '<li>Discurso</li>' +
                '<li>Visual</li>' +
                '</ul>',
            icon: 'info',
            confirmButtonText: 'Entendido'
        });
    });

    // Sidebar Toggle
    document.getElementById('toggleSidebarBtn').addEventListener('click', () => {
        const sidebar = document.getElementById('sidebar');
        const resizerH = document.getElementById('resizer-h');
        sidebar.classList.toggle('d-none');
        if (resizerH) resizerH.classList.toggle('d-none');
        // Delay map update slightly to allow CSS reflow
        setTimeout(() => map && map.invalidateSize(), 50);
    });

    // Observe side-bar width changes to refresh Leaflet Map smoothly
    const resizeObserver = new ResizeObserver(() => {
        if (map) {
            map.invalidateSize();
        }
    });
    resizeObserver.observe(document.getElementById('sidebar'));

    // Resizer Logic
    const sidebar = document.getElementById('sidebar');
    const resizerH = document.getElementById('resizer-h');
    const containerV = document.getElementById('main-content');
    const panelTop = document.getElementById('map-container');
    const resizerV = document.getElementById('resizer-v');

    let isResizingH = false;
    let isResizingV = false;

    resizerH.addEventListener('mousedown', function (e) {
        isResizingH = true;
        document.body.style.cursor = 'col-resize';
        resizerH.classList.add('resizing');
        e.preventDefault();
    });

    resizerV.addEventListener('mousedown', function (e) {
        isResizingV = true;
        document.body.style.cursor = 'row-resize';
        resizerV.classList.add('resizing');
        if (map) {
             map.dragging.disable();
        }
        e.preventDefault();
    });

    document.addEventListener('mousemove', function (e) {
        if (!isResizingH && !isResizingV) return;

        if (isResizingH) {
            let newWidth = e.clientX;
            if (newWidth < 320) newWidth = 320;
            if (newWidth > window.innerWidth * 0.8) newWidth = window.innerWidth * 0.8;
            sidebar.style.width = newWidth + 'px';
            if (map) map.invalidateSize();
        }

        if (isResizingV) {
            const containerRect = containerV.getBoundingClientRect();
            // account for padding/margin
            let newHeight = e.clientY - containerRect.top;
            
            if (newHeight < 200) newHeight = 200;
            if (newHeight > containerRect.height - 200) newHeight = containerRect.height - 200;
            
            panelTop.style.flex = 'none';
            panelTop.style.height = newHeight + 'px';
            if (map) map.invalidateSize();
        }
    });

    document.addEventListener('mouseup', function () {
        if (isResizingH) {
            isResizingH = false;
            document.body.style.cursor = '';
            resizerH.classList.remove('resizing');
            if (map) {
                setTimeout(() => map.invalidateSize(), 50);
            }
        }
        if (isResizingV) {
            isResizingV = false;
            document.body.style.cursor = '';
            resizerV.classList.remove('resizing');
            if (map) {
                map.dragging.enable();
                setTimeout(() => map.invalidateSize(), 50);
            }
        }
    });
});

// Funcion Global para Presets de Fecha (Llamada desde HTML onclick)
window.setPresetDate = function (days) {
    const end = new Date();
    // Si days es 1 (Hoy), empieza desde la medianoche de hoy
    let start;
    let aggValue = '';

    if (days === 'all') {
        start = new Date('1970-01-01T00:00:00');
        aggValue = '1 month'; // Histórico -> 1 Mes
    } else if (days === 1) {
        start = new Date();
        start.setHours(0, 0, 0, 0);
        aggValue = ''; // Hoy -> Crudo
    } else {
        start = new Date(end.getTime() - (days * 24 * 60 * 60 * 1000));
        // Determinar agrupación óptima según cantidad de días
        if (days === 3) aggValue = '15m'; // 3 Días -> 15 min
        else if (days === 7) aggValue = '30m'; // 1 Semana -> 30 min
        else if (days === 15) aggValue = '1h'; // 15 Días -> 1 hr
        else if (days === 30) aggValue = '6h'; // 1 Mes -> 6 hr
        else if (days === 90) aggValue = '12h'; // Trimestre -> 12 hr
        else if (days === 180) aggValue = '1d'; // Semestre -> 1 día
        else if (days === 365) aggValue = '1 week'; // 1 Año -> 1 semana
        else aggValue = '';
    }

    // Convertir a formato local datetime (YYYY-MM-DDThh:mm)
    const tzOffset = (new Date()).getTimezoneOffset() * 60000; // offset en milisegundos
    const localStart = new Date(start.getTime() - tzOffset).toISOString().slice(0, 16);
    const localEnd = new Date(end.getTime() - tzOffset).toISOString().slice(0, 16);

    document.getElementById('startTime').value = localStart;
    document.getElementById('endTime').value = localEnd;
    
    // Asignar el valor óptimo de agrupación seleccionado
    const aggSelect = document.getElementById('aggregateSelect');
    if (aggSelect) {
        aggSelect.value = aggValue;
    }

    Toast.fire({ icon: 'success', title: 'Filtros de tiempo y agrupación ajustados', timer: 2000 });
};

// Controles Globales de Variables
window.selectAllVariables = function () {
    const select = document.getElementById('variableSelect');
    for (let i = 0; i < select.options.length; i++) select.options[i].selected = true;
};

window.clearVariables = function () {
    const select = document.getElementById('variableSelect');
    for (let i = 0; i < select.options.length; i++) select.options[i].selected = false;
};

// Controles Globales de Tipo Estación
window.selectAllStationTypes = function () {
    const select = document.getElementById('stationTypeSelect');
    for (let i = 0; i < select.options.length; i++) select.options[i].selected = true;
    plotStationsOnMap(stationsData);
};

window.clearStationTypes = function () {
    const select = document.getElementById('stationTypeSelect');
    for (let i = 0; i < select.options.length; i++) select.options[i].selected = false;
    plotStationsOnMap(stationsData);
};

// Controles Globales de Regiones
window.selectAllRegions = function () {
    const select = document.getElementById('regionSelect');
    for (let i = 0; i < select.options.length; i++) select.options[i].selected = true;
    plotStationsOnMap(stationsData);
};

window.clearRegions = function () {
    const select = document.getElementById('regionSelect');
    for (let i = 0; i < select.options.length; i++) select.options[i].selected = false;
    plotStationsOnMap(stationsData);
};

// Controles Globales de Municipios
window.selectAllMunicipios = function () {
    const select = document.getElementById('municipioSelect');
    for (let i = 0; i < select.options.length; i++) select.options[i].selected = true;
    plotStationsOnMap(stationsData);
};

window.clearMunicipios = function () {
    const select = document.getElementById('municipioSelect');
    for (let i = 0; i < select.options.length; i++) select.options[i].selected = false;
    plotStationsOnMap(stationsData);
};

// Control limpiar filtro Geoespacial (Botón UI)
window.clearGeoFilter = function () {
    document.getElementById('pointLat').value = '';
    document.getElementById('pointLng').value = '';
    document.getElementById('radiusKm').value = '5'; // Reset default
    drawGeoFilterCircle(); // Esto lo borrará del mapa

    // También limpiar las estaciones seleccionadas manualmente
    document.getElementById('clearSelectionBtn').click();

    Toast.fire({ icon: 'info', title: 'Filtros Geográficos Limpios' });
    plotStationsOnMap(stationsData); // Actualizar los pines normales
};

// Traductor de Códigos de Estación a Tipo
function getStationTypeStr(code) {
    if (!code) return 'Desconocido';
    const s = stationsData.find(st => st.station_code === code);
    if (s && s.tipo) return s.tipo;
    return 'Otro';
}

function initMap() {
    map = L.map('map').setView([6.2518, -75.5636], 9);
    L.tileLayer('https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png', {
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>',
        maxZoom: 20
    }).addTo(map);

    markersLayer = L.layerGroup().addTo(map);
}

function initDates() {
    window.setPresetDate('all'); // Por defecto histórico completo
}

async function fetchVariables() {
    try {
        const res = await fetch(`${API_PROXY}/variables`);
        const json = await res.json();
        const select = document.getElementById('variableSelect');
        select.innerHTML = '';

        if (json.data && json.data.length > 0) {
            variablesData = json.data;
            variablesData.forEach(v => {
                const opt = document.createElement('option');
                opt.value = v.variable_name;
                opt.textContent = `${v.variable_name} (${v.variable_unit})`;
                // Por defecto dejar seleccionado solo nivel
                if (v.variable_name === 'nivel') {
                    opt.selected = true;
                }
                select.appendChild(opt);
            });
        } else {
            select.innerHTML = '<option disabled selected class="text-danger fw-bold">No hay datos en la base de datos</option>';
        }
    } catch (err) { Toast.fire({ icon: 'error', title: "Error cargando variables" }); }
}

async function fetchStations() {
    try {
        const res = await fetch(`${API_PROXY}/stations`);
        if (!res.ok) throw new Error("HTTP Status " + res.status);
        const json = await res.json();

        if (json.data) {
            const pseudoRandom = (seed) => {
                let x = Math.sin(seed++) * 10000;
                return x - Math.floor(x);
            };

            // MAP: Limpiar espacios de station_code (char(7) in Postgres) y generar Lats/Lons
            stationsData = json.data.map((s, idx) => {
                return {
                    ...s,
                    station_code: s.station_code ? s.station_code.trim() : '',
                    lat: s.latitude !== null && s.latitude !== undefined ? s.latitude : null,
                    lon: s.longitude !== null && s.longitude !== undefined ? s.longitude : null,
                    location_name: s.location || 'Ubicación desconocida',
                    municipio: s.municipio || null,
                    region: s.region || null,
                    tipo: s.tipo || null
                };
            });

            populateLocationSelects(stationsData);
            plotStationsOnMap(stationsData);
        } else {
            throw new Error("Formato de JSON Inesperado");
        }
    } catch (err) {
        console.error("Error cargando estaciones:", err);
        Toast.fire({ icon: 'error', title: "Error cargando estaciones al Frontend" });
    }
}

function populateLocationSelects(data) {
    const rSet = new Set();
    const mSet = new Set();
    const tSet = new Set();
    data.forEach(s => {
        if (s.region) rSet.add(s.region);
        if (s.municipio) mSet.add(s.municipio);
        if (s.tipo) tSet.add(s.tipo);
    });

    const rSelect = document.getElementById('regionSelect');
    rSelect.innerHTML = '';
    if (rSet.size > 0) {
        [...rSet].sort().forEach(r => {
            const opt = document.createElement('option');
            opt.value = r; opt.textContent = r;
            rSelect.appendChild(opt);
        });
    } else {
        rSelect.innerHTML = '<option disabled class="text-danger fw-bold">No hay datos en la base de datos</option>';
    }

    const mSelect = document.getElementById('municipioSelect');
    mSelect.innerHTML = '';
    if (mSet.size > 0) {
        [...mSet].sort().forEach(m => {
            const opt = document.createElement('option');
            opt.value = m; opt.textContent = m;
            mSelect.appendChild(opt);
        });
    } else {
        mSelect.innerHTML = '<option disabled class="text-danger fw-bold">No hay datos en la base de datos</option>';
    }

    const tSelect = document.getElementById('stationTypeSelect');
    tSelect.innerHTML = '';
    if (tSet.size > 0) {
        [...tSet].sort().forEach(t => {
            const opt = document.createElement('option');
            opt.value = t; opt.textContent = t;
            opt.selected = true; // Por defecto seleccionamos todas
            tSelect.appendChild(opt);
        });
    } else {
        tSelect.innerHTML = '<option disabled class="text-danger fw-bold">No hay tipos de estación en la base de datos</option>';
    }
}

function plotStationsOnMap(stations) {
    markersLayer.clearLayers();
    const bounds = L.latLngBounds();
    const typeFilters = Array.from(document.getElementById('stationTypeSelect').selectedOptions).map(o => o.value);
    const rFilters = Array.from(document.getElementById('regionSelect').selectedOptions).map(o => o.value);
    const mFilters = Array.from(document.getElementById('municipioSelect').selectedOptions).map(o => o.value);

    let visibleCount = 0;
    stations.forEach(s => {
        if (rFilters.length > 0 && !rFilters.includes(s.region)) return;
        if (mFilters.length > 0 && !mFilters.includes(s.municipio)) return;

        if (s.lat !== null && s.lon !== null) {
            if (typeFilters.length === 0) return; // No pintar nada si no hay tipos listados
            if (!s.tipo || !typeFilters.includes(s.tipo)) return;

            let isSelected = selectedStations.has(s.station_code);

            // Además del click manual, si existe el filtro de radio y están adentró, se colorean dorado/seleccionadas
            const pLatStr = document.getElementById('pointLat').value;
            const pLngStr = document.getElementById('pointLng').value;
            const rKmStr = document.getElementById('radiusKm').value;
            if (pLatStr && pLngStr && rKmStr) {
                const pLat = parseFloat(pLatStr);
                const pLng = parseFloat(pLngStr);
                const radi = parseFloat(rKmStr);
                if (!isNaN(pLat) && !isNaN(pLng) && !isNaN(radi)) {
                    if (calculateDistance(pLat, pLng, s.lat, s.lon) <= radi) {
                        isSelected = true; // Forzamos el coloreado visual de selección si caen en el radio rojo
                    }
                }
            }

            // Asignar color Base e Ícono según Tipo de Estación
            let baseColor = '#6c757d'; // Gris por defecto
            let iconClass = 'fa-solid fa-satellite-dish'; // Icono por defecto

            if (s.tipo) {
                const tipoLower = s.tipo.toLowerCase();
                if (tipoLower.includes('nivel') || tipoLower.includes('caudal')) {
                    baseColor = '#0dcaf0'; // Cyan
                    iconClass = 'fa-solid fa-water';
                }
                if (tipoLower.includes('pluviómetro') || tipoLower.includes('pluviometro')) {
                    baseColor = '#0d6efd'; // Azul Oscuro
                    iconClass = 'fa-solid fa-cloud-showers-heavy';
                }
                if (tipoLower.includes('ambiental') || tipoLower.includes('meteorología') || tipoLower.includes('meteorologia')) {
                    baseColor = '#198754'; // Verde
                    iconClass = 'fa-solid fa-leaf';
                }
                if (tipoLower.includes('alarma')) {
                    baseColor = '#dc3545'; // Rojo
                    iconClass = 'fa-solid fa-bell';
                }
            }

            // Si está seleccionada explícitamente por el usuario
            const fillColor = isSelected ? '#ffc107' : baseColor;
            const borderColor = isSelected ? '#dc3545' : 'white';
            const iconColor = isSelected ? '#000' : '#fff'; // Icono oscuro si está seleccionado dorado

            const markerIcon = L.divIcon({
                className: 'custom-div-icon',
                html: `<div style='background-color:${fillColor}; width:28px; height:28px; border-radius:50%; border:2px solid ${borderColor}; box-shadow: 0 0 5px rgba(0,0,0,0.6); display:flex; align-items:center; justify-content:center; cursor:pointer;'>
                          <i class="${iconClass}" style="color:${iconColor}; font-size:12px;"></i>
                       </div>`,
                iconSize: [28, 28], iconAnchor: [14, 14]
            });

            const marker = L.marker([s.lat, s.lon], { icon: markerIcon });
            marker.bindTooltip(`<b>Est:</b> ${s.station_code} (${getStationTypeStr(s.station_code)})<br><small>Click para (des)seleccionar</small>`);

            marker.on('click', () => {
                if (selectedStations.has(s.station_code)) {
                    selectedStations.delete(s.station_code);
                } else {
                    selectedStations.add(s.station_code);
                    // Llenar automáticamente el punto de interés con las coordenadas de la estación anclada
                    document.getElementById('pointLat').value = s.lat.toFixed(6);
                    document.getElementById('pointLng').value = s.lon.toFixed(6);
                    drawGeoFilterCircle(); // Proyectar el círculo desde esta estación
                }
                updateSelectionUI();
                plotStationsOnMap(stationsData);
            });

            markersLayer.addLayer(marker);
            bounds.extend([s.lat, s.lon]);
            visibleCount++;
        }
    });

    if (visibleCount > 0 && bounds.isValid() && visibleCount === stations.length) {
        if (map.getZoom() < 8) map.fitBounds(bounds, { padding: [30, 30] });
    }
}

function updateSelectionUI() {
    const container = document.getElementById('selectedStationsList');
    if (selectedStations.size === 0) {
        container.innerHTML = '<em class="text-muted">Seleccione la estación en el Mapa o selecione filtros espaciales</em>';
        return;
    }

    // Convertir de Set a array visual
    const badges = Array.from(selectedStations).map(code =>
        `<span class="badge bg-primary me-1 mb-1" title="Estación seleccionada: ${code}" data-bs-toggle="tooltip">${code}</span>`
    ).join('');

    container.innerHTML = badges;
    const tooltipTriggerList = container.querySelectorAll('[data-bs-toggle="tooltip"]');
    [...tooltipTriggerList].forEach(el => new bootstrap.Tooltip(el));
}

function drawGeoFilterCircle() {
    if (geoCircleLayer) {
        map.removeLayer(geoCircleLayer);
        geoCircleLayer = null;
    }

    const pLatStr = document.getElementById('pointLat').value;
    const pLngStr = document.getElementById('pointLng').value;
    const rKmStr = document.getElementById('radiusKm').value;

    if (pLatStr && pLngStr && rKmStr) {
        const pLat = parseFloat(pLatStr);
        const pLng = parseFloat(pLngStr);
        const radiusKm = parseFloat(rKmStr);
        if (!isNaN(pLat) && !isNaN(pLng) && !isNaN(radiusKm)) {
            // Dibujar Círculo
            geoCircleLayer = L.circle([pLat, pLng], {
                color: 'red',
                fillColor: '#f03',
                fillOpacity: 0.1,
                radius: radiusKm * 1000 // Leaflet usa metros
            }).addTo(map);

            // Agregar a la lista de "Selección Manual" las estaciones dentro del radio
            let addedCount = 0;
            stationsData.forEach(s => {
                if (s.lat !== null && s.lon !== null) {
                    if (calculateDistance(pLat, pLng, s.lat, s.lon) <= radiusKm) {
                        if (!selectedStations.has(s.station_code)) {
                            selectedStations.add(s.station_code);
                            addedCount++;
                        }
                    }
                }
            });

            if (addedCount > 0) {
                Toast.fire({ icon: 'success', title: `Se incluyeron ${addedCount} estaciones del área` });
                updateSelectionUI(); // Refrescar visualmente la caja de Selección Manual
            }

            plotStationsOnMap(stationsData);
        }
    } else {
        // Redibujar clean
        plotStationsOnMap(stationsData);
    }
}

function calculateDistance(lat1, lon1, lat2, lon2) {
    const R = 6371;
    const dLat = (lat2 - lat1) * Math.PI / 180;
    const dLon = (lon2 - lon1) * Math.PI / 180;
    const a = Math.sin(dLat / 2) * Math.sin(dLat / 2) + Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) * Math.sin(dLon / 2) * Math.sin(dLon / 2);
    const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
    return R * c;
}

function buildQueryParams(format = 'json') {
    const params = new URLSearchParams();
    let sTime = new Date(document.getElementById('startTime').value).toISOString();
    let eTime = new Date(document.getElementById('endTime').value).toISOString();
    params.append('start_time', sTime);
    params.append('end_time', eTime);

    const selVars = Array.from(document.getElementById('variableSelect').selectedOptions).map(o => o.value);
    if (selVars.length > 0) params.append('variable_name', selVars.join(','));

    // Lógica Estaciones y Tipo
    const typeFilters = Array.from(document.getElementById('stationTypeSelect').selectedOptions).map(o => o.value);

    let codesToQuery = [];

    if (selectedStations.size > 0) {
        codesToQuery = Array.from(selectedStations);
    } else {
        // En su defecto, verificamos geo-filtro
        const pLatStr = document.getElementById('pointLat').value;
        const pLngStr = document.getElementById('pointLng').value;
        const rKmStr = document.getElementById('radiusKm').value;

        if (pLatStr && pLngStr && rKmStr) {
            const pLat = parseFloat(pLatStr);
            const pLng = parseFloat(pLngStr);
            const radius = parseFloat(rKmStr);
            if (!isNaN(pLat) && !isNaN(pLng) && !isNaN(radius)) {
                codesToQuery = stationsData
                    .filter(s => calculateDistance(pLat, pLng, s.lat, s.lon) <= radius)
                    .map(s => s.station_code);
            }
        } else {
            // Todos los visibles
            const rFilters = Array.from(document.getElementById('regionSelect').selectedOptions).map(o => o.value);
            const mFilters = Array.from(document.getElementById('municipioSelect').selectedOptions).map(o => o.value);
            codesToQuery = stationsData.filter(s => {
                if (rFilters.length > 0 && !rFilters.includes(s.region)) return false;
                if (mFilters.length > 0 && !mFilters.includes(s.municipio)) return false;
                return true;
            }).map(s => s.station_code);
        }
    }

    // Intersectar con el filtro de TIPO seleccionado
    if (typeFilters.length > 0) {
        codesToQuery = codesToQuery.filter(c => {
            const s = stationsData.find(st => st.station_code === c);
            return s && s.tipo && typeFilters.includes(s.tipo);
        });
    } else {
        codesToQuery = ['NO_MATCH_TYPE']; // forzar búsqueda en 0
    }

    if (codesToQuery.length > 0) {
        // Enviar solo los codigos validos filtrados
        // Prevenir error HTTP limit en GET (414 URI Too Long) si son muchisimas:
        if (codesToQuery.length < stationsData.length) {
            params.append('station_code', codesToQuery.join(','));
        }
    } else {
        // Fuerza a mandar algo inencontrable para que de 0 resultados reales de DB si descarta todo via Frontend
        params.append('station_code', 'NO_MATCH_TYPE');
    }

    const agg = document.getElementById('aggregateSelect').value;
    if (agg) params.append('aggregate', agg);

    params.append('format', format);
    // params.append('limit', '0'); // Limit removed to fetch all data without restrictions
    return params.toString();
}

function updateFilterSummary() {
    // 1. Fechas
    const sTime = document.getElementById('startTime').value.replace('T', ' ');
    const eTime = document.getElementById('endTime').value.replace('T', ' ');

    // 2. Agrupación
    const aggValue = document.getElementById('aggregateSelect').value;
    const aggText = document.getElementById('aggregateSelect').options[document.getElementById('aggregateSelect').selectedIndex].text;

    // 3. Variables
    const selVars = Array.from(document.getElementById('variableSelect').selectedOptions).map(o => o.text);
    const varText = selVars.length > 0 ? selVars.join(', ') : 'Ninguna';

    // 4. Ubicación (Estaciones exactas o radios)
    let stationText = '';
    if (selectedStations.size > 0) {
        stationText = `<b>${selectedStations.size}</b> Estaciones Específicas: ` + Array.from(selectedStations).join(', ');
    } else {
        const pLatStr = document.getElementById('pointLat').value;
        const pLngStr = document.getElementById('pointLng').value;
        const rKmStr = document.getElementById('radiusKm').value;

        if (pLatStr && pLngStr && rKmStr) {
            stationText = `Radio de <b>${rKmStr}km</b> desde (${pLatStr}, ${pLngStr}).`;
        } else {
            const rFilters = Array.from(document.getElementById('regionSelect').selectedOptions).map(o => o.text);
            const mFilters = Array.from(document.getElementById('municipioSelect').selectedOptions).map(o => o.text);
            let locText = [];
            if (rFilters.length > 0) locText.push("Región: " + rFilters.join(', '));
            if (mFilters.length > 0) locText.push("Municipio: " + mFilters.join(', '));
            stationText = locText.length > 0 ? locText.join(' | ') : 'Todas las zonas visibles';
        }
    }

    // 5. Tipos de Estación explicitos
    const typeIds = Array.from(document.getElementById('stationTypeSelect').selectedOptions).map(o => o.text);
    const typeStr = typeIds.length > 0 ? typeIds.join(', ') : 'Ninguno';

    // Render HTML in summary box
    const summaryHTML = `
        <div class="mb-1"><i class="fas fa-calendar-check text-muted w-15px"></i> <b>Fechas:</b> ${sTime} &rarr; ${eTime}</div>
        <div class="mb-1"><i class="fas fa-layer-group text-muted w-15px"></i> <b>Agrupación:</b> ${aggText}</div>
        <div class="mb-1"><i class="fas fa-satellite-dish text-muted w-15px"></i> <b>Tipo Estación:</b> ${typeStr}</div>
        <div class="mb-1"><i class="fas fa-satellite text-muted w-15px"></i> <b>Variables:</b> ${varText}</div>
        <div class="mb-0"><i class="fas fa-map-marker-alt text-muted w-15px"></i> <b>Filtro Espacial:</b> ${stationText}</div>
        <hr class="my-2">
        <div class="text-center mt-1 text-primary fw-bold" id="resultCounterText"><i class="fas fa-spinner fa-spin"></i> Consultando...</div>
    `;

    document.getElementById('filterSummaryContent').innerHTML = summaryHTML;
    document.getElementById('filterSummaryContainer').classList.remove('d-none');
}

async function fetchMeasurements() {
    if (abortController) abortController.abort();
    abortController = new AbortController();

    const loader = document.getElementById('loader');
    const tBody = document.getElementById('tableBody');
    const btnSearch = document.getElementById('searchBtn');

    updateFilterSummary();

    tBody.innerHTML = '';
    loader.classList.remove('d-none');
    btnSearch.disabled = true;
    document.getElementById('exportCsvBtn').disabled = true;
    document.getElementById('exportExcelBtn').disabled = true;
    document.getElementById('exportJsonBtn').disabled = true;

    try {
        let swalInstance = Swal.fire({
            title: 'Consultando Datos...',
            html: `
                <div class="my-3 text-primary"><i class="fas fa-circle-notch fa-spin fa-3x"></i></div>
                <p>Esta operación puede tardar unos minutos dependiendo del número de registros seleccionados.</p>
                <div class="alert alert-warning py-2 mb-0" style="font-size: 0.85rem;">
                    <i class="fas fa-info-circle me-1"></i> 
                    <b>Tip:</b> Si la consulta es muy pesada, considera usar la <b>Agrupación de Tiempo</b> en los filtros.
                </div>
            `,
            allowOutsideClick: false,
            showConfirmButton: false,
            showCancelButton: true,
            cancelButtonText: '<i class="fas fa-times-circle me-1"></i> Cancelar Consulta',
            cancelButtonColor: '#dc3545',
        });

        // Escuchar si el usuario hace clic en Cancelar
        swalInstance.then((result) => {
            if (result.dismiss === Swal.DismissReason.cancel) {
                if (abortController) {
                    abortController.abort();
                }
                const counterElement = document.getElementById('resultCounterText');
                if (counterElement) counterElement.innerHTML = `<i class="fas fa-ban text-danger"></i> <span class="text-danger fw-bold">Consulta cancelada.</span>`;
                Toast.fire({ icon: 'info', title: 'Consulta Cancelada' });
            }
        });

        const query = buildQueryParams('json');
        const url = `${API_PROXY}/measurements?${query}`;
        const res = await fetch(url, { signal: abortController.signal });

        if (!res.ok) throw new Error("API status " + res.status);
        const json = await res.json();

        const counterElement = document.getElementById('resultCounterText');
        const dataRows = json.data || [];

        renderTable(dataRows);

        if (dataRows.length > 0) {
            document.getElementById('exportCsvBtn').disabled = false;
            document.getElementById('exportExcelBtn').disabled = false;
            document.getElementById('exportJsonBtn').disabled = false;
            if (counterElement) counterElement.innerHTML = `<i class="fas fa-check-circle text-success"></i> ${dataRows.length} registros listos para exportar.`;
            Toast.fire({ icon: 'success', title: `Cargadas ${dataRows.length} filas.` });
        } else {
            if (counterElement) counterElement.innerHTML = `<i class="fas fa-exclamation-triangle text-danger"></i> <span class="text-danger fw-bold">Sin resultados.</span>`;
            Toast.fire({ icon: 'warning', title: `Búsqueda sin resultados.` });

            // Reemplazar el texto vacío de DataTables con el mensaje rojo personalizado
            const emptyCell = document.querySelector('#resultsTable .dataTables_empty');
            if (emptyCell) {
                emptyCell.innerHTML = '<span class="text-danger fw-bold">No hay datos en la base de datos</span>';
                emptyCell.classList.add('py-4');
            }
        }
    } catch (err) {
        if (err.name === 'AbortError') return;
        tBody.innerHTML = `<tr><td colspan="9" class="py-4 text-danger">Error: ${err.message}</td></tr>`;
        Toast.fire({ icon: 'error', title: 'Error consultando API' });
    } finally {
        Swal.close();
        loader.classList.add('d-none');
        btnSearch.disabled = false;
    }
}

function updateProfiling(data) {
    const total = data.length || 0;

    const processCol = (extractor, isNum) => {
        let valid = 0, error = 0, empty = 0;
        let valuesMap = new Map();

        if (total > 0) {
            data.forEach(row => {
                let val = extractor(row);
                if (val === null || val === undefined || val === '') {
                    empty++;
                } else if (isNum && (isNaN(Number(val)) || val === '-')) {
                    error++;
                } else {
                    valid++;
                    valuesMap.set(val, (valuesMap.get(val) || 0) + 1);
                }
            });
        }

        const distinct = valuesMap.size;
        let unique = 0;
        valuesMap.forEach(count => { if (count === 1) unique++; });

        return {
            validPct: total > 0 ? Math.round((valid / total) * 100) : 0,
            errorPct: total > 0 ? Math.round((error / total) * 100) : 0,
            emptyPct: total > 0 ? Math.round((empty / total) * 100) : 0,
            distinct,
            unique,
            valuesMap
        };
    };

    const cols = [
        { id: 'timestamp', icon: '📅', name: 'Fecha / Tiempo', stats: processCol(d => d.timestamp, false) },
        { id: 'station_code', icon: 'ABC', name: 'Cód. Estación', stats: processCol(d => (d.station_code || '').trim(), false) },
        { id: 'tipo', icon: 'ABC', name: 'Tipo', stats: processCol(d => getStationTypeStr((d.station_code || '').trim()), false) },
        { id: 'latitud', icon: '1.2', name: 'Latitud', stats: processCol(d => { const s = stationsData.find(st => st.station_code === (d.station_code || '').trim()); return (s && s.lat !== null) ? s.lat.toFixed(4) : null; }, true) },
        { id: 'longitud', icon: '1.2', name: 'Longitud', stats: processCol(d => { const s = stationsData.find(st => st.station_code === (d.station_code || '').trim()); return (s && s.lon !== null) ? s.lon.toFixed(4) : null; }, true) },
        { id: 'variable_name', icon: 'ABC', name: 'Variable', stats: processCol(d => d.variable_name, false) },
        { id: 'variable_unit', icon: 'ABC', name: 'Unidad', stats: processCol(d => d.variable_unit, false) },
        { id: 'value', icon: '1.2', name: 'Valor', stats: processCol(d => d.value, true) },
        { id: 'quality', icon: '123', name: 'Calidad', stats: processCol(d => d.quality, false) }
    ];

    const tr = document.getElementById('tableHeaderRow');
    if (!tr) return;
    tr.innerHTML = '';

    cols.forEach((c, i) => {
        let chartHTML = '<div class="pq-dist-chart">';
        const sortedCounts = Array.from(c.stats.valuesMap.values()).sort((a, b) => b - a).slice(0, 20);
        const maxCount = sortedCounts[0] || 1;
        sortedCounts.forEach(count => {
            const h = Math.max(15, Math.round((count / maxCount) * 100));
            chartHTML += `<div class="pq-dist-bar" style="height: ${h}%;"></div>`;
        });
        chartHTML += '</div>';

        const th = document.createElement('th');
        th.innerHTML = `
            <div class="pq-header-title d-flex justify-content-between align-items-center">
                <div><span class="pq-type-icon">${c.icon}</span> ${c.name}</div>
                <button class="btn btn-sm p-0 border-0 text-muted shadow-none" type="button" onclick="event.stopPropagation(); window.togglePqSort(${i})" title="Cambiar orden dinámico">
                    <i class="fas fa-sort px-2" style="font-size: 11px; cursor: pointer;"></i>
                </button>
            </div>
            <div class="pq-bar-container">
                <div class="pq-bar-valid-fill" style="width: ${c.stats.validPct}%;"></div>
                <div class="pq-bar-error-fill" style="width: ${c.stats.errorPct}%;"></div>
                <div class="pq-bar-empty-fill" style="width: ${c.stats.emptyPct}%;"></div>
            </div>
            <div class="pq-stats">
                <div class="pq-stat-row"><span class="pq-dot pq-valid"></span>Válido <span class="float-end">${c.stats.validPct}%</span></div>
                <div class="pq-stat-row"><span class="pq-dot pq-error"></span>Error <span class="float-end">${c.stats.errorPct}%</span></div>
                <div class="pq-stat-row"><span class="pq-dot pq-empty"></span>Vacío <span class="float-end">${c.stats.emptyPct}%</span></div>
            </div>
            ${chartHTML}
            <div class="pq-distinct">Distintos: ${c.stats.distinct}; únicos: ${c.stats.unique}</div>
        `;
        tr.appendChild(th);
    });
}

window.togglePqSort = function (colIndex) {
    if ($.fn.DataTable.isDataTable('#resultsTable')) {
        const table = $('#resultsTable').DataTable();
        const currentOrder = table.order();
        let newDir = 'asc';

        if (currentOrder.length > 0 && currentOrder[0][0] === colIndex) {
            newDir = currentOrder[0][1] === 'asc' ? 'desc' : 'asc';
        }

        table.order([colIndex, newDir]).draw();
    }
};

function renderTable(data) {
    if ($.fn.DataTable.isDataTable('#resultsTable')) {
        $('#resultsTable').DataTable().destroy();
    }
    document.getElementById('tableBody').innerHTML = '';

    // Calculate profiling and update headers HTML before drawing table
    updateProfiling(data);

    // Initialise DataTables
    $('#resultsTable').DataTable({
        data: data,
        deferRender: true,
        ordering: true,
        order: [], // No forzamos un orden inicial para que mantenga el devuelto por la API hasta que el usuario elija
        columns: [
            { data: 'timestamp', render: d => new Date(d).toLocaleString() },
            { data: 'station_code', render: d => (d || '').trim() },
            { data: 'station_code', render: d => getStationTypeStr((d || '').trim()) },
            { data: 'station_code', render: d => { const s = stationsData.find(st => st.station_code === (d || '').trim()); return (s && s.lat !== null) ? s.lat.toFixed(4) : ''; } },
            { data: 'station_code', render: d => { const s = stationsData.find(st => st.station_code === (d || '').trim()); return (s && s.lon !== null) ? s.lon.toFixed(4) : ''; } },
            { data: 'variable_name' },
            { data: 'variable_unit' },
            { data: 'value', render: d => d !== null ? Number(d).toFixed(2) : '' },
            { data: 'quality' }
        ],
        language: {
            url: 'https://cdn.datatables.net/plug-ins/1.13.7/i18n/es-ES.json'
        },
        pageLength: 25,
        responsive: false
    });
}

function exportData(format) {
    const savedName = localStorage.getItem('sama_nombre') || '';
    const savedEmail = localStorage.getItem('sama_email') || '';
    const savedInst = localStorage.getItem('sama_inst') || '';

    Swal.fire({
        title: 'Registro de Descarga',
        html: `
            <div class="mb-3 text-start">
                <label class="form-label small fw-bold">Nombre Completo *</label>
                <input type="text" id="dlgName" class="form-control" placeholder="Tu nombre" value="${savedName}">
            </div>
            <div class="mb-3 text-start">
                <label class="form-label small fw-bold">Correo Electrónico *</label>
                <input type="email" id="dlgEmail" class="form-control" placeholder="nombre@correo.com" value="${savedEmail}">
            </div>
            <div class="mb-3 text-start">
                <label class="form-label small fw-bold">Institución / Entidad *</label>
                <input type="text" id="dlgInst" class="form-control" placeholder="Ej. Universidad, DAGRAN, etc." value="${savedInst}">
            </div>
            <div class="mb-3 text-start">
                <label class="form-label small fw-bold">Propósito de la descarga *</label>
                <textarea id="dlgPurpose" class="form-control" rows="2" placeholder="¿Para qué se usarán estos datos?"></textarea>
            </div>
            <div class="mb-1 text-start">
                <label class="form-label small fw-bold text-primary"><i class="fas fa-folder-open me-1"></i> Ruta y Nombre de Archivo *</label>
                <div class="input-group input-group-sm">
                    <span class="input-group-text bg-light text-muted" title="El Explorador de Archivos se abrirá para confirmar esta ruta" data-bs-toggle="tooltip">/Descargas/</span>
                    <input type="text" id="dlgFilename" class="form-control" placeholder="Ej. reporte_precipitacion" value="SAMA_DATA">
                    <span class="input-group-text bg-primary text-white">.${format === 'excel' ? 'xlsx' : format}</span>
                </div>
                <div class="form-text mt-1" style="font-size: 0.70rem; color: #64748b;">
                    <i class="fas fa-info-circle"></i> Al presionar Descargar, se abrirá la ventana de <b>Guardar Como</b> para elegir la carpeta exacta en su equipo.
                </div>
            </div>
        `,
        confirmButtonText: '<i class="fas fa-download me-2"></i>Descargar',
        showCancelButton: true,
        cancelButtonText: 'Cancelar',
        focusConfirm: false,
        preConfirm: () => {
            const name = document.getElementById('dlgName').value.trim();
            const email = document.getElementById('dlgEmail').value.trim();
            const inst = document.getElementById('dlgInst').value.trim();
            const purpose = document.getElementById('dlgPurpose').value.trim();
            const rawFilename = document.getElementById('dlgFilename').value.trim();

            if (!name || !email || !inst || !purpose || !rawFilename) {
                Swal.showValidationMessage('Por favor completa todos los campos requeridos (*)');
                return false;
            }

            // Almacenar localmente en el navegador los datos fijos del investigador web (UX)
            localStorage.setItem('sama_nombre', name);
            localStorage.setItem('sama_email', email);
            localStorage.setItem('sama_inst', inst);

            // Obtener datos del filtro para el log: Tipos de estacion y areas
            const typeFilters = Array.from(document.getElementById('stationTypeSelect').selectedOptions).map(o => o.value).join(',');
            const selVars = Array.from(document.getElementById('variableSelect').selectedOptions).map(o => o.text).join(', ') || 'Ninguna';
            const sTime = document.getElementById('startTime').value.replace('T', ' ');
            const eTime = document.getElementById('endTime').value.replace('T', ' ');
            const aggOptions = document.getElementById('aggregateSelect').options;
            const aggText = aggOptions[document.getElementById('aggregateSelect').selectedIndex].text;

            let codesStr = "Todas las zonas visibles / Filtro Geográfico";
            if (selectedStations.size > 0) {
                codesStr = Array.from(selectedStations).join(', ');
            }

            const typeNames = Array.from(document.getElementById('stationTypeSelect').selectedOptions).map(o => o.text).join(', ') || 'Ninguno';

            const filterSummary = `Fechas: ${sTime} a ${eTime} | Agrupación: ${aggText} | Variables: ${selVars} | Estaciones: ${typeNames} | Filtro Espacial: ${codesStr}`;

            const ua = navigator.userAgent;
            let os = "Desconocido";
            if (ua.indexOf("Win") !== -1) os = "Windows";
            if (ua.indexOf("Mac") !== -1) os = "MacOS";
            if (ua.indexOf("Linux") !== -1) os = "Linux";
            if (ua.indexOf("Android") !== -1) os = "Android";
            if (ua.indexOf("like Mac") !== -1) os = "iOS";

            let browser = "Desconocido";
            if (ua.indexOf("Firefox") !== -1) browser = "Firefox";
            else if (ua.indexOf("Opera") !== -1 || ua.indexOf("OPR") !== -1) browser = "Opera";
            else if (ua.indexOf("Edg") !== -1) browser = "Edge";
            else if (ua.indexOf("Chrome") !== -1) browser = "Chrome";
            else if (ua.indexOf("Safari") !== -1) browser = "Safari";

            let filename = rawFilename;
            if (format === 'csv' && !filename.endsWith('.csv')) filename += '.csv';
            if (format === 'excel' && !filename.endsWith('.xlsx')) filename += '.xlsx';
            if (format === 'json' && !filename.endsWith('.json')) filename += '.json';

            const counterEl = document.getElementById('resultCounterText');
            const recordCountText = counterEl ? counterEl.innerText.trim() : "Desconocido";

            return {
                name,
                email,
                institution: inst,
                purpose,
                format,
                station_types: typeFilters,
                station_codes: codesStr.length > 100 ? "Multiples selecciones" : codesStr,
                filter_summary: filterSummary,
                file_name: filename,
                record_count: recordCountText,
                os: os,
                browser: browser
            };
        }
    }).then((result) => {
        if (result.isConfirmed) {
            // Enviar Log de Datos Silenciosamente al Backend sin bloquear la descarga
            fetch('/log_download', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(result.value)
            }).catch(console.error);

            // Llamar a la descarga de inmediato para no perder el 'User Gesture'
            executeDownload(format, result.value.file_name);
        }
    });
}

async function executeDownload(format, customFilename = null) {
    const ext = format === 'excel' ? 'xlsx' : format;
    let defaultName = customFilename || ('export_sama.' + ext);
    if (!defaultName.endsWith('.' + ext)) defaultName += '.' + ext;

    let handle = null;
    let useFallback = false;

    // 1. Pedir ubicación de archivo INMEDIATAMENTE antes de cualquier fetch
    if (window.showSaveFilePicker) {
        try {
            const options = {
                suggestedName: defaultName,
                types: [{
                    description: 'Archivo de SAMA DATA (' + ext.toUpperCase() + ')',
                    accept: { '*/*': ['.' + ext] },
                }],
            };
            handle = await window.showSaveFilePicker(options);
        } catch (err) {
            // Si el usuario cancela la ventana de FilePicker, cancelamos todo
            if (err.name === 'AbortError') return;
            // Si falla por otro motivo (ej. permisos), usar Fallback
            useFallback = true;
        }
    } else {
        useFallback = true;
    }

    Toast.fire({ icon: 'info', title: 'Generando archivo...', timer: 5000 });
    const query = buildQueryParams(format);
    const url = `${API_PROXY}/measurements?${query}`;

    try {
        // 2. Traer los datos después de tener el File Handle
        const res = await fetch(url);
        if (!res.ok) throw new Error("Falló el endpoint Export de Go.");
        const blob = await res.blob();
        
        // 3. Escribir los datos
        if (handle && !useFallback) {
            const writable = await handle.createWritable();
            await writable.write(blob);
            await writable.close();
            Toast.fire({ icon: 'success', title: 'Archivo guardado exitosamente.' });
        } else {
            // Fallback clásico
            const downloadUrl = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.style.display = 'none';
            a.href = downloadUrl;
            a.target = '_blank';
            a.download = defaultName;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(downloadUrl);
            a.remove();
            Toast.fire({ icon: 'success', title: 'Descarga iniciada clásicamente.' });
        }
    } catch(err) {
        Swal.fire('Error', err.message, 'error');
    }
}
