
import dash
from dash import dcc, html
import dash_bootstrap_components as dbc
import dash_leaflet as dl
import data_service
import pandas as pd
import geopandas as gpd
import json

def layout(municipality, scenario_id):
    """
    Genera el diseño de la página de ubicación del escenario, obteniendo los datos geográficos y mostrando un mapa con el epicentro usando Dash Leaflet.
    """
    if not municipality:
        return html.Div("Por favor seleccione un municipio.", style={'padding': '50px', 'textAlign': 'center'})

    # 1. Get Data
    data = data_service.get_scenario_location_data(municipality, scenario_id)
    geo_gdf = data_service.get_municipio_geometry(municipality)
    
    if data is None:
        return html.Div([
            html.Div([
                html.I(className='bx bx-error-circle', style={'fontSize': '4rem', 'color': '#ef4444', 'marginBottom': '20px'}),
                html.H3(f"Datos no encontrados", style={'color': '#0a2240', 'fontWeight': 'bold'}),
                html.P(f"No se encontraron datos para el escenario {scenario_id} en el municipio de {data_service.get_municipality_display_name(municipality)}.", style={'fontSize': '1.1rem', 'color': '#666'}),
                html.P("Por favor verifique que los archivos de datos existan en la carpeta correspondiente.", style={'fontSize': '0.9rem', 'color': '#999', 'marginTop': '10px'})
            ], style={'textAlign': 'center', 'backgroundColor': 'white', 'padding': '50px', 'borderRadius': '16px', 'boxShadow': '0 4px 20px rgba(0,0,0,0.08)', 'maxWidth': '600px', 'margin': '0 auto'})
        ], style={'padding': '100px 20px', 'backgroundColor': '#f0f2f5', 'height': '100vh'})

    # Extract coordinates for map center and marker
    lat = data.get('Lat')
    lon = data.get('Lon')
    magnitude = data.get('Magnitud', 'N/A')
    depth = data.get('Profundidad', 'N/A')
    
    # Map Setup
    # Ensure Lat/Lon are valid floats
    try:
        if lat is not None and lon is not None:
             lat = float(lat)
             lon = float(lon)
             valid_coords = True
             map_center = [lat, lon]
        else:
            valid_coords = False
            map_center = [6.5, -75.5] # Default Antioquia
    except:
        valid_coords = False
        map_center = [6.5, -75.5]
    
    map_zoom = 9

    # Geometry Layer (Municipality)
    geojson_layer = None
    if not geo_gdf.empty:
        # Convert to GeoJSON format for dash-leaflet
        geojson_data = json.loads(geo_gdf.to_json())
        geojson_layer = dl.GeoJSON(data=geojson_data, options=dict(style=dict(color="#0a2240", weight=2, fillOpacity=0.1)))
        
        # If we have a geometry but no epicenter, maybe center on the municipality?
        if not valid_coords:
             # Basic centroid logic if needed, or just let map default
             pass

    # 2. Header
    title_scenario = "R1" if "R1" in scenario_id else "R2" if "R2" in scenario_id else scenario_id
    title = f"Ubicación del escenario {title_scenario}"
    header = html.Div([
        html.Div([
             html.Div([
                html.Div([
                    html.H1(title, style={
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
        ], style={'maxWidth': '1400px', 'margin': '0 auto', 'padding': '0 20px'}),
    ], style={
        'background': 'linear-gradient(135deg, #0a2240 0%, #081a32 100%)',
        'padding': '32px 0',
        'borderBottom': '2px solid #f5c800',
        'marginBottom': '32px',
        'boxShadow': '0 4px 20px rgba(0,0,0,0.15)'
    })

    # 3. Content Layout
    
    # Table Rows
    table_rows = []
    # Mapping keys to labels based on user image/requirement
    # Keys from file: ['ruptura', 'Tr', 'ambiente', 'Magnitud', 'Lon', 'Lat', 'Profundidad']
    display_map = {
        'ruptura': 'Escenario',
        'Tr': 'Periodo de retorno (años)',
        'ambiente': 'Ambiente tectónico',
        'Magnitud': 'Magnitud (Mw)',
        'Lon': 'Longitud',
        'Lat': 'Latitud',
        'Profundidad': 'Profundidad (km)'
    }
    
    for key, label in display_map.items():
        val = data.get(key, '')
        # Formatting numbers
        if isinstance(val, (int, float)):
             if key in ['Lon', 'Lat']:
                 val = f"{val:.4f}"
             elif key in ['Magnitud', 'Profundidad']:
                 val = f"{val:.2f}"
             else:
                 val = f"{val}"
        
        table_rows.append(html.Tr([
            html.Td(label, style={'fontWeight': '600', 'color': '#0a2240', 'backgroundColor': '#f8f9fa', 'width': '40%'}),
            html.Td(str(val), style={'textAlign': 'right'})
        ]))

    # --- SEISMIC VISUALIZATION LOGIC ---
    
    # 1. Color by Depth (Profundidad)
    # Shallow (< 70 km): Red (Danger/Surface)
    # Intermediate (70 - 300 km): Orange
    # Deep (> 300 km): Blue (Deep)
    try:
        depth_val = float(depth)
        if depth_val < 70:
            depth_color = "#d62728" # Red
            depth_label = "Superficial (< 70km)"
        elif depth_val < 300:
            depth_color = "#ff7f0e" # Orange
            depth_label = "Intermedio (70-300km)"
        else:
            depth_color = "#1f77b4" # Blue
            depth_label = "Profundo (> 300km)"
    except:
        depth_color = "#333" # Default
        depth_label = "Desconocido"

    # 2. Radius by Magnitude
    try:
        mag_val = float(magnitude)
        # Scale: Mw 5 -> 10px, Mw 7 -> 20px, Mw 9 -> 30px (Approx)
        base_radius = (mag_val ** 1.5) # Non-linear scaling
    except:
        base_radius = 10

    # 3. Create Layers
    map_layers = [
         dl.LayersControl([
             dl.BaseLayer(dl.TileLayer(url="https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png"), name="Claro"),
             dl.BaseLayer(dl.TileLayer(url="https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png"), name="Voyager"),
             dl.BaseLayer(dl.TileLayer(url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"), name="Oscuro"),
             dl.BaseLayer(dl.TileLayer(url="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"), name="Satélite"),
             dl.BaseLayer(dl.TileLayer(url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"), name="Geográfico", checked=True),
             dl.BaseLayer(dl.TileLayer(url="https://server.arcgisonline.com/ArcGIS/rest/services/World_Street_Map/MapServer/tile/{z}/{y}/{x}"), name="Callejero"),
             dl.BaseLayer(dl.TileLayer(url="https://{s}.tile.opentopomap.org/{z}/{x}/{y}.png"), name="Topográfico")
         ], position="bottomright")
    ]

    if geojson_layer:
        map_layers.append(geojson_layer)

    # Epicenter Visuals - ONLY IF COORDS ARE VALID
    if valid_coords:
        # A. "Pulse" Rings (Static concentric circles with decreasing opacity)
        map_layers.append(
            dl.CircleMarker(center=[lat, lon], radius=base_radius * 3, color=depth_color, weight=1, fill=True, fillOpacity=0.1, interactive=False)
        )
        map_layers.append(
            dl.CircleMarker(center=[lat, lon], radius=base_radius * 2, color=depth_color, weight=1, fill=True, fillOpacity=0.2, interactive=False)
        )

        # B. Main Epicenter Marker with RICHER TOOLTIP
        map_layers.append(
            dl.CircleMarker(center=[lat, lon], radius=base_radius, color="white", weight=2, fillColor=depth_color, fillOpacity=0.9, children=[
                dl.Tooltip(children=[
                    html.Div([
                        html.Div([
                            html.Span(f"Escenario {scenario_id}", style={'fontWeight': 'bold', 'color': '#0a2240', 'fontSize': '1.1rem'}),
                            html.Span(f"Mw {magnitude}", style={'backgroundColor': depth_color, 'color': 'white', 'padding': '2px 6px', 'borderRadius': '4px', 'marginLeft': '8px', 'fontSize': '0.9rem', 'fontWeight': 'bold'})
                        ], style={'display': 'flex', 'alignItems': 'center', 'marginBottom': '5px'}),
                        
                        html.Div([
                            html.I(className='bx bx-trending-down', style={'marginRight': '5px', 'fontSize': '1.2rem'}),
                            html.Span(f"Profundidad: {float(depth):.2f} km" if isinstance(depth, (int, float)) or (isinstance(depth, str) and depth != 'N/A') else f"Profundidad: {depth} km", style={'fontWeight': '500'}),
                        ], style={'display': 'flex', 'alignItems': 'center', 'fontSize': '0.9rem', 'color': '#333', 'marginBottom': '2px'}),
                        
                        html.Div([
                            html.I(className='bx bx-world', style={'marginRight': '5px', 'fontSize': '1.2rem'}),
                            html.Span(f"{data.get('ambiente', 'N/A')}", style={'fontWeight': '500'}),
                        ], style={'display': 'flex', 'alignItems': 'center', 'fontSize': '0.9rem', 'color': '#333'}),
                        
                        html.Div("Haga clic para ver detalles completos", style={'fontSize': '0.75rem', 'color': '#777', 'marginTop': '8px', 'fontStyle': 'italic', 'textAlign': 'center', 'borderTop': '1px solid #eee', 'paddingTop': '4px'})
                    ], style={'padding': '5px', 'fontFamily': "'Poppins', sans-serif", 'minWidth': '180px'})
                ], direction="top", opacity=1),
                
                dl.Popup([
                    html.H5(f"Escenario {scenario_id}", style={'marginBottom': '0'}),
                    html.Hr(style={'margin': '5px 0'}),
                    html.P(f"Magnitud: {magnitude} Mw", style={'margin': '0'}),
                    html.P(f"Profundidad: {float(depth):.2f} km" if isinstance(depth, (int, float)) or (isinstance(depth, str) and depth != 'N/A') else f"Profundidad: {depth} km", style={'margin': '0'}),
                    html.P(f"Ambiente: {data.get('ambiente', 'N/A')}", style={'margin': '0'}),
                    html.P(f"Tr: {data.get('Tr', 'N/A')} años", style={'margin': '0', 'fontSize': '0.9rem', 'color': '#666'})
                ])
            ])
        )
    
    # Map Component (leyenda de profundidad removida según requerimiento)
    map_component = html.Div([
        dl.Map(map_layers, center=map_center, zoom=map_zoom, style={'width': '100%', 'height': '500px'}, id=f"scenario-map-{scenario_id}")
    ], style={'border': '1px solid #dee2e6', 'borderRadius': '8px', 'overflow': 'hidden', 'boxShadow': '0 4px 15px rgba(0,0,0,0.05)', 'position': 'relative'})

    # Table Component
    table_component = html.Div([
        html.H4("Detalles del Evento", style={'color': '#0a2240', 'marginBottom': '20px', 'fontWeight': 'bold'}),
        dbc.Table(html.Tbody(table_rows), bordered=True, hover=True, responsive=True, className="modern-table")
    ], style={'backgroundColor': 'white', 'padding': '25px', 'borderRadius': '16px', 'boxShadow': '0 4px 20px rgba(0,0,0,0.05)'})

    content = dbc.Container([
        dbc.Row([
            dbc.Col(map_component, md=7, className="mb-4"),
            dbc.Col(table_component, md=5, className="mb-4"),
        ], className="g-4")
    ], fluid=True, style={'maxWidth': '1400px'})

    return html.Div([
        header,
        content,
        html.Div(style={'height': '50px'})
    ], style={
        'height': '100vh', 
        'overflowY': 'auto', 
        'backgroundColor': '#f0f2f5', 
        'paddingTop': '180px', # Space for floating header
        'paddingBottom': '20px',
        'fontFamily': '"Poppins", sans-serif'
    })
