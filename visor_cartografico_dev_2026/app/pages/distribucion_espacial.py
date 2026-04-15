import data_service

import glob
import os
import pandas as pd
import geopandas as gpd
import dash_leaflet as dl
from dash import html, dcc, callback, Input, Output
import dash
import json
import numpy as np
import plotly.colors as pc
import plotly.express as px # Used for getting color scales

# Helper to load data
def load_data(municipality):
    """
    Carga y procesa los datos anuales promedio a nivel de manzana de un municipio, combinando Excel de pérdidas con geometrías de las manzanas.
    """
    try:
        BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        DATA_DIR = os.path.join(BASE_DIR, 'data')
        mun_dir = os.path.join(DATA_DIR, 'municipios', municipality)
        
        # 1. Load Excel Data
        pattern = os.path.join(mun_dir, f"ResumenTOTAL*{municipality}.xlsx")
        files = glob.glob(pattern)
        if not files:
            files = glob.glob(os.path.join(mun_dir, "ResumenTOTAL*.xlsx"))
            
        df = None
        if files:
            df = pd.read_excel(files[0], sheet_name='perdidasprom')
            # Clean Code: Remove leading 'C'
            df['manz_ccnct'] = df['CodigoManzana2024'].astype(str).str.replace('C', '', 1)
            
            # Explicitly identify relevant columns for aggregation to ensure they are numeric
            metrics_cols = [
                'Perdida_Tot', 'PerdidaRel_Tot',
                'Fallecidos_Tot', 'FallecidosRel_Tot',
                'Heridos_Tot', 'HeridosRel_Tot',
                'Desplazados_Tot', 'DesplazadosRel_Tot',
                'DanoCompleto_Tot', 'DanoCompletoRel_Tot'
            ]
            
            # Ensure these columns exist and are numeric
            available_metrics = [c for c in metrics_cols if c in df.columns]
            
            for col in available_metrics:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
                
            # --- New Aggregation Logic for Pisos and Taxonomy ---
            # Distributions (Weighted by NumEdificios)
            def get_distribution(df_data, group_col):
                """Calcula la distribución porcentual ponderada por el número de edificaciones para una variable específica a nivel de manzana."""
                if group_col not in df_data.columns or 'NumEdificios' not in df_data.columns:
                    return pd.DataFrame(columns=['manz_ccnct', f'{group_col}_dist'])
                grouped = df_data.groupby(['manz_ccnct', group_col])['NumEdificios'].sum().reset_index()
                totals = grouped.groupby('manz_ccnct')['NumEdificios'].transform('sum')
                grouped['pct'] = np.where(totals > 0, (grouped['NumEdificios'] / totals) * 100, 0)
                def format_group(group):
                    """Da formato a los principales grupos de porcentaje en texto HTML para inyectarlos en tooltips informativos."""
                    group = group.sort_values('pct', ascending=False)
                    top = group.head(3)
                    formatted = [f"{row[group_col]}: {row['pct']:.1f}%" for _, row in top.iterrows() if row['pct'] > 0]
                    if len(group[group['pct'] > 0]) > 3:
                        formatted.append("...")
                    return "<br>".join(formatted) if formatted else "Sin datos"
                return grouped.groupby('manz_ccnct').apply(format_group).reset_index(name=f'{group_col}_dist')

            tax_dist = get_distribution(df, 'taxonomy')
            pisos_dist = get_distribution(df, 'NumeroPisos').rename(columns={'NumeroPisos_dist': 'pisos_dist'})

            # Group by Block ID and Sum numeric metrics
            df_grouped = df.groupby('manz_ccnct')[available_metrics].sum().reset_index()
            
            # Merge distributions
            if not tax_dist.empty:
                df_grouped = df_grouped.merge(tax_dist, on='manz_ccnct', how='left')
            if not pisos_dist.empty:
                df_grouped = df_grouped.merge(pisos_dist, on='manz_ccnct', how='left')
                
            df = df_grouped

        # 2. Load GeoJSON/GPKG
        geo_pattern = os.path.join(mun_dir, "*", "Manzana*.gpkg")
        geo_files = glob.glob(geo_pattern)
        if not geo_files:
             geo_files = glob.glob(os.path.join(mun_dir, "Manzana*.gpkg"))
        
        gdf = None
        if geo_files:
            gdf = gpd.read_file(geo_files[0])
            if 'manz_ccnct' in gdf.columns:
                gdf = gdf[['manz_ccnct', 'geometry']].drop_duplicates(subset='manz_ccnct')
        
        if df is not None and gdf is not None:
            gdf['manz_ccnct'] = gdf['manz_ccnct'].astype(str)
            df['manz_ccnct'] = df['manz_ccnct'].astype(str)
            merged = gdf.merge(df, on='manz_ccnct', how='left')
            # Fill NaNs in distribution text for cleaner tooltips
            merged['taxonomy_dist'] = merged['taxonomy_dist'].fillna('Sin datos')
            merged['pisos_dist'] = merged['pisos_dist'].fillna('Sin datos')
            return merged
            
    except Exception as e:
        print(f"Error loading spatial data: {e}")
        return None
    return None

def get_color(value, min_val, max_val, scale_name="Reds"):
    """
    Calcula y extrae un color en formato hexadecimal dada una escala de colores de Plotly y el valor normalizado en un rango.
    """
    if pd.isna(value):
        return "#cccccc"
    
    # Normalize
    if max_val == min_val:
        norm = 0
    else:
        norm = (value - min_val) / (max_val - min_val)
    
    # Get color from Plotly scale
    # pc.sample_colorscale returns list of hex
    color = pc.sample_colorscale(scale_name, [norm])[0]
    return color

import dash_bootstrap_components as dbc

# --- Helper Functions ---

def create_header(municipality):
    """
    Genera el encabezado HTML para la interfaz de distribución espacial según el municipio seleccionado.
    """
    return html.Div([
        html.Div([
            html.Div([
                html.Div([
                    html.H1(f"Afectaciones anuales promedio a nivel de manzana", style={
                        'color': 'white', 
                        'margin': '0', 
                        'fontSize': '2rem', 
                        'fontWeight': '700',
                        'fontFamily': "'Poppins', sans-serif"
                    }),
                    html.P(f"Municipio de {data_service.get_municipality_display_name(municipality)}", style={
                        'color': 'rgba(255,255,255,0.8)', 
                        'margin': '4px 0 0 0', 
                        'fontSize': '1rem',
                        'fontWeight': '400'
                    })
                ], style={'textAlign': 'center'})
            ], style={'display': 'flex', 'alignItems': 'center', 'justifyContent': 'center'})
        ], style={
            'maxWidth': '1400px', 
            'margin': '0 auto', 
            'padding': '0 20px'
        })
    ], style={
        'background': 'linear-gradient(135deg, #0a2240 0%, #081a32 100%)',
        'padding': '32px 0',
        'marginBottom': '32px',
        'boxShadow': '0 4px 20px rgba(0,0,0,0.15)',
        'borderBottom': '2px solid #f5c800'
    })

def layout(municipality="Caucasia"):
    """
    Configura y retorna el layout global de la página de distribución espacial, incluyendo controles, mapa y leyenda.
    """
    if not municipality:
        municipality = "Caucasia"
        
    return html.Div([
        # Header
        create_header(municipality),
        
        # Main Content
        html.Div([
            # Controls Card
            html.Div([
                html.Label("Seleccione la métrica de análisis:", style={'fontWeight': '600', 'color': '#0a2240', 'marginBottom': '8px', 'display': 'block'}),
                html.Div([
                    dcc.Dropdown(
                        id='spatial-metric-dropdown',
                        options=[
                            {'label': 'Pérdida económica anual promedio (Millones COP)', 'value': 'perc_abs'},
                            {'label': 'Pérdida económica relativa (%)', 'value': 'perc_rel'},
                            {'label': 'Fallecidos promedio anual (No.)', 'value': 'fall_abs'},
                            {'label': 'Fallecidos relativos (por 1,000 hab)', 'value': 'fall_rel'},
                            {'label': 'Heridos promedio anual (No.)', 'value': 'her_abs'},
                            {'label': 'Heridos relativos (por 1,000 hab)', 'value': 'her_rel'},
                            {'label': 'Desplazados promedio anual (No.)', 'value': 'des_abs'},
                            {'label': 'Desplazados relativos (por 1,000 hab)', 'value': 'des_rel'},
                            {'label': 'Daño completo (No.)', 'value': 'dam_abs'},
                            {'label': 'Daño completo (por 1,000 edif)', 'value': 'dam_rel'},
                        ],
                        value='perc_abs',
                        clearable=False,
                        style={'width': '100%', 'fontSize': '0.9rem'}
                    ),
                ], className="modern-dropdown-container"),
                dcc.Store(id='spatial-municipality-store', data=municipality)
            ], style={
                'backgroundColor': 'white', 
                'padding': '24px', 
                'borderRadius': '16px', 
                'boxShadow': '0 4px 6px rgba(0,0,0,0.05)',
                'marginBottom': '24px',
                'border': '1px solid #f1f5f9'
            }),
            
            # Map Container
            html.Div([
                html.Div(id='spatial-map-container', style={'height': '75vh', 'width': '100%', 'position': 'relative', 'borderRadius': '16px', 'overflow': 'hidden', 'boxShadow': '0 10px 30px rgba(0,0,0,0.1)'}, children=[
                    # Map will be injected here
                    dcc.Loading(type="cube", color="#f5c800", children=[
                         html.Div(id='spatial-leaflet-content')
                    ])
                ]),
                
                # Metric Legend Container (Absolute position overlaid on map bottom right)
                 html.Div(id='spatial-legend-container', style={
                    'position': 'absolute', 
                    'bottom': '30px', 
                    'right': '30px', 
                    'zIndex': '1000', 
                    'backgroundColor': 'rgba(255, 255, 255, 0.95)', 
                    'padding': '16px', 
                    'borderRadius': '12px',
                    'boxShadow': '0 8px 32px rgba(0,0,0,0.15)',
                    'backdropFilter': 'blur(8px)',
                    'border': '1px solid rgba(255,255,255,0.5)'
                })
    
            ], style={'position': 'relative'}), 
            
            html.Div(style={'height': '80px'}) # Spacer
            
        ], style={'maxWidth': '1400px', 'margin': '0 auto', 'padding': '0 20px'}),
        
    ], style={'backgroundColor': '#f0f2f5', 'minHeight': '100vh', 'fontFamily': '"Poppins", sans-serif', 'paddingTop': '180px', 'paddingBottom': '20px'})

@callback(
    [Output('spatial-leaflet-content', 'children'),
     Output('spatial-legend-container', 'children')],
    [Input('spatial-metric-dropdown', 'value'),
     Input('spatial-municipality-store', 'data')]
)
def update_map(metric, municipality):
    """
    Callback para actualizar dinámicamente el componente GeoJSON del mapa y la leyenda en función de la métrica y municipio escogido.
    """
    # Load Data
    gdf = load_data(municipality)
    
    if gdf is None or gdf.empty:
        return html.Div("No data found"), html.Div()
        
    # Determine Column and Title
    col = None
    title = ""
    unit = ""
    color_scale_name = "Reds"
    
    if metric == 'perc_abs':
        col = 'Perdida_Tot'
        title = "Pérdida promedio"
        unit = "M COP"
        color_scale_name = "Magma_r" 
    elif metric == 'perc_rel':
        col = 'PerdidaRel_Tot'
        gdf[col] = gdf[col] * 100
        title = "Pérdida relativa"
        unit = "%"
        color_scale_name = "Viridis_r"
    elif metric == 'fall_abs':
        col = 'Fallecidos_Tot'
        title = "Fallecidos"
        unit = "Pers"
        color_scale_name = "Reds"
    elif metric == 'fall_rel':
        col = 'FallecidosRel_Tot'
        gdf[col] = gdf[col] * 1000
        title = "Fallecidos rel."
        unit = "‰"
        color_scale_name = "Reds"
    elif metric == 'her_abs':
        col = 'Heridos_Tot'
        title = "Heridos"
        unit = "Pers"
        color_scale_name = "Reds"
    elif metric == 'her_rel':
        col = 'HeridosRel_Tot'
        gdf[col] = gdf[col] * 1000
        title = "Heridos rel."
        unit = "‰"
        color_scale_name = "Reds"
    elif metric == 'des_abs':
        col = 'Desplazados_Tot'
        title = "Desplazados"
        unit = "Pers"
        color_scale_name = "Reds"
    elif metric == 'des_rel':
        col = 'DesplazadosRel_Tot'
        gdf[col] = gdf[col] * 1000
        title = "Desplazados rel."
        unit = "‰"
        color_scale_name = "Reds"
    elif metric == 'dam_abs':
        col = 'DanoCompleto_Tot'
        title = "Daño completo"
        unit = "Edif"
        color_scale_name = "Reds"
    elif metric == 'dam_rel':
        col = 'DanoCompletoRel_Tot'
        gdf[col] = gdf[col] * 1000
        title = "Daño completo rel."
        unit = "‰"
        color_scale_name = "Reds"

    if col not in gdf.columns:
         return html.Div(f"Column {col} not found"), html.Div()

    # Pre-calculate colors
    # Use 5th and 95th percentiles as requested
    min_val = gdf[col].quantile(0.05)
    max_val = gdf[col].quantile(0.95)
    
    # Ensure safeguards if constant value or empty
    if pd.isna(min_val) or pd.isna(max_val):
        min_val = gdf[col].min()
        max_val = gdf[col].max()
        
    if min_val == max_val:
        # Avoid division by zero in normalization
        # Fallback to absolute mins/maxs if quartiles are equal (rare but possible in sparse data)
        min_val = gdf[col].min()
        max_val = gdf[col].max()

    # Add tooltip and style property
    # We construct a simpler dict list for GeoJSON because direct GeoDataFrame passing 
    # doesn't support row-based styling in dl.GeoJSON easily without a JS function 
    # that parses a property.
    
    # Generate colors using CLAMPED values
    def get_clamped_color(val, mn, mx, scale):
        """Restringe el valor dentro de los mínimos y máximos para evitar desbordes al extraer colores de la escala."""
        if pd.isna(val): return "#cccccc"
        val_clamped = max(mn, min(val, mx))
        return get_color(val_clamped, mn, mx, scale)

    gdf['fillColor'] = gdf[col].apply(lambda x: get_clamped_color(x, min_val, max_val, color_scale_name))
    
    # Generate Tooltip content
    # Format: <b>Manzana:</b> {ID}<br><b>{Metric}:</b> {Value} {Unit}<br>...Distributions...
    def create_tooltip(row):
        """Construye un bloque de texto HTML detallado para el tooltip interactivo del GeoJSON de cada manzana."""
        val = row[col]
        
        # Safe access to distributions (merged above)
        tax_str = row.get('taxonomy_dist', 'N/A')
        pisos_str = row.get('pisos_dist', 'N/A')
        
        return (
            f"<b>Municipio:</b> {data_service.get_municipality_display_name(municipality)}<br>"
            f"<b>Manzana:</b> {row['manz_ccnct']}<br>"
            f"<b>{title}:</b> {val:.6f} {unit}<br>"
            f"<hr style='margin:5px 0'>"
            f"<b>Distribución Pisos:</b><br>{pisos_str}<br>"
            f"<br><b>Distribución Taxonomía:</b><br>{tax_str}"
        )
        
    gdf['tooltip'] = gdf.apply(create_tooltip, axis=1)
    
    # Tooltip
    # We can use `hover_style_arrow` or similar from dash_extensions but let's keep it simple.
    # dl.GeoJSON has `hoverStyle`.
    
    geojson_data = json.loads(gdf.to_json())
    
    # Calculate bounds
    # gdf.total_bounds returns [minx, miny, maxx, maxy]
    # dash-leaflet expects [[miny, minx], [maxy, maxx]] (SouthWest, NorthEast)
    minx, miny, maxx, maxy = gdf.total_bounds
    bounds = [[miny, minx], [maxy, maxx]]
    
    # Styles
    # Base Layers
    # Esri Satellite
    satellite = dl.BaseLayer(
        dl.TileLayer(url="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
                     attribution="Esri"),
        name="Satelite",
        checked=True # Default
    )
    
    osm = dl.BaseLayer(dl.TileLayer(), name="Callejero", checked=False)
    carto_pos = dl.BaseLayer(dl.TileLayer(url="https://cartodb-basemaps-{s}.global.ssl.fastly.net/light_all/{z}/{x}/{y}.png", attribution="CartoDB"), name="Claro", checked=False)
    carto_dark = dl.BaseLayer(dl.TileLayer(url="https://cartodb-basemaps-{s}.global.ssl.fastly.net/dark_all/{z}/{x}/{y}.png", attribution="CartoDB"), name="Oscuro", checked=False)

    # GeoJSON Layer
    # We use a JS function for style to read fillColor from properties.
    # Since we can't easily write new JS assets here, we'll try to rely on 'options' if possible, 
    # OR we just rely on the fact that if we pass `style` as a dict it applies to all. 
    # But we need Choropleth.
    
    # Alternative: Use "hideout" and a functional prop in functional component? 
    # Standard dl.GeoJSON `style` can be a function handle.
    # Namespace("dl", "style") might not exist.
    # Let's use a workaround:
    # We can't insert JS easily. 
    # BUT, we can use `dl.Choropleth` equivalent... which is `dl.GeoJSON` with hideout.
    # Wait, `app.py` has `Namespace`. If there is a `assets/custom.js`...
    # There is `assets/clientside.js`. 
    # Let's assume we can't depend on custom JS.
    # STRATEGY: Create a unique Colorbar/Legend manually in HTML (done below) and 
    # for the map, if we can't color per feature without JS, we are stuck.
    # WAIT! `dl.GeoJSON` data allows Style in `properties` if `pointToLayer` is used, but for polygons...
    
    # Let's check if we can pass a dictionary to `options`.
    # `options=dict(style=...)`.
    
    # Actually, the simplest way without JS files is:
    # Use `dl.Colorbar` + `dl.GeoJSON(..., hideout=...)` if we had the JS function hooked up.
    # Since we are in a rush and need to be reliable:
    # We will assume `assign` (dash_extensions) is NOT available unless checked.
    # But wait, `app.py` line 14: `from dash_extensions.javascript import Namespace`.
    # So `dash_extensions` IS installed.
    # I can import `assign`.
    
    # Use raw dict for dash-extensions variable reference to avoid Namespace serialization issues
    # This points to window.spatialMaps.styleHandle defined in assets/spatial_maps.js
    style_handle = {"variable": "spatialMaps.styleHandle"}
    on_each_feature_handle = {"variable": "spatialMaps.onEachFeatureHandle"}
    
    geojson_layer = dl.GeoJSON(
        data=geojson_data,
        style=style_handle,
        onEachFeature=on_each_feature_handle,
        hoverStyle={"weight": 5, "color": '#666', "dashArray": ""},
        id="geojson-layer-spatial"
    )
    
    map_component = dl.Map(bounds=bounds, children=[
        dl.LayersControl([
            satellite, osm, carto_pos, carto_dark
        ]),
        geojson_layer
    ], style={'width': '100%', 'height': '70vh'})
    
    # Legend HTML
    # create a gradient bar
    colors = pc.sample_colorscale(color_scale_name, np.linspace(0, 1, 10))
    gradient_str = ", ".join(colors)
    
    legend = html.Div([
        html.H4(title, style={'fontSize': '14px', 'fontWeight': 'bold', 'marginBottom': '5px'}),
        html.Div(style={
            'background': f'linear-gradient(to right, {gradient_str})',
            'height': '15px',
            'width': '100%',
            'marginBottom': '5px'
        }),
        html.Div([
            html.Span(f"{min_val:.6f} {unit}", style={'fontSize': '12px'}),
            html.Span(f"{max_val:.6f} {unit}", style={'fontSize': '12px'})
        ], style={'display': 'flex', 'justifyContent': 'space-between'})
    ], style={'minWidth': '200px'})

    return map_component, legend
