import data_service

import glob
import os
import pandas as pd
import geopandas as gpd
import dash_leaflet as dl
from dash import html, dcc, callback, Input, Output, State
import dash
import json
import numpy as np
import plotly.colors as pc
import plotly.express as px

# Helper to load data
def load_data(municipality, scenario_id):
    """
    Carga y procesa los datos espaciales y de riesgo asociados a un escenario y municipio, combinando archivos Excel y GeoPackages (manzanas).
    """
    try:
        BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        DATA_DIR = os.path.join(BASE_DIR, 'data')
        mun_dir = os.path.join(DATA_DIR, 'municipios', municipality)
        
        # 1. Load Excel Data
        # Pattern: ResumenTOTAL*{municipality}*{scenario_id}*.xlsx
        pattern = os.path.join(mun_dir, f"ResumenTOTAL*{municipality}*{scenario_id}*.xlsx")
        files = glob.glob(pattern)
            
        df = None
        if files:
            # Sheet is 'perdidas' for scenarios
            df = pd.read_excel(files[0], sheet_name='perdidas')
            # Clean Code: Remove leading 'C'
            df['manz_ccnct'] = df['CodigoManzana2024'].astype(str).str.replace('C', '', 1)
            
            # Metrics Columns (same as standard report)
            metrics_cols = [
                'Perdida_Tot', 'PerdidaRel_Tot',
                'Fallecidos_Tot', 'FallecidosRel_Tot',
                'Heridos_Tot', 'HeridosRel_Tot',
                'Desplazados_Tot', 'DesplazadosRel_Tot',
                'DanoCompleto_Tot', 'DanoCompletoRel_Tot'
            ]
            
            available_metrics = [c for c in metrics_cols if c in df.columns]
            
            for col in available_metrics:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
                
            # Distributions (Weighted by NumEdificios)
            def get_distribution(df_data, group_col):
                """Calcula la distribución porcentual ponderada por el número de edificaciones para una columna de agrupación dada."""
                if group_col not in df_data.columns or 'NumEdificios' not in df_data.columns:
                    return pd.DataFrame(columns=['manz_ccnct', f'{group_col}_dist'])
                grouped = df_data.groupby(['manz_ccnct', group_col])['NumEdificios'].sum().reset_index()
                totals = grouped.groupby('manz_ccnct')['NumEdificios'].transform('sum')
                grouped['pct'] = np.where(totals > 0, (grouped['NumEdificios'] / totals) * 100, 0)
                def format_group(group):
                    """Formatea el top de los grupos de distribución en una cadena de texto para visualizar en tooltips."""
                    group = group.sort_values('pct', ascending=False)
                    top = group.head(3)
                    formatted = [f"{row[group_col]}: {row['pct']:.1f}%" for _, row in top.iterrows() if row['pct'] > 0]
                    if len(group[group['pct'] > 0]) > 3:
                        formatted.append("...")
                    return "<br>".join(formatted) if formatted else "Sin datos"
                return grouped.groupby('manz_ccnct').apply(format_group).reset_index(name=f'{group_col}_dist')

            tax_dist = get_distribution(df, 'taxonomy')
            pisos_dist = get_distribution(df, 'NumeroPisos').rename(columns={'NumeroPisos_dist': 'pisos_dist'})

            # Grouping
            df_grouped = df.groupby('manz_ccnct')[available_metrics].sum().reset_index()
            
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
            merged['taxonomy_dist'] = merged['taxonomy_dist'].fillna('Sin datos')
            merged['pisos_dist'] = merged['pisos_dist'].fillna('Sin datos')
            return merged
            
    except Exception as e:
        print(f"Error loading spatial data: {e}")
        return None
    return None

def get_color(value, min_val, max_val, scale_name="Reds"):
    """
    Interpola y obtiene un color de una escala de colores de Plotly con base en un valor numérico normalizado.
    """
    if pd.isna(value): return "#cccccc"
    if max_val == min_val: norm = 0
    else: norm = (value - min_val) / (max_val - min_val)
    return pc.sample_colorscale(scale_name, [norm])[0]

# --- Helper Functions ---

def create_header(municipality, scenario_id):
    """
    Genera el componente visual del encabezado de la página de escenario a nivel de manzana.
    """
    title_scenario = "R1" if "R1" in scenario_id else "R2" if "R2" in scenario_id else scenario_id
    return html.Div([
        html.Div([
            html.Div([
                html.H1(f"Afectaciones promedio (manzana) - Escenario {title_scenario}", style={
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
        ], style={'maxWidth': '1400px', 'margin': '0 auto', 'padding': '0 20px'})
    ], style={
        'background': 'linear-gradient(135deg, #0a2240 0%, #081a32 100%)',
        'padding': '32px 0',
        'marginBottom': '32px',
        'boxShadow': '0 4px 20px rgba(0,0,0,0.15)',
        'borderBottom': '2px solid #f5c800'
    })

def layout(municipality="Caucasia", scenario_id="R1"):
    """
    Genera el diseño completo (layout) de la interfaz de usuario para la visualización del mapa interactivo de afectaciones por escenario.
    """
    if not municipality:
        municipality = "Caucasia"
        
    return html.Div([
        create_header(municipality, scenario_id),
        
        html.Div([
            # Controls
            html.Div([
                html.Label("Seleccione la métrica de análisis:", style={'fontWeight': '600', 'color': '#0a2240', 'marginBottom': '8px', 'display': 'block'}),
                html.Div([
                    dcc.Dropdown(
                        id='em-metric-dropdown',
                        options=[
                            {'label': 'Pérdida económica (Millones COP)', 'value': 'perc_abs'},
                            {'label': 'Pérdida económica relativa (%)', 'value': 'perc_rel'},
                            {'label': 'Fallecidos (No.)', 'value': 'fall_abs'},
                            {'label': 'Fallecidos relativos (por 1,000 hab)', 'value': 'fall_rel'},
                            {'label': 'Heridos (No.)', 'value': 'her_abs'},
                            {'label': 'Heridos relativos (por 1,000 hab)', 'value': 'her_rel'},
                            {'label': 'Desplazados (No.)', 'value': 'des_abs'},
                            {'label': 'Desplazados relativos (por 1,000 hab)', 'value': 'des_rel'},
                            {'label': 'Daño completo (No.)', 'value': 'dam_abs'},
                            {'label': 'Daño completo (por 1,000 edif)', 'value': 'dam_rel'},
                        ],
                        value='perc_abs',
                        clearable=False,
                        style={'width': '100%', 'fontSize': '0.9rem'}
                    ),
                ], className="modern-dropdown-container"),
                dcc.Store(id='em-municipality-store', data=municipality),
                dcc.Store(id='em-scenario-store', data=scenario_id)
            ], style={'backgroundColor': 'white', 'padding': '24px', 'borderRadius': '16px', 'boxShadow': '0 4px 6px rgba(0,0,0,0.05)', 'marginBottom': '24px', 'border': '1px solid #f1f5f9'}),
            
            # Map
            html.Div([
                html.Div(id='em-map-container', style={'height': '75vh', 'width': '100%', 'position': 'relative', 'borderRadius': '16px', 'overflow': 'hidden', 'boxShadow': '0 10px 30px rgba(0,0,0,0.1)'}, children=[
                    dcc.Loading(type="cube", color="#f5c800", children=[
                         html.Div(id='em-leaflet-content')
                    ])
                ]),
                html.Div(id='em-legend-container', style={'position': 'absolute', 'bottom': '30px', 'right': '30px', 'zIndex': '1000', 'backgroundColor': 'rgba(255, 255, 255, 0.95)', 'padding': '16px', 'borderRadius': '12px', 'boxShadow': '0 8px 32px rgba(0,0,0,0.15)'})
            ], style={'position': 'relative'}), 
            
            html.Div(style={'height': '80px'})
        ], style={'maxWidth': '1400px', 'margin': '0 auto', 'padding': '0 20px'}),
        
    ], style={'backgroundColor': '#f0f2f5', 'minHeight': '100vh', 'fontFamily': '"Poppins", sans-serif', 'paddingTop': '180px', 'paddingBottom': '20px'})

@callback(
    [Output('em-leaflet-content', 'children'),
     Output('em-legend-container', 'children')],
    [Input('em-metric-dropdown', 'value'),
     Input('em-municipality-store', 'data'),
     Input('em-scenario-store', 'data')]
)
def update_map(metric, municipality, scenario_id):
    """
    Callback de Dash que actualiza el mapa interactivo GeoJSON y la leyenda basándose en la métrica, municipio y escenario.
    """
    gdf = load_data(municipality, scenario_id)
    
    if gdf is None or gdf.empty:
        return html.Div([
            html.Div([
                html.I(className='bx bx-error-circle', style={'fontSize': '3rem', 'color': '#ef4444', 'marginBottom': '10px'}),
                html.H4("Datos no encontrados", style={'fontWeight': 'bold'}),
                html.P(f"No hay datos espaciales para el escenario {'1 (Tr: 225 años)' if 'R1' in scenario_id else '2 (Tr: 475 años)' if 'R2' in scenario_id else scenario_id}.")
            ], style={'textAlign': 'center', 'padding': '50px'})
        ]), html.Div()
        
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
    min_val = gdf[col].quantile(0.05)
    max_val = gdf[col].quantile(0.95)
    
    if pd.isna(min_val) or pd.isna(max_val):
        min_val = gdf[col].min()
        max_val = gdf[col].max()
        
    if min_val == max_val:
        min_val = gdf[col].min()
        max_val = gdf[col].max()

    def get_clamped_color(val, mn, mx, scale):
        """Asegura que el valor para calcular el color esté confinado (clamped) dentro de los límites y devuelve el color correspondiente."""
        if pd.isna(val): return "#cccccc"
        val_clamped = max(mn, min(val, mx))
        return get_color(val_clamped, mn, mx, scale)

    gdf['fillColor'] = gdf[col].apply(lambda x: get_clamped_color(x, min_val, max_val, color_scale_name))
    
    def create_tooltip(row):
        """Genera una cadena de texto en formato HTML con información de las variables y distribuciones para el tooltip del mapa."""
        val = row[col]
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
    
    geojson_data = json.loads(gdf.to_json())
    
    minx, miny, maxx, maxy = gdf.total_bounds
    bounds = [[miny, minx], [maxy, maxx]]
    
    satellite = dl.BaseLayer(dl.TileLayer(url="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}", attribution="Esri"), name="Satelite", checked=True)
    osm = dl.BaseLayer(dl.TileLayer(), name="Callejero", checked=False)
    carto_pos = dl.BaseLayer(dl.TileLayer(url="https://cartodb-basemaps-{s}.global.ssl.fastly.net/light_all/{z}/{x}/{y}.png", attribution="CartoDB"), name="Claro", checked=False)
    carto_dark = dl.BaseLayer(dl.TileLayer(url="https://cartodb-basemaps-{s}.global.ssl.fastly.net/dark_all/{z}/{x}/{y}.png", attribution="CartoDB"), name="Oscuro", checked=False)

    style_handle = {"variable": "spatialMaps.styleHandle"}
    on_each_feature_handle = {"variable": "spatialMaps.onEachFeatureHandle"}
    
    geojson_layer = dl.GeoJSON(
        data=geojson_data,
        style=style_handle,
        onEachFeature=on_each_feature_handle,
        hoverStyle={"weight": 5, "color": '#666', "dashArray": ""},
        id="geojson-layer-spatial-em"
    )
    
    map_component = dl.Map(bounds=bounds, children=[
        dl.LayersControl([satellite, osm, carto_pos, carto_dark]),
        geojson_layer
    ], style={'width': '100%', 'height': '70vh'})
    
    colors = pc.sample_colorscale(color_scale_name, np.linspace(0, 1, 10))
    gradient_str = ", ".join(colors)
    
    legend = html.Div([
        html.H4(title, style={'fontSize': '14px', 'fontWeight': 'bold', 'marginBottom': '5px'}),
        html.Div(style={'background': f'linear-gradient(to right, {gradient_str})', 'height': '15px', 'width': '100%', 'marginBottom': '5px'}),
        html.Div([
            html.Span(f"{min_val:.6f} {unit}", style={'fontSize': '12px'}),
            html.Span(f"{max_val:.6f} {unit}", style={'fontSize': '12px'})
        ], style={'display': 'flex', 'justifyContent': 'space-between'})
    ], style={'minWidth': '200px'})

    return map_component, legend
