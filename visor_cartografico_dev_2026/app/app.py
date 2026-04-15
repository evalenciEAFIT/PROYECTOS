# =============================================================================
# IMPORTACIÓN DE LIBRERÍAS
# =============================================================================
import sys
import os
# Agregar el directorio actual al path del sistema para permitir importaciones relativas
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import dash
from dash import dcc, html, Input, Output, State, callback, ClientsideFunction
import dash_bootstrap_components as dbc
import dash_leaflet as dl

# Importación de librerías de análisis de datos y geoespaciales
try:
    import geopandas as gpd
    import pandas as pd
    import numpy as np
except ImportError as e:
    # Manejo de errores crítico si faltan dependencias fundamentales
    print("\n" + "="*60)
    print("ERROR CRÍTICO: Faltan librerías necesarias.")
    print(f"Detalle: {e}")
    print("Por favor ejecute: pip install -r requirements.txt")
    print("="*60 + "\n")
    sys.exit(1)

from config import custom_style


import json
import glob
import os
from dash_extensions.javascript import Namespace

# =============================================================================
# IMPORTACIÓN DE MÓDULOS INTERNOS
# =============================================================================
# Se importan los módulos de las páginas individuales del aplicativo
import pages.perdida_economica as perdida_economica
import pages.perdida_civil as perdida_civil
import pages.perdida_humana as perdida_humana
import pages.riesgo_global as riesgo_global
import pages.distribucion_espacial as distribucion_espacial
import pages.analisis_model as analisis_model
import pages.escenario_ubicacion as escenario_ubicacion
import pages.escenario_municipio as escenario_municipio
import pages.escenario_manzana as escenario_manzana
# Servicio de acceso a datos centralizado
import data_service


# =============================================================================
# CONFIGURACIÓN GLOBAL Y CONSTANTES
# =============================================================================
from config import BASE_DIR, DATA_DIR, APP_LABELS

# =============================================================================

# CARGA INICIAL DE DATOS (INVENTARIO DE MUNICIPIOS)
# =============================================================================
try:
    print(f"Buscando datos en: {DATA_DIR}") # Debug log

    # Buscar archivos Geopackage de municipios para poblar la lista inicial
    search_pattern = os.path.join(DATA_DIR, 'municipios', '*', 'Municipio*.gpkg')
    municipio_files = glob.glob(search_pattern)
    
    if municipio_files:
        gdfs = []
        for f in municipio_files:
            try:
                # Leer solo la geometría y columnas básicas para optimizar el inicio
                curr_gdf = gpd.read_file(f)
                
                # Usar siempre el nombre extraído del archivo crudo como valor de unión (ID)
                # Esto garantiza que municipios con tildes (como "Nariño") coincidan con sus carpetas ("Narino")
                curr_gdf['municipio'] = os.path.basename(f).replace('Municipio', '').replace('.gpkg', '')
                
                # Asegurar col region y poblacion (datos dummy si no existen para evitar errores)
                if 'region' not in curr_gdf.columns:
                    curr_gdf['region'] = 'Antioquia'
                if 'poblacion' not in curr_gdf.columns:
                    curr_gdf['poblacion'] = 10000 
                
                gdfs.append(curr_gdf)
            except Exception as e:
                print(f"Error cargando {f}: {e}")
                continue
        
        if gdfs:
            # Concatenar todos los municipios en un único GeoDataFrame global
            gdf = pd.concat(gdfs, ignore_index=True)
            # Asegurar SRC (Sistema de Referencia de Coordenadas) a WGS84 para compatibilidad web (Leaflet)
            if gdf.crs != 'EPSG:4326':
                 gdf = gdf.to_crs('EPSG:4326')
            
            # Crear tooltip básico para la vista inicial
            if 'tooltip' not in gdf.columns:
                gdf['tooltip'] = gdf['municipio'].map(lambda m: data_service.get_municipality_display_name(m))
        else:
            raise FileNotFoundError("No se pudieron cargar archivos gpkg correctamente.")
    else:
        raise FileNotFoundError("No se encontraron archivos en data/municipios/")

except Exception as e:
    print(f"Error cargando datos reales: {e}")
    # En caso de error, el aplicativo podría fallar o usar datos dummy (comentados en el original para limpieza)
    from shapely.geometry import Polygon
    import numpy as np

# Función auxiliar para cargar datos dinámicamente

# Crear la aplicación Dash
# =============================================================================
# INICIALIZACIÓN DE LA APP DASH
# =============================================================================
app = dash.Dash(__name__, title='Riesgo Sismico', external_stylesheets=[
    dbc.themes.BOOTSTRAP, # Tema base Bootstrap
    'https://unpkg.com/boxicons@2.1.4/css/boxicons.min.css', # Iconos Boxicons
    'https://unpkg.com/leaflet@1.7.1/dist/leaflet.css', # Estilos Leaflet Maps
    'https://fonts.googleapis.com/css2?family=Poppins:wght@400;500;700&display=swap' # Fuente Poppins
], suppress_callback_exceptions=True, meta_tags=[
    {"name": "viewport", "content": "width=device-width, initial-scale=1"}
])
server = app.server

# =============================================================================
# FUNCIONES DE LAYOUT
# =============================================================================

def get_exposure_map():
    """
    Genera el componente del mapa interactivo usando Dash Leaflet.
    Incluye capas base (satélite, oscuro, claro) y la capa GeoJSON principal.
    """
    return html.Div([
        dl.Map([
            # Controles de Capas (Tile Layers)
            dl.LayersControl([
                dl.BaseLayer(dl.TileLayer(url="https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png"), name="Claro"),
                dl.BaseLayer(dl.TileLayer(url="https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png"), name="Voyager"),
                dl.BaseLayer(dl.TileLayer(url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"), name="Oscuro"),
                dl.BaseLayer(dl.TileLayer(url="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"), name="Satélite", checked=True),
                dl.BaseLayer(dl.TileLayer(url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"), name="Geográfico"),
                dl.BaseLayer(dl.TileLayer(url="https://server.arcgisonline.com/ArcGIS/rest/services/World_Street_Map/MapServer/tile/{z}/{y}/{x}"), name="Callejero"),
                dl.BaseLayer(dl.TileLayer(url="https://{s}.tile.opentopomap.org/{z}/{x}/{y}.png"), name="Topográfico")
            ], position="bottomright"),
            
            # Capa GeoJSON dinámica (se actualiza vía callback)
            dl.GeoJSON(id="geojson-layer", 
                # Namespace permite usar funciones JS para estilos (data-driven styling)
                options=dict(style=Namespace("dash_props", "module")("style_handle"), onEachFeature=Namespace("dash_props", "module")("on_each_feature")), 
                zoomToBounds=True,
                hoverStyle={
                    'weight': 3,
                    'color': '#f5c800', 
                    'dashArray': '',
                    'fillOpacity': 0.7
                }
            )
        ], 
        id="map",
        center=[6.5, -75.5], 
        zoom=8, 
        zoomControl=False,
        className="map-container",
        style={'width': '100%', 'height': '100vh', 'position': 'absolute', 'top': '0', 'left': '0', 'zIndex': '0'}),
        
        # Mapa Legend (Flotante) - Se rellena dinámicamente
        html.Div(id="map-legend", className="map-legend"),

    ], className="map-container")

# Layout principal con soporte de Routing
# =============================================================================
# LAYOUT PRINCIPAL
# =============================================================================
app.layout = html.Div([
    # Control de URL para routing
    dcc.Location(id='url', refresh=False),
    
    # 1. Contenedor del Mapa (Siempre presente en el DOM para preservar estado/callbacks)
    dcc.Loading(
        id="loading-map",
        type="circle",
        color="#0a2240",
        style={'position': 'absolute', 'top': 0, 'left': 0, 'width': '100%', 'height': '100vh', 'zIndex': 0, 'pointerEvents': 'none'},
        children=html.Div(get_exposure_map(), id='map-view-container', style={'display': 'block', 'position': 'absolute', 'top': 0, 'left': 0, 'width': '100%', 'height': '100vh', 'zIndex': 0, 'pointerEvents': 'auto'})
    ),
    
    # 2. Contenedor para Tableros de Análisis (Oculto por defecto, se sobrescribe con el contenido de las páginas)
    dcc.Loading(
        id="loading-dashboard",
        type="circle",
        color="#0a2240",
        style={'position': 'absolute', 'top': 0, 'left': 0, 'width': '100%', 'height': '100vh', 'zIndex': 0, 'pointerEvents': 'none'},
        children=html.Div(id='dashboard-view-container', style={'display': 'none', 'position': 'absolute', 'top': 0, 'left': 0, 'width': '100%', 'height': '100vh', 'zIndex': 0, 'pointerEvents': 'auto', 'overflowY': 'auto'})
    ),
    # UI Overlay
    # UI Overlay
    html.Div([
        # Floating Header Container with Glassmorphism
        html.Div([
            # Left: Toggle + Dropdown
            html.Div([
                html.Button(
                    html.I(className='bx bx-menu'), 
                    id="sidebar-toggle", 
                    className="sidebar-toggle",
                    style={'backgroundColor': 'transparent', 'boxShadow': 'none', 'color': '#0a2240'},
                    title="Alternar menú lateral"
                ),
                html.Div([
                    html.Span("Municipio:", className="text-navy", style={'fontWeight': '600', 'marginRight': '10px', 'fontSize': '0.9rem', 'textTransform': 'uppercase', 'letterSpacing': '0.5px'}),
                    dcc.Dropdown(
                        id="municipality-search",
                        placeholder="SELECCIONAR...",
                        options=sorted([{'label': data_service.get_municipality_display_name(m), 'value': m} for m in gdf['municipio'].unique()], key=lambda x: x['label']),
                        value=None, 
                        className="modern-dropdown",
                        style={'width': '220px', 'border': 'none', 'backgroundColor': 'transparent'},
                        clearable=True
                    )
                ], className="search-container", 
                   style={'display': 'flex', 'alignItems': 'center', 'borderLeft': '1px solid rgba(0,0,0,0.1)', 'paddingLeft': '15px', 'marginLeft': '10px'},
                   title="Buscar y seleccionar un municipio"),

                # Botones de Accesibilidad WCAG 2.1
                html.Div([
                    html.Button("A-", id="wcag-decrease", n_clicks=0, className="btn-wcag", title="Reducir fuente", style={'border': 'none', 'background': 'transparent', 'fontWeight': 'bold', 'fontSize': '14px', 'cursor': 'pointer', 'color': '#0a2240', 'padding': '5px'}),
                    html.Button("A+", id="wcag-increase", n_clicks=0, className="btn-wcag", title="Aumentar fuente", style={'border': 'none', 'background': 'transparent', 'fontWeight': 'bold', 'fontSize': '16px', 'cursor': 'pointer', 'color': '#0a2240', 'padding': '5px'}),
                    html.Button(html.I(className='bx bx-adjust'), id="wcag-contrast", n_clicks=0, className="btn-wcag", title="Alto Contraste", style={'border': 'none', 'background': 'transparent', 'fontSize': '20px', 'cursor': 'pointer', 'color': '#0a2240', 'padding': '5px', 'display': 'flex', 'alignItems': 'center'}),
                    html.Div(id="wcag-dummy-out", style={'display': 'none'})
                ], className="wcag-container", style={'display': 'flex', 'alignItems': 'center', 'gap': '5px', 'borderLeft': '1px solid rgba(0,0,0,0.1)', 'paddingLeft': '15px', 'marginLeft': '10px'}),

                html.A(
                    html.Button("Ayuda", className="btn-dagran-icon", style={
                         'height': '36px', 'marginLeft': '15px', 'padding': '0 15px', 'borderRadius': '18px', 'fontWeight': '600', 'color': '#0a2240'
                    }, title="Manual de Uso"),
                    href="/assets/manual.html", target='_blank', style={'textDecoration': 'none'}
                )
            ], className="float-pill glass-effect", 
               style={
                   'display': 'flex', 'alignItems': 'center', 'padding': '8px 20px', 
                   'backgroundColor': 'rgba(255, 255, 255, 0.85)', 'backdropFilter': 'blur(12px)',
                   'borderRadius': '50px', 'boxShadow': '0 8px 32px rgba(0, 0, 0, 0.1)',
                   'border': '1px solid rgba(255, 255, 255, 0.3)'
               }),

            # Right: Logo only
            html.Div([
                html.Div([
                    html.Img(src="assets/logo.png", style={'height': '110px', 'padding': '5px'}) 
                ], className="float-card glass-effect",
                   style={
                       'backgroundColor': 'white', 'backdropFilter': 'blur(8px)',
                       'borderRadius': '16px', 'padding': '5px 15px', 'boxShadow': '0 4px 20px rgba(0,0,0,0.08)'
                   })
            ], style={'display': 'flex', 'alignItems': 'center'}) 
        ], className="floating-header-container", 
           style={'display': 'flex', 'justifyContent': 'space-between', 'alignItems': 'center', 'padding': '20px 0', 'width': '100%', 'maxWidth': '100%', 'boxSizing': 'border-box', 'pointerEvents': 'none', 'zIndex': '2000'}),

        # Floating Notification (Alert)
        html.Div(
            "Por favor seleccione un municipio de la lista desplegable para ver los detalles.",
            id="selection-alert",
            className="dagran-alert",
            style={
                'position': 'absolute',
                'top': '50%',
                'left': '50%',
                'transform': 'translate(-50%, -50%)',
                'zIndex': '2100',
                'display': 'block' # Default visible since value is None
            }
        ),

        # Sidebar Overlay (Mobile)
        html.Div(id="sidebar-overlay", className="sidebar-overlay"),

        # Sidebar with Options
        html.Div([
            # Close button at the top of the sidebar
            html.I(id='sidebar-close', className='bx bx-x', title="Cerrar panel", 
                   style={'position': 'absolute', 'top': '15px', 'right': '15px', 'fontSize': '1.8rem', 'cursor': 'pointer', 'color': '#0a2240', 'zIndex': '10'}),
            
            # Main Content
            html.Div([
                # Navigation Menu
                # Navigation Menu (Hierarchical)
                html.Nav([
                    # 1. Modelo de Exposición
                    html.Div([
                        html.Div([
                            html.H5("1. Modelo de exposición", className="sidebar-header"),
                            html.Span("Ver más", className="text-gold", id="target-exposicion", style={'cursor': 'pointer', 'fontSize': '0.85rem', 'marginLeft': '8px', 'textDecoration': 'underline'})
                        ], style={'display': 'flex', 'alignItems': 'center', 'marginBottom': '10px', 'marginTop': '20px', 'paddingLeft': '15px'}),
        dbc.Tooltip([
            html.P("El modelo de exposición corresponde al inventario de las edificaciones residenciales de cada municipio. El modelo tiene información a nivel de manzana de la cantidad y las características de las edificaciones residenciales y la respectiva población.", style={'marginBottom': '10px'}),
            html.P("Cada edificación se describe mediante una taxonomía que identifica el conjunto de atributos que definen su comportamiento ante cargas sísmicas. Los atributos son: material y tipo del sistema de resistencia a cargas laterales, nivel de ductilidad y número de pisos.", style={'marginBottom': '10px'}),
            html.P("Los mapas presentan información a nivel de manzana del modelo de exposición diferenciando las edificaciones según macro-taxonomías (definidas por el material y el tipo de sistema de resistencia a cargas laterales) y según el número de pisos.", style={'marginBottom': '0'})
        ], target="target-exposicion", placement="top", className="dagran-tooltip"),
                        dcc.Link([html.I(className='bx bx-map-alt'), " Visor mapa"], href="/", className="menu-item", id="link-map"),
                        
                        # --- CONTROLS MOVED HERE ---
                        html.Div([
                            html.Div([
                                html.Label("Nivel geográfico", className="text-navy", style={'fontWeight': 'bold', 'fontSize': '0.8rem', 'marginTop': '5px', 'display': 'block'}),
                                dcc.Dropdown(
                                    id='layer-selector',
                                    options=[
                                        {'label': 'Municipios', 'value': 'Municipio'},
                                        {'label': 'Cabeceras', 'value': 'Cabecera'},
                                        {'label': 'Manzanas', 'value': 'Manzanas'},
                                        {'label': 'Secciones', 'value': 'Secciones'},
                                        {'label': 'Sectores', 'value': 'Sectores'},
                                    ],
                                    value='Municipio',
                                    style={'marginBottom': '10px', 'fontSize': '0.85rem'},
                                    className='sidebar-dropdown'
                                )
                            ], title="Seleccionar nivel geográfico"),
                            
                            # Selector de Atributo para Colorear (Solo visible en Manzanas)
                            html.Div([
                                html.Label("Seleccionar variable:", className="text-navy", style={'fontWeight': 'bold', 'fontSize': '0.8rem', 'display': 'block'}),
                                dcc.Dropdown(
                                    id='color-selector',
                                    options=[
                                        {'label': 'Valor de Reposición Total', 'value': 'ValorReposicion'},
                                        {'label': 'Número Total de Edificaciones', 'value': 'NumeroEdificios'},
                                        {'label': 'Población Expuesta', 'value': 'Ocupacion'},

                                        # Pisos
                                        {'label': 'Edificaciones de 1 piso', 'value': 'pisos_1'},
                                        {'label': 'Edificaciones de 2 a 3 pisos', 'value': 'pisos_2_3'},
                                        {'label': 'Edificaciones de 4 a 5 pisos', 'value': 'pisos_4_5'},
                                        {'label': 'Edificaciones de 6 a 10 pisos', 'value': 'pisos_6_10'},
                                        {'label': 'Edificaciones de 11 o más pisos', 'value': 'pisos_11_mas'},
                                        
                                        # Taxonomía
                                        {'label': 'BQ_M: muros de bahareque', 'value': 'tax_BQ_M'},
                                        {'label': 'CR_M: muros de concreto reforzado', 'value': 'tax_CR_M'},
                                        {'label': 'CR_PRMM: pórticos resistentes a momento de concreto reforzado con muros adosados', 'value': 'tax_CR_PRMM'},
                                        {'label': 'CR_SC: sistemas combinados de concreto reforzado', 'value': 'tax_CR_SC'},
                                        {'label': 'MC_M: muros de mampostería confinada', 'value': 'tax_MC_M'},
                                        {'label': 'MD_M: muros de madera', 'value': 'tax_MD_M'},
                                        {'label': 'MD_PL: pórticos livianos de madera', 'value': 'tax_MD_PL'},
                                        {'label': 'MNR_M: muros de mampostería no reforzada', 'value': 'tax_MNR_M'},
                                        {'label': 'MR_M: muros de mampostería reforzada', 'value': 'tax_MR_M'},
                                        {'label': 'PR_M: muros prefabricado', 'value': 'tax_PR_M'},
                                        {'label': 'TA_M: muros de tapia', 'value': 'tax_TA_M'},
                                    ],
                                    value='ValorReposicion',
                                    clearable=False,
                                    style={'width': '100%', 'fontSize': '0.85rem'},
                                    className='sidebar-dropdown'
                                )
                            ], id='color-container', style={'display': 'block'}, title="Seleccionar variable para colorear el mapa"),



                        ], style={'marginLeft': '2rem', 'borderLeft': '2px solid #e2e8f0', 'paddingLeft': '1rem', 'paddingRight': '15px', 'marginTop': '5px', 'marginBottom': '15px'}),

                        dcc.Link([html.I(className='bx bx-pie-chart-alt-2'), " Análisis de la exposición"], href="/analisis-modelo", className="menu-item", id="link-am"),

                    ], style={'marginBottom': '15px'}),
                        # ---------------------------
                    
                    # Context Dependent Links (Wrapped in Div for disabling)
                    html.Div([
                        # 2. Evaluación Probabilística
                        html.Div([
                            html.Div([
                                html.H5("2. Evaluación probabilística", className="sidebar-header"),
                                html.Span("Ver más", className="text-gold", id="target-eval-prob", style={'cursor': 'pointer', 'fontSize': '0.85rem', 'marginLeft': '8px', 'textDecoration': 'underline'})
                            ], style={'display': 'flex', 'alignItems': 'center', 'marginBottom': '10px', 'paddingLeft': '15px'}),
                            dbc.Tooltip("La evaluación probabilística considera todos los eventos sísmicos que pueden ocurrir dentro de un periodo de tiempo determinado. Mediante esta evaluación se puede estimar la probabilidad de que ocurran afectaciones, identificando los factores que más contribuyen a las pérdidas y daños, y la frecuencia con la cual pueden ocurrir eventos potencialmente destructivos.", target="target-eval-prob", placement="top", className="dagran-tooltip"),
                            
                            # 2.1 Curvas
                            html.Div([
                                html.Div("2.1. Curvas de excedencia", className="text-navy", style={'fontSize': '0.9rem', 'fontWeight': 'bold'}),
                                html.Span("Ver más", className="text-navy", id="target-curvas", style={'cursor': 'pointer', 'fontSize': '0.85rem', 'marginLeft': '8px', 'textDecoration': 'underline'})
                            ], style={'display': 'flex', 'alignItems': 'center', 'marginBottom': '5px', 'paddingLeft': '15px'}),
                            dbc.Tooltip("Las curvas de excedencia representan el periodo de retorno de las afectaciones económicas, humanas y estructurales en el lugar de análisis. Es decir, las curvas de excedencia indican con qué frecuencia se espera que ocurran diferentes niveles de afectaciones. Las figuras presentan los valores medios.", target="target-curvas", placement="top", className="dagran-tooltip"),
                            dcc.Link([html.I(className='bx bx-line-chart'), " Pérdida económica"], href="/perdida-economica", className="menu-item", id="link-pe", style={'paddingLeft': '25px'}),
                            dcc.Link([html.I(className='bx bx-user'), " Afectaciones humanas"], href="/perdida-humana", className="menu-item", id="link-ph", style={'paddingLeft': '25px'}),
                            dcc.Link([html.I(className='bx bx-building-house'), " Daño completo"], href="/perdida-civil", className="menu-item", id="link-pc", style={'paddingLeft': '25px'}),
                            
                            # 2.2 Afectaciones Municipio
                            html.Div([
                                html.Div("2.2. Afectaciones (municipio)", className="text-navy", style={'fontSize': '0.9rem', 'fontWeight': 'bold'}),
                                html.Span("Ver más", className="text-navy", id="target-afect-mun", style={'cursor': 'pointer', 'fontSize': '0.85rem', 'marginLeft': '8px', 'textDecoration': 'underline'})
                            ], style={'display': 'flex', 'alignItems': 'center', 'marginBottom': '5px', 'marginTop': '10px', 'paddingLeft': '15px'}),
                            dbc.Tooltip("Se presentan una tabla que indican el índice de afectación anual promedio para el municipio.", target="target-afect-mun", placement="top", className="dagran-tooltip"),
                            dcc.Link([html.I(className='bx bx-table'), " Afectaciones anuales promedio a nivel de municipio"], href="/riesgo-global", className="menu-item", id="link-rg", style={'paddingLeft': '25px'}),
                            
                            # 2.3 Afectaciones Manzana
                            html.Div([
                                html.Div("2.3. Afectaciones (manzana)", className="text-navy", style={'fontSize': '0.9rem', 'fontWeight': 'bold'}),
                                html.Span("Ver más", className="text-navy", id="target-afect-man", style={'cursor': 'pointer', 'fontSize': '0.85rem', 'marginLeft': '8px', 'textDecoration': 'underline'})
                            ], style={'display': 'flex', 'alignItems': 'center', 'marginBottom': '5px', 'marginTop': '10px', 'paddingLeft': '15px'}),
                            dbc.Tooltip("Se presentan mapas que indican el índice de afectación anual promedio en cada manzana. Los mapas se presentan tanto para valores absolutos (totales por manzana) y relativos (afectación con respecto al número de edificaciones, población o costo de reposición de la manzana).", target="target-afect-man", placement="top", className="dagran-tooltip"),
                            dcc.Link([html.I(className='bx bx-grid-alt'), " Afectaciones anuales promedio a nivel de manzana"], href="/distribucion-espacial", className="menu-item", id="link-de", style={'paddingLeft': '25px'}),
                        ], style={'marginBottom': '15px'}),

                        # 3. Escenarios (Placeholder)
                        html.Div([
                            html.Div([
                                html.H5("3. Escenarios de riesgo", className="sidebar-header"),
                                html.Span("Ver más", className="text-gold", id="target-escenarios", style={'cursor': 'pointer', 'fontSize': '0.85rem', 'marginLeft': '8px', 'textDecoration': 'underline'})
                            ], style={'display': 'flex', 'alignItems': 'center', 'marginBottom': '10px', 'paddingLeft': '15px'}),
                            dbc.Tooltip("La evaluación determinística o por escenarios considera los efectos en la zona de estudio de sismos individuales con características definidas. En este estudio los escenarios son eventos hipotéticos relevantes para el municipio debido al régimen tectónico y la frecuencia de ocurrencia. Para cada escenario se evalúa el impacto que tendría en las condiciones actuales del municipio", target="target-escenarios", placement="top", className="dagran-tooltip"),
                            # 3.1 Escenario 1
                            html.Div([
                                html.Div("3.1. Escenario 1 (Tr 225)", className="text-navy", style={'fontSize': '0.9rem', 'fontWeight': 'bold'}),
                            ], style={'display': 'flex', 'alignItems': 'center', 'marginBottom': '5px', 'paddingLeft': '15px'}),
                            
                            dcc.Link([html.I(className='bx bx-map-pin'), " Ubicación del escenario"], href="/escenario1-ubicacion", className="menu-item", id="link-e1-loc", style={'paddingLeft': '25px'}),
                            dcc.Link([html.I(className='bx bx-table'), " Afectaciones promedio (municipio)"], href="/escenario1-municipio", className="menu-item", id="link-e1-mun", style={'paddingLeft': '25px'}),
                            dcc.Link([html.I(className='bx bx-grid-alt'), " Afectaciones promedio (manzana)"], href="/escenario1-manzana", className="menu-item", id="link-e1-man", style={'paddingLeft': '25px'}),

                            # 3.2 Escenario 2
                            html.Div([
                                html.Div("3.2. Escenario 2 (Tr 475)", className="text-navy", style={'fontSize': '0.9rem', 'fontWeight': 'bold'}),
                            ], style={'display': 'flex', 'alignItems': 'center', 'marginBottom': '5px', 'marginTop': '15px', 'paddingLeft': '15px'}),
                            
                            dcc.Link([html.I(className='bx bx-map-pin'), " Ubicación del escenario"], href="/escenario2-ubicacion", className="menu-item", id="link-e2-loc", style={'paddingLeft': '25px'}),
                            dcc.Link([html.I(className='bx bx-table'), " Afectaciones promedio (municipio)"], href="/escenario2-municipio", className="menu-item", id="link-e2-mun", style={'paddingLeft': '25px'}),
                            dcc.Link([html.I(className='bx bx-grid-alt'), " Afectaciones promedio (manzana)"], href="/escenario2-manzana", className="menu-item", id="link-e2-man", style={'paddingLeft': '25px'}),
                        ], style={'marginBottom': '15px'}),
                        
                    ], id="restricted-nav-menu", style={'display': 'flex', 'flexDirection': 'column', 'opacity': '0.5', 'pointerEvents': 'none'}),
                    
                    # Link al Manual - Siempre activo
                    dcc.Link([html.I(className='bx bx-book-open'), " Manual de Uso"], href="/assets/manual.html", target='_blank', className="menu-item", style={'marginTop': '5px', 'borderTop': '1px solid #eee', 'paddingTop': '10px', 'color': '#0056b3', 'textDecoration': 'none', 'display': 'flex', 'alignItems': 'center', 'padding': '10px 15px', 'cursor': 'pointer'}),
                ], style={'display': 'flex', 'flexDirection': 'column', 'paddingBottom': '1rem'}),

                html.Hr(style={'border': '0', 'borderTop': '1px solid #eee', 'margin': '0 1.5rem 1rem'}),


                # removed old option block


                html.Div(id='municipio-info', style={
                    'backgroundColor': '#f8f9fa',
                    'padding': '15px',
                    'margin': '1rem',
                    'borderRadius': '5px',
                    'fontSize': '0.9rem'
                })
            ], style={'flexGrow': '1', 'overflowY': 'auto'}),

            # Sidebar Footer (Info)
            html.Div([
                html.I(id='info-icon', className='bx bx-info-circle info-icon', style={'cursor': 'pointer'}, n_clicks=0, title="Ver información de ayuda"),
            ], className="nav-footer")

        ], id="sidebar", className="sidebar glass-panel"),

        # Help Modal
        html.Div([
            html.Div([
                # html.Button("×", id="close-help", ...) Removed as requested
                html.H2("Acerca del visor", style={'color': '#0a2240', 'marginTop': '0', 'textAlign': 'center'}),
                html.Hr(),
                html.H4("Visor Cartográfico de Riesgo Sísmico de Antioquia", style={'marginTop': '20px', 'color': '#0a2240'}),
                html.P("Esta herramienta permite visualizar y analizar los datos de exposición y pérdidas potenciales (económicas, civiles y humanas) ante eventos sísmicos en el departamento. Apoya la toma de decisiones mediante información geográfica detallada y estadísticas interactivas.", style={'lineHeight': '1.6'}),
                
                html.H4("Instrucciones rápidas"),
                html.Ul([
                    html.Li("Seleccione un Municipio para habilitar todas las funciones."),
                    html.Li("Use el menú lateral para navegar entre modelos de pérdida."),
                    html.Li("Haga clic en el mapa para ver detalles de manzanas o barrios."),
                ], style={'lineHeight': '1.6'}),
                
                html.Hr(),
                html.P("Desarrollado por la Universidad EAFIT para la Gobernación de Antioquia / DAGRAN", style={'fontSize': '0.9rem', 'color': '#777', 'textAlign': 'center', 'marginTop': '1rem'}),
                html.Img(src="assets/logo.png", style={'height': '120px', 'display': 'block', 'margin': '10px auto'}),
                
                # Instruction to close
                html.Div([
                    html.Span("Presione la tecla ", style={'color': '#666'}),
                    html.Kbd("ESC", style={'backgroundColor': '#eee', 'borderRadius': '3px', 'border': '1px solid #ccc', 'padding': '2px 5px', 'fontSize': '0.9rem'}),
                    html.Span(" para salir", style={'color': '#666'})
                ], style={'textAlign': 'center', 'marginTop': '20px', 'fontSize': '0.9rem'})

                # Removed "CERRAR" button container
            ], className="modal-content"),
            # Hidden button for ESC key trigger
            html.Button(id="close-help-esc", style={"display": "none"}, n_clicks=0)
        ], id="help-modal", className="modal-overlay"),

        # Mobile screen warning
        html.Div(
            html.Div(
                [
                    html.I(className="bx bx-error", style={'fontSize': '4rem', 'color': '#f5c800', 'marginBottom': '20px', 'display': 'block'}),
                    html.H4("Aviso de visualización", style={'color': '#0a2240', 'marginBottom': '15px', 'fontWeight': 'bold'}),
                    html.P("Esta aplicación presenta limitaciones de visualización en dispositivos de formato pequeño. Para una experiencia óptima, se recomienda utilizar pantallas de 12 pulgadas o superiores.", style={'fontSize': '1.05rem', 'lineHeight': '1.5', 'margin': '0', 'marginBottom': '0px'})
                ],
                className="mobile-warning-card"
            ),
            id="mobile-warning",
            className="mobile-warning-alert"
        ),

        # Footer
        html.Div([
            html.Span("En Desarrollo por la Universidad EAFIT"),
            html.Img(src="assets/Logo_EAFIT.png", className="footer-logo")
        ], className="app-footer")

    ], className="ui-overlay")
])



# =============================================================================
# CALLBACKS: LOGICA INTERACTIVA
# =============================================================================

# --- Dismiss Warning (Removido: Ahora el aviso es permanente en móviles) ---

# --- Accesibilidad WCAG 2.1 ---
app.clientside_callback(
    """
    function(n_contrast, n_inc, n_dec) {
        const ctx = dash_clientside.callback_context;
        if (!ctx.triggered) return window.dash_clientside.no_update;
        
        let prop = ctx.triggered[0].prop_id;
        
        if (prop === 'wcag-contrast.n_clicks') {
            let isHC = document.body.classList.contains('high-contrast-mode');
            if (isHC) {
                document.body.classList.remove('high-contrast-mode');
                localStorage.setItem('wcag-contrast', 'false');
            } else {
                document.body.classList.add('high-contrast-mode');
                localStorage.setItem('wcag-contrast', 'true');
            }
        } else {
            let currentZoom = parseInt(localStorage.getItem('wcag-zoom')) || 100;
            if (prop === 'wcag-increase.n_clicks' && currentZoom < 180) {
                currentZoom += 10;
            } else if (prop === 'wcag-decrease.n_clicks' && currentZoom > 70) {
                currentZoom -= 10;
            }
            document.documentElement.style.fontSize = currentZoom + '%';
            localStorage.setItem('wcag-zoom', currentZoom);
        }
        
        return window.dash_clientside.no_update;
    }
    """,
    Output("wcag-dummy-out", "children"),
    [Input("wcag-contrast", "n_clicks"), Input("wcag-increase", "n_clicks"), Input("wcag-decrease", "n_clicks")],
    prevent_initial_call=True
)


# Callback: Habilitar menú lateral y ocultar alerta cuando se selecciona un municipio
@app.callback(
    [Output('restricted-nav-menu', 'style'),
     Output('selection-alert', 'style'),
     Output('url', 'pathname')],
    [Input('municipality-search', 'value'),
     Input('layer-selector', 'value'),
     Input('color-selector', 'value')]
)
def update_nav_state(municipality, layer_val, color_val):
    ctx = dash.callback_context
    trigger_id = ctx.triggered[0]['prop_id'].split('.')[0] if ctx.triggered else ""
    
    base_nav_style = {'display': 'flex', 'flexDirection': 'column'}
    
    alert_style = {
        'position': 'absolute',
        'top': '50%',
        'left': '50%',
        'transform': 'translate(-50%, -50%)',
        'zIndex': '2100',
    }

    if municipality:
        # Habilitado: quitar opacidad y permitir clicks
        nav_style = {**base_nav_style, 'opacity': '1', 'pointerEvents': 'auto'}
        alert_style['display'] = 'none'
        
        # Redirigir al inicio (Visor Mapa) si el usuario usó Nivel geográfico o Variable
        if trigger_id in ["layer-selector", "color-selector"]:
            return nav_style, alert_style, "/"
            
        return nav_style, alert_style, dash.no_update
    else:
        # Deshabilitado: añadir opacidad y bloquear eventos (reiniciar a ruta raíz)
        nav_style = {**base_nav_style, 'opacity': '0.5', 'pointerEvents': 'none'}
        alert_style['display'] = 'block'
        return nav_style, alert_style, "/"


# Callback: Sincronizar selección del Dropdown al hacer clic en un municipio del mapa
@app.callback(
    Output('municipality-search', 'value'),
    Input('geojson-layer', 'click_feature')
)
def select_municipality_from_map(feature):
    if feature and 'properties' in feature:
        props = feature['properties']
        # Buscar el nombre, puede variar según la fuente ('municipio' o 'MPIO_CNMBR')
        val = props.get('municipio', props.get('MPIO_CNMBR'))
        
        # Verificación de robustez: Normalizar coincidencia con opciones disponibles
        try:
            if val and 'gdf' in globals():
                valid_options = gdf['municipio'].unique()
                # Coincidencia directa
                if val in valid_options:
                    return val
                # Coincidencia insensible a mayúsculas/espacios
                for opt in valid_options:
                     if str(val).strip().upper() == str(opt).strip().upper():
                         return opt
        except Exception as e:
            print(f"Error matching municipality: {e}")
            
        print(f"Map Clicked! Value: {val}") # Debug
        return val
    return dash.no_update


# Callback: Ruteo de Páginas
# Determina qué contenido mostrar (Mapa vs Dashboard) según la URL actual
@app.callback(
    [Output('map-view-container', 'style'),
     Output('dashboard-view-container', 'style'),
     Output('dashboard-view-container', 'children')],
    [Input('url', 'pathname'),
     Input('municipality-search', 'value')]
)
def display_page(pathname, municipality):
    # Estilos comunes de visibilidad
    visible_style = {'display': 'block', 'position': 'absolute', 'top': 0, 'left': 0, 'width': '100%', 'height': '100vh', 'zIndex': 0, 'overflowY': 'auto'}
    hidden_style = {'display': 'none'}
    
    try:
        # Página Principal (Mapa)
        if pathname == '/' or pathname is None:
            return visible_style, hidden_style, dash.no_update
        
        # --- Páginas de Análisis (Requieren llamada a módulos externos) ---
        elif pathname == '/perdida-economica':
            content = perdida_economica.layout(municipality)
            return hidden_style, visible_style, content
            
        elif pathname == '/perdida-civil':
            content = perdida_civil.layout(municipality)
            return hidden_style, visible_style, content
            
        elif pathname == '/perdida-humana':
            content = perdida_humana.layout(municipality)
            return hidden_style, visible_style, content
            
        elif pathname == '/riesgo-global':
            content = riesgo_global.layout(municipality)
            return hidden_style, visible_style, content
            
        elif pathname == '/distribucion-espacial':
            content = distribucion_espacial.layout(municipality)
            return hidden_style, visible_style, content
 
        elif pathname == '/analisis-modelo':
            content = analisis_model.layout(municipality)
            return hidden_style, visible_style, content

        # --- Sub-páginas de Escenarios ---
        elif pathname == '/escenario1-ubicacion':
            content = escenario_ubicacion.layout(municipality, 'R1_TR225')
            return hidden_style, visible_style, content

        elif pathname == '/escenario2-ubicacion':
            content = escenario_ubicacion.layout(municipality, 'R2_TR475')
            return hidden_style, visible_style, content

        elif pathname == '/escenario1-municipio':
            content = escenario_municipio.layout(municipality, 'R1_TR225')
            return hidden_style, visible_style, content

        elif pathname == '/escenario2-municipio':
            content = escenario_municipio.layout(municipality, 'R2_TR475')
            return hidden_style, visible_style, content

        elif pathname == '/escenario1-manzana':
            content = escenario_manzana.layout(municipality, 'R1_TR225')
            return hidden_style, visible_style, content

        elif pathname == '/escenario2-manzana':
            content = escenario_manzana.layout(municipality, 'R2_TR475')
            return hidden_style, visible_style, content
   
        else:
            # Ruta no encontrada por defecto
            return visible_style, hidden_style, dash.no_update
            
    except Exception as e:
        print(f"Error in display_page: {e}")
        # Mostrar interfaz de error amigable
        error_content = html.Div([
            html.H3("Ocurrió un error al cargar la página", style={'color': '#d9534f'}),
            html.P(str(e)),
            html.Button("Volver al Mapa", id='btn-error-back', n_clicks=0, 
                       style={'marginTop': '20px', 'padding': '10px 20px', 'backgroundColor': '#0a2240', 'color': 'white', 'border': 'none', 'borderRadius': '5px', 'cursor': 'pointer'})
        ], style={'padding': '50px', 'textAlign': 'center'})
        return hidden_style, visible_style, error_content

# Callback: Mostrar/Ocultar selector de colores (solo relevante para Manzanas)
@app.callback(
    Output('color-container', 'style'),
    [Input('layer-selector', 'value'),
     Input('municipality-search', 'value')]
)
def toggle_color_dropdown(layer_type, municipality):
    # Si la capa es de detalle (Manzanas, Secciones, etc.), mostrar opción de colorear por variable
    if layer_type in ['Manzanas', 'Secciones', 'Sectores', 'Cabecera', 'Municipio']:
        return {'display': 'block'}
    return {'display': 'none'}

# Callback: Gestión inteligente de selección de capa
@app.callback(
    Output('layer-selector', 'value'),
    [Input('layer-selector', 'value'),
     Input('municipality-search', 'value')]
)
def manage_layer_selection(layer_val, muni_val):
    ctx = dash.callback_context
    if not ctx.triggered:
        return dash.no_update
        
    trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]
    
    # 1. Prevenir selección vacía
    if trigger_id == 'layer-selector':
        if layer_val is None:
            return 'Municipio'
        return dash.no_update
        
    # 2. Auto-cambiar a Manzanas cuando se selecciona un municipio específico
    # Esto mejora la UX al mostrar el detalle inmediatamente
    if trigger_id == 'municipality-search':
        if muni_val and (layer_val == 'Municipio' or layer_val is None):
            return 'Manzanas'
            
    return dash.no_update

# Callback PRINCIPAL: Actualización del GeoJSON del Mapa
@app.callback(
    [Output('geojson-layer', 'data'),
     Output('map-legend', 'children')],
    [Input('layer-selector', 'value'),
     Input('municipality-search', 'value'),
     Input('color-selector', 'value')]
)
def update_map(layer_type, municipality_search, color_by):
    try:
        # Default fallback if cleared
        if not layer_type:
            layer_type = 'Manzanas'

        legend_content = html.Div() # Empty by default
        # 1. Determinar datos base
        # Si es 'Municipio' y no hay filtro de municipio especifico, usar cache global para velocidad
        # OJO: Si no hay municipio seleccionado, NO permitir cargar Manzanas/etc para todo el departamento (causa OOM)
        if not municipality_search:
            # User request: Do NOT show municipalities on map to prevent selection errors.
            # Force selection via dropdown.
            empty_geojson = {"type": "FeatureCollection", "features": []}
            return empty_geojson, html.Div()
        else:
            # Cargar dinamicamente (esto soporta Manzanas, Cabeceras, etc.)
            # Si hay busqueda de municipio, filtramos la carga
            # UPDATED: Use NEW get_map_data from data_service
            target_gdf = data_service.get_map_data(municipality_search, layer_type)
        
        # 2. Calcular Colores si corresponde (Manzanas, etc.)
        dynamic_colors = []
        dynamic_labels = []
        
        supported_layers = ['Manzanas', 'Secciones', 'Sectores', 'Cabecera', 'Municipio']
        
        # Validar que si no hay color_by o no está en columnas, se use un default
        if target_gdf.empty:
             return dash.no_update, dash.no_update
             
        # Default styling for all rows
        if 'fillColor' not in target_gdf.columns:
            target_gdf['fillColor'] = '#000000'
        if 'fillOpacity' not in target_gdf.columns:
             target_gdf['fillOpacity'] = 0.5
             
        if layer_type in supported_layers and color_by in target_gdf.columns:
            # Fallback color (just in case)
            target_gdf['fillColor'] = '#000000'
            
            # Validar si es numérico
            if np.issubdtype(target_gdf[color_by].dtype, np.number):
                # Reduced to 6 distinct levels for granularity
                # Sequential YlOrRd scale (Yellow -> Orange -> Red)
                colors_pool = ['#ffffb2', '#fed976', '#feb24c', '#fd8d3c', '#f03b20', '#bd0026']
                
                # Init empty
                target_gdf['fillColor'] = '#000000' # No data = Black
                target_gdf['fillOpacity'] = 0.5     # Standard opacity
                
                # Select only POSITIVE values for the scale
                mask_positive = target_gdf[color_by] > 0
                vals_positive = target_gdf.loc[mask_positive, color_by]
                
                if not vals_positive.empty:
                    try:
                        # Use qcut on POSITIVE values only
                        cat_series, bins = pd.qcut(vals_positive, len(colors_pool), retbins=True, duplicates='drop')
                        
                        # Handle edge case: single unique value or all duplicates
                        if len(bins) < 2:
                             # Assign the first color to all positive values
                             target_gdf.loc[mask_positive, 'fillColor'] = colors_pool[0]
                             # Labels? "Value"
                             if not vals_positive.empty:
                                 val = vals_positive.iloc[0]
                                 if color_by == 'ValorReposicion':
                                     if val > 1000000: lbl = f"${val/1000000:,.1f}M"
                                     else: lbl = f"${val:,.0f}"
                                 else:
                                     lbl = f"{float(val):,.0f}"
                                 dynamic_labels = [lbl]
                                 dynamic_colors = [colors_pool[0]]
                        else:
                            # Map codes to colors for positive values
                            # Note: bins might be fewer than colors_pool if duplicates were dropped
                            dynamic_colors = colors_pool[:len(bins)-1] # Adjust pool to actual bins
                            
                            # Generate Labels based on bins
                            dynamic_labels = []
                            for i in range(len(bins)-1):
                                lower = bins[i]
                                upper = bins[i+1]
                                
                                # Formatting
                                if color_by == 'ValorReposicion':
                                     if upper > 1000000:
                                         lbl = f"${lower/1000000:,.1f}M - ${upper/1000000:,.1f}M"
                                     else:
                                         lbl = f"${lower:,.0f} - ${upper:,.0f}"
                                else:
                                     lbl = f"{float(lower):,.0f} - {float(upper):,.0f}"
                                
                                dynamic_labels.append(lbl)
                                
                            # Create mapping serie
                            code_to_color = {i: col for i, col in enumerate(dynamic_colors)}
                            
                            # Store color in original dataframe only for positive rows
                            colors_mapped = cat_series.cat.codes.map(code_to_color)
                            target_gdf.loc[mask_positive, 'fillColor'] = colors_mapped
    
                    except Exception as e:
                        print(f"Coloring Error with qcut: {e}")
                        # Keep default black if error
                else:
                     # No positive values
                     pass
    
                # Final check to ensure no NaNs in fillColor (caused by mapping errors)
                target_gdf['fillColor'] = target_gdf['fillColor'].fillna('#000000')
                # Final check to ensure no NaNs in fillColor (caused by mapping errors)
                target_gdf['fillColor'] = target_gdf['fillColor'].fillna('#000000')
    
        # --- TOOLTIP GENERATION LOGIC ---
        if 'tooltip' not in target_gdf.columns:
             # Helper to format distribution from row keys
            def create_tooltip(row):
                 try:
                     # 1. Header (Municipality & ID)
                     tooltip_header = f"<b>Municipio:</b> {data_service.get_municipality_display_name(municipality_search)}<br>"
                     
                     # Only show specific ID for Manzanas
                     if layer_type == 'Manzanas' and 'manz_ccnct' in row:
                         tooltip_header += f"<b>Manzana:</b> {row['manz_ccnct']}<br>"
                     
                     # 2. Main Value (Colored Variable)
                     val_str = ""
                     if color_by in row and pd.notna(row[color_by]):
                          val = row[color_by]
                          formatted_val = f"{val:,.2f}"
                          # Custom formats
                          if color_by == 'ValorReposicion': formatted_val = f"${val:,.0f}"
                          elif color_by in ['NumeroEdificios', 'Ocupacion', 'Ocupantes']: formatted_val = f"{val:,.0f}"
                          
                          # Use descriptive title from APP_LABELS if available
                          title_label = APP_LABELS.get(color_by, color_by)
                          val_str = f"<b>{title_label}:</b> {formatted_val}<br>"
                     
                     # 3. Aggregated Summaries (For non-Manzanas mainly, but useful context)
                     summary_str = ""
                     if layer_type != 'Manzanas':
                         summary_str += "<br><b>Totales Acumulados:</b><br>"
                         if 'NumeroEdificios' in row: summary_str += f"Edificios: {row['NumeroEdificios']:,.0f}<br>"
                         if 'Ocupacion' in row: summary_str += f"Ocupantes: {row['Ocupacion']:,.0f}<br>"
                         if 'ValorReposicion' in row: summary_str += f"Valor Rep.: ${row['ValorReposicion']:,.0f}<br>"
                         if 'NumeroDeManzanas' in row: summary_str += f"Manzanas: {row['NumeroDeManzanas']:.0f}<br>"

                     # 4. Distributions (Manzanas only usually)
                     dist_str = ""
                     
                     # Pisos
                     p_cols = [c for c in row.index if str(c).startswith('pct_pisos_')]
                     if p_cols:
                         p_vals = {c.replace('pct_pisos_', ''): row[c] for c in p_cols if pd.notna(row[c]) and row[c] > 0}
                         if p_vals:
                             sorted_p = sorted(p_vals.items(), key=lambda x: x[1], reverse=True)
                             top_p = sorted_p[:3]
                             pisos_items = [f"{k.replace('_', '-')}: {v:.1f}%" for k, v in top_p]
                             if len(sorted_p) > 3: pisos_items.append("...")
                             dist_str += f"<hr style='margin:5px 0'><b>Pisos:</b><br>{'<br>'.join(pisos_items)}<br>"

                     # Taxonomía
                     t_cols = [c for c in row.index if str(c).startswith('pct_tax_')]
                     if t_cols:
                         t_vals = {c.replace('pct_tax_', ''): row[c] for c in t_cols if pd.notna(row[c]) and row[c] > 0}
                         if t_vals:
                             sorted_t = sorted(t_vals.items(), key=lambda x: x[1], reverse=True)
                             top_t = sorted_t[:3]
                             # Use Global APP_LABELS
                             tax_items = [f"{APP_LABELS.get(k, k)}: {v:.1f}%" for k, v in top_t]
                             if len(sorted_t) > 3: tax_items.append("...")
                             dist_str += f"<br><b>Taxonomía:</b><br>{'<br>'.join(tax_items)}"
                     
                     return (
                        f"{tooltip_header}"
                        f"{val_str}"
                        f"{summary_str}"
                        f"{dist_str}"
                     )
                 except Exception as e:
                     return f"<b>Error:</b> {str(e)}"

            # Apply
            # Only apply if dataframe is not empty
            if not target_gdf.empty:
                target_gdf['tooltip'] = target_gdf.apply(create_tooltip, axis=1)

        # 3. Convertir a GeoJSON
        # Clean NaNs in tooltip before conversion to avoid JSON errors
        if 'tooltip' in target_gdf.columns:
             target_gdf['tooltip'] = target_gdf['tooltip'].fillna('Sin información')
             
        geojson_data = json.loads(target_gdf.to_json())
        
        # Inject styles
        # Inject styles
        for feat in geojson_data['features']:
            props = feat['properties']
            fill_color = props.get('fillColor', '#000000') # default black
            
            # Default Opacity
            fill_opacity = props.get('fillOpacity', 0.5)
            
            # Apply style
            feat['properties']['style'] = {
                'color': 'white',
                'weight': 1,
                'opacity': 1,
                'fillColor': fill_color,
                'fillOpacity': fill_opacity
            }
        
        # Create Legend if Manzanas and we have dynamic data
        if layer_type in supported_layers and dynamic_colors:
            items = []
            
            for c, l in zip(dynamic_colors, dynamic_labels):
                 items.append(html.Div([
                     html.Span(style={'backgroundColor': c, 'width': '15px', 'height': '15px', 'display': 'inline-block', 'marginRight': '5px', 'borderRadius': '3px'}),
                     html.Span(l, style={'fontSize': '0.8rem'})
                 ], style={'display': 'flex', 'alignItems': 'center', 'marginBottom': '2px'}))
            
            # Add "Sin Datos" explicit item
            items.append(html.Div([
                 html.Span(style={'backgroundColor': '#000000', 'width': '15px', 'height': '15px', 'display': 'inline-block', 'marginRight': '5px', 'borderRadius': '3px', 'border': '1px solid #ccc'}),
                 html.Span("Sin datos", style={'fontSize': '0.8rem'})
            ], style={'display': 'flex', 'alignItems': 'center', 'marginBottom': '2px', 'marginTop': '5px'}))
                 
            legend_title = APP_LABELS.get(color_by, color_by)
                  
            legend_content = html.Div([
                html.H5(legend_title, style={'fontSize': '0.9rem', 'fontWeight': 'bold', 'marginBottom': '5px'}),
                html.Div(items)
            ], style={'backgroundColor': 'white', 'padding': '10px', 'borderRadius': '5px', 'boxShadow': '0 2px 5px rgba(0,0,0,0.2)', 'position': 'absolute', 'bottom': '30px', 'right': '10px', 'zIndex': '1000'})
    
        return geojson_data, legend_content

    except Exception as e:
        print(f"Error CRITICAL in update_map: {e}")
        return dash.no_update, dash.no_update


# Callback: Mostrar Información Detallada al hacer click en Mapa
# Actualiza el panel lateral con la información de la feature seleccionada
@app.callback(
    Output('municipio-info', 'children'),
    Input('geojson-layer', 'click_feature')
)
def display_click_info(feature):
    try:
        info_text = ""
        
        if feature:
            props = feature.get('properties', {})
            
            # Extraer propiedades comunes
            nombre = props.get('municipio', 'N/A')
            if nombre == 'N/A': nombre = props.get('MPIO_CNMBR', 'Desconocido')
            
            region_nombre = props.get('region', 'N/A')
            poblacion = props.get('poblacion', 'N/A')
            
            info_children = [html.H4(f"{nombre}")]
            
            if region_nombre != 'N/A':
                info_children.append(html.P(f"Región: {region_nombre}"))
            
            # --- Tooltip Rico para Manzanas (Datos agregados) ---
            if 'ValorReposicion' in props:
                 mid = props.get('manz_ccnct', props.get('CodigoManzana2024', 'N/A'))
                 info_children.append(html.P(f"ID: {mid}", style={'fontSize': '0.8rem', 'color': '#777'}))
                 html.Hr()
                 
                 # Valor Reposicion
                 val_repo = str(props.get('ValorReposicion', 0))
                 if isinstance(props.get('ValorReposicion'), (int, float)):
                     val_repo = f"$ {float(props['ValorReposicion']):,.0f}"

                 info_children.append(html.P([html.B("Valor Reposición: "), val_repo]))
                 
                 # Edificios
                 edif = props.get('NumeroEdificios', 'N/A')
                 info_children.append(html.P([html.B("Número Edificios: "), str(edif)]))
                 
                 # Ocupacion
                 ocup = props.get('Ocupacion', 'N/A')
                 info_children.append(html.P([html.B("Ocupación: "), str(ocup)]))
            
            elif poblacion != 'N/A':
                 # Fallback población simple
                try:
                    val = f"{int(poblacion):,}"
                except:
                    val = str(poblacion)
                info_children.append(html.P(f"Población: {val}"))
                
            # Añadir más propiedades si es Manzana/Seccion
            codigo = props.get('CODIGO', props.get('id', None))
            if codigo:
                 info_children.append(html.P(f"Código: {codigo}"))

            # --- MENÚ DE NAVEGACIÓN MUNICIPAL ---
            # Acceso directo a los tableros analíticos desde el detalle
            if nombre != 'N/A':
                info_children.append(html.Hr(style={'margin': '10px 0'}))
                info_children.append(html.H5("Ir a tableros:", style={'color': '#0a2240', 'marginTop': '10px'}))
                
                # Estilo botones
                btn_style = {
                    'display': 'block', 'width': '100%', 'padding': '8px', 'marginBottom': '5px',
                    'backgroundColor': 'white', 'border': '1px solid #ddd', 'borderRadius': '5px',
                    'textAlign': 'left', 'color': '#0056b3', 'textDecoration': 'none',
                    'fontWeight': '500', 'fontSize': '0.9rem', 'cursor': 'pointer',
                    'transition': 'all 0.2s'
                }
                
                info_children.append(html.Div([
                    dcc.Link(html.Div([html.I(className='bx bx-globe'), " Riesgo Global"], style={'display': 'flex', 'gap': '10px', 'alignItems': 'center'}), href="/riesgo-global", style=btn_style),
                    dcc.Link(html.Div([html.I(className='bx bx-line-chart'), " Pérdida Económica"], style={'display': 'flex', 'gap': '10px', 'alignItems': 'center'}), href="/perdida-economica", style=btn_style),
                    dcc.Link(html.Div([html.I(className='bx bx-user'), " Pérdida Humana"], style={'display': 'flex', 'gap': '10px', 'alignItems': 'center'}), href="/perdida-humana", style=btn_style),
                    dcc.Link(html.Div([html.I(className='bx bx-building-house'), " Pérdida Civil"], style={'display': 'flex', 'gap': '10px', 'alignItems': 'center'}), href="/perdida-civil", style=btn_style),
                    dcc.Link(html.Div([html.I(className='bx bx-map-alt'), " Distribución Espacial"], style={'display': 'flex', 'gap': '10px', 'alignItems': 'center'}), href="/distribucion-espacial", style=btn_style),
                ]))

            info_text = html.Div(info_children)
        
        return info_text
    except Exception as e:
        print(f"Error in display_click_info: {e}")
        return html.Div("Error al mostrar información.")

# Callback: Control de Apertura/Cierre del Menú Lateral (Sidebar)
@app.callback(
    [Output("sidebar", "className"),
     Output("sidebar-overlay", "className")],
    [Input("sidebar-toggle", "n_clicks"),
     Input("sidebar-close", "n_clicks"),
     Input("sidebar-overlay", "n_clicks"),
     Input("municipality-search", "value"),
     Input("layer-selector", "value"),
     Input("color-selector", "value")],
    [State("sidebar", "className")]
)
def toggle_sidebar(n_toggle, n_close, n_overlay, municipality, layer_val, color_val, sidebar_class):
    ctx = dash.callback_context
    overlay_class = "sidebar-overlay"
    
    if not ctx.triggered:
        return sidebar_class, overlay_class

    trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]
    
    def toggle_cls(cls_str, target):
        if target in cls_str:
            return cls_str.replace(" " + target, "")
        else:
            return cls_str + " " + target

    if trigger_id == "sidebar-toggle" or trigger_id == "sidebar-close":
        # Toggle (o cierre explícito) para escritorio y movil
        if trigger_id == "sidebar-close":
            if "collapsed" not in sidebar_class:
                sidebar_class += " collapsed"
            if "mobile-open" in sidebar_class:
                sidebar_class = sidebar_class.replace(" mobile-open", "")
        else:
            sidebar_class = toggle_cls(sidebar_class, "collapsed")
            sidebar_class = toggle_cls(sidebar_class, "mobile-open")
        
        if "mobile-open" in sidebar_class:
             overlay_class += " active"
             
        return sidebar_class, overlay_class
            
    elif trigger_id in ["sidebar-overlay", "municipality-search"]:
        # Auto-cierre al hacer click fuera en mobile
        if trigger_id == "sidebar-overlay" and "mobile-open" in sidebar_class:
            sidebar_class = sidebar_class.replace(" mobile-open", "")
            
        # Comportamiento Escritorio: 
        elif trigger_id == "municipality-search":
             # Abrir automáticamente al seleccionar municipio para ver opciones
             if municipality:
                  sidebar_class = sidebar_class.replace(" collapsed", "")
        
        return sidebar_class, overlay_class
            
    return sidebar_class, overlay_class

# Callback: Modal de Ayuda
@app.callback(
    Output("help-modal", "style"),
    [Input("info-icon", "n_clicks"),
     Input("close-help-esc", "n_clicks")],
    [State("help-modal", "style")]
)
def toggle_help(n_open, n_esc, current_style):
    ctx = dash.callback_context
    if not ctx.triggered:
        return {'display': 'none'}
    
    button_id = ctx.triggered[0]['prop_id'].split('.')[0]
    
    if button_id == "info-icon":
        return {'display': 'flex'}
    elif button_id == "close-help-esc":
        return {'display': 'none'}
    
    return {'display': 'none'}




import argparse

# Register callbacks for modules that need them
analisis_model.register_callbacks(app)

@app.callback(
    Output("map-tooltip", "children"),
    [Input("geojson-layer", "hover_feature")]
)
def update_map_tooltip(feature):
    import traceback
    try:
        if not feature or 'properties' not in feature:
            return None
        
        props = feature['properties']
        
        # Helper for modern horizontal bars with teal gradient
        def create_bar_row(label, val, total, idx=0, total_items=1):
            pct = (val / total * 100) if total > 0 else 0
            # Teal gradient based on position
            ratio = idx / max(total_items - 1, 1) if total_items > 1 else 0
            r = int(13 + (16 - 13) * ratio)
            g = int(148 + (185 - 148) * ratio)
            b = int(136 + (129 - 136) * ratio)
            bar_color = f'rgb({r},{g},{b})'
            
            return html.Div([
                html.Div([
                    html.Span(f"{label}", style={'fontSize': '11px', 'fontWeight': '600', 'color': '#1e293b'}),
                    html.Span(f"{int(val):,}", style={'fontSize': '11px', 'color': '#64748b', 'fontWeight': '500'})
                ], style={'display': 'flex', 'justifyContent': 'space-between', 'marginBottom': '3px'}),
                html.Div([
                    html.Div(style={
                        'width': f'{min(pct, 100)}%', 
                        'height': '5px', 
                        'backgroundColor': bar_color, 
                        'borderRadius': '3px',
                        'transition': 'width 0.3s ease'
                    })
                ], style={'width': '100%', 'backgroundColor': '#e2e8f0', 'height': '5px', 'borderRadius': '3px', 'marginBottom': '6px'})
            ])

        # 1. Process Floor Data
        floor_map = {
            'pisos_1': APP_LABELS['pisos_1'], 
            'pisos_2_3': APP_LABELS['pisos_2_3'], 
            'pisos_4_5': APP_LABELS['pisos_4_5'], 
            'pisos_6_10': APP_LABELS['pisos_6_10'], 
            'pisos_11_mas': APP_LABELS['pisos_11_mas']
        }
        floor_data = [(v, props.get(k, 0)) for k, v in floor_map.items()]
        total_floors = sum(val for _, val in floor_data)
        floor_rows = [create_bar_row(lbl, val, total_floors, i, len(floor_data)) for i, (lbl, val) in enumerate(floor_data) if val > 0]

        # 2. Process Taxonomy Data (Top 5)
        tax_data = {}
        for k, v in props.items():
            if k.startswith('tax_') and not k.startswith('pct_tax_') and isinstance(v, (int, float)) and v > 0:
                 raw_code = k.replace('tax_', '')
                 # Use global APP_LABELS or fallback to raw
                 lbl = APP_LABELS.get(raw_code, raw_code) 
                 tax_data[lbl] = v
        
        sorted_tax = sorted(tax_data.items(), key=lambda x: x[1], reverse=True)[:5]
        total_tax = sum(tax_data.values())
        tax_rows = [create_bar_row(k, v, total_tax, i, len(sorted_tax)) for i, (k, v) in enumerate(sorted_tax)]

        return html.Div([
            # Header with gradient
            html.Div([
                html.Div([
                    html.I(className="bx bx-map-pin", style={'fontSize': '1.2rem', 'marginRight': '8px', 'color': '#10b981'}),
                    html.Span(f"Mz {props.get('manz_ccnct', 'N/A')}", style={'fontSize': '14px', 'fontWeight': '700', 'color': 'white'})
                ], style={'display': 'flex', 'alignItems': 'center', 'marginBottom': '6px'}),
                html.Div([
                    html.Span(f"${props.get('ValorReposicion', 0):,.0f}", style={'fontSize': '16px', 'fontWeight': 'bold', 'color': '#10b981'})
                ], style={'marginBottom': '4px'}),
                html.Div([
                    html.Span(f"🏢 {props.get('NumeroEdificios', 0):,}", style={'marginRight': '12px', 'fontSize': '11px'}),
                    html.Span(f"👥 {props.get('Ocupacion', 0):,}", style={'fontSize': '11px'})
                ], style={'color': 'rgba(255,255,255,0.75)'})
            ], style={
                'background': 'linear-gradient(135deg, #0f172a 0%, #1e293b 100%)',
                'padding': '14px 16px', 
                'borderRadius': '12px 12px 0 0'
            }),
            
            # Content Body
            html.Div([
                # Floors Section
                html.Div([
                    html.Div([
                        html.Span("PISOS", style={'fontSize': '9px', 'fontWeight': '700', 'letterSpacing': '1px', 'color': '#64748b'}),
                        html.Span(f"{total_floors:,} edificios", style={'fontSize': '9px', 'color': '#94a3b8'})
                    ], style={'display': 'flex', 'justifyContent': 'space-between', 'marginBottom': '8px', 'paddingBottom': '4px', 'borderBottom': '1px solid #e2e8f0'}),
                    html.Div(floor_rows if floor_rows else html.I("Sin datos", style={'fontSize': '10px', 'color': '#94a3b8'}))
                ], style={'marginBottom': '12px'}),
                
                # Taxonomy Section
                html.Div([
                    html.Div([
                        html.Span("TAXONOMÍA", style={'fontSize': '9px', 'fontWeight': '700', 'letterSpacing': '1px', 'color': '#64748b'}),
                        html.Span("Top 5", style={'fontSize': '9px', 'color': '#94a3b8'})
                    ], style={'display': 'flex', 'justifyContent': 'space-between', 'marginBottom': '8px', 'paddingBottom': '4px', 'borderBottom': '1px solid #e2e8f0'}),
                    html.Div(tax_rows if tax_rows else html.I("Sin datos", style={'fontSize': '10px', 'color': '#94a3b8'}))
                ])
            ], style={'padding': '12px 16px 16px 16px', 'backgroundColor': 'white'})
        ], style={
            'width': '280px', 
            'backgroundColor': 'white', 
            'borderRadius': '12px', 
            'boxShadow': '0 10px 40px -5px rgba(0,0,0,0.25)',
            'fontFamily': "'Poppins', sans-serif",
            'zIndex': 1000,
            'overflow': 'hidden',
            'border': '1px solid rgba(0,0,0,0.06)'
        })
    except Exception:
        traceback.print_exc()
        return html.Div([
            html.I(className="bx bx-error-circle", style={'fontSize': '1.5rem', 'color': '#ef4444', 'marginBottom': '6px'}),
            html.Div("Error cargando datos", style={'color': '#ef4444', 'fontSize': '11px', 'fontWeight': '600'}),
            html.Div("Verifique la consola", style={'fontSize': '10px', 'color': '#94a3b8'})
        ], style={
            'width': '180px', 'padding': '16px', 'backgroundColor': '#fff', 
            'border': '1px solid #fecaca', 'borderRadius': '10px', 'textAlign': 'center',
            'boxShadow': '0 4px 12px rgba(0,0,0,0.1)'
        })

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Run the Dash app.')
    parser.add_argument('port_arg', nargs='?', type=int, help='Port to run the app on (positional, e.g. 8050)')
    parser.add_argument('--port', type=int, default=8050, help='Port to run the app on (flag, e.g. --port 8050)')
    args = parser.parse_args()
    
    # Use positional arg if provided, otherwise flag default
    port = args.port_arg if args.port_arg is not None else args.port
    
    app.run(debug=True, port=port, host='0.0.0.0')