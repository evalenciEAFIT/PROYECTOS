import data_service

import glob
import os
import pandas as pd
import numpy as np
from dash import html, dcc
import dash_bootstrap_components as dbc

# Formatter helper
def format_number(val, decimals=0):
    """
    Formatea un número con separadores de miles y la cantidad de decimales especificada.
    """
    if pd.isna(val):
        return "N/A"
    try:
        if decimals == 0:
             return f"{val:,.0f}"
        return f"{val:,.{decimals}f}"
    except:
        return str(val)

def get_scenario_risk_data(municipality, scenario_id):
    """
    Obtiene los datos de riesgo del escenario específico para un municipio leyendo el archivo Excel correspondiente.
    """
    try:
        BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        DATA_DIR = os.path.join(BASE_DIR, 'data')
        
        base_path = os.path.join(DATA_DIR, 'municipios', municipality)
        
        # Determine filename based on scenario
        # Relaxed Pattern to match: ResumenTOTAL_Caucasia_R1_TR225.xlsx OR similar variations
        # Use wildcards around municipality and scenario to be safe
        search_pattern = f"ResumenTOTAL*{municipality}*{scenario_id}*.xlsx"
        files = glob.glob(os.path.join(base_path, search_pattern))
        
        if not files:
            return None
            
        file_path = files[0]
        
        # Read 'riesgoag' sheet
        df = pd.read_excel(file_path, sheet_name='riesgoag')
        if not df.empty:
            return df.iloc[0]
                
        return None
    except Exception as e:
        print(f"Error loading scenario risk data for {municipality} {scenario_id}: {e}")
        return None

def create_stat_card(title, value, unit, icon, description=None, card_id=None):
    """
    Crea una tarjeta de estadística (KPI) utilizando componentes de Dash Bootstrap para mostrar un valor específico con su unidad e icono.
    """
    card_content = html.Div([
        dbc.Row([
            # Column 1: Icon
            dbc.Col(
                html.Div(
                    html.I(className=f"bx {icon}", style={'fontSize': '2rem', 'color': '#0a2240'}),
                    style={
                        'background': 'rgba(10, 34, 64, 0.08)', 
                        'borderRadius': '50%', 
                        'width': '64px', 
                        'height': '64px', 
                        'display': 'flex', 
                        'alignItems': 'center', 
                        'justifyContent': 'center'
                    }
                ),
                width="auto",
                className="d-flex align-items-start justify-content-center pe-0"
            ),
            
            # Column 2: Content
            dbc.Col(
                html.Div([
                    # Title
                    html.P(title, style={
                        'fontSize': '0.75rem', 
                        'letterSpacing': '1.0px', 
                        'color': '#64748b', 
                        'textTransform': 'uppercase',
                        'fontWeight': '700',
                        'marginBottom': '4px',
                        'lineHeight': '1.2'
                    }),
                    # Value & Unit
                    html.H2([
                        f"{value} ",
                        html.Span(unit, style={'fontSize': '0.9rem', 'color': '#64748b', 'fontWeight': '500'})
                    ], style={
                        'color': '#0a2240', 
                        'fontSize': '1.6rem', 
                        'fontWeight': '700',
                        'fontFamily': "'Poppins', sans-serif",
                        'margin': '0 0 8px 0',
                        'lineHeight': '1.1',
                        'wordBreak': 'break-word'
                    }),
                    # Description
                    html.P(description, style={
                        'fontSize': '0.8rem',
                        'color': '#64748b',
                        'lineHeight': '1.4',
                        'marginBottom': '0'
                    }) if description else None
                ], style={'display': 'flex', 'flexDirection': 'column'}),
                className="ps-3"
            )
        ], className="g-0 align-items-start h-100"),
        
    ], className="kpi-card p-4 h-100 hover-card", # Added hover-card for effect
       style={
           'backgroundColor': 'white', 
           'borderRadius': '16px', 
           'boxShadow': '0 4px 6px -1px rgba(0, 0, 0, 0.05)',
           'border': '1px solid #f1f5f9',
           'position': 'relative',
           'transition': 'all 0.3s ease',
           'height': '100%'
       })
    
    return card_content

def layout(municipality, scenario_id):
    """
    Genera el diseño completo (layout) visual de la página para mostrar los datos de riesgo de un municipio y escenario dados.
    """
    if not municipality:
        return html.Div("Por favor seleccione un municipio.", style={'padding': '50px', 'textAlign': 'center'})

    row_data = get_scenario_risk_data(municipality, scenario_id)
    
    display_scenario = "1 (Tr: 225 años)" if "R1" in scenario_id else "2 (Tr: 475 años)" if "R2" in scenario_id else scenario_id
    title_scenario = "R1" if "R1" in scenario_id else "R2" if "R2" in scenario_id else scenario_id
    title = f"Afectaciones promedio (Escenario {title_scenario})"
    
    # Header Section
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

    # Description Section
    description_section = dbc.Alert([
        html.Div([
            html.I(className="bx bx-info-circle", style={'fontSize': '1.5rem', 'marginRight': '12px', 'color': '#0284c7'}),
            html.Span(f"Este reporte presenta las afectaciones estimadas para el escenario sísmico {display_scenario}. Los valores indican el impacto esperado si ocurriera este evento específico.", 
                     style={'fontSize': '0.95rem', 'color': '#334155', 'lineHeight': '1.6'})
        ], style={'display': 'flex', 'alignItems': 'flex-start'})
    ], color="light", style={
        'maxWidth': '1400px', 
        'margin': '0 auto 32px auto', 
        'borderRadius': '12px',
        'border': '1px solid #e0f2fe',
        'backgroundColor': '#f0f9ff',
        'padding': '20px'
    })

    # --- Content Logic ---
    content_div = None
    
    if row_data is None:
        # Show Error
        content_div = html.Div([
            html.Div([
                html.I(className='bx bx-error-circle', style={'fontSize': '4rem', 'color': '#ef4444', 'marginBottom': '20px'}),
                html.H3(f"Datos no encontrados", style={'color': '#0a2240', 'fontWeight': 'bold'}),
                html.P(f"No se encontraron datos para el escenario {scenario_id} en {data_service.get_municipality_display_name(municipality)}.", style={'fontSize': '1.1rem', 'color': '#666'}),
            ], style={'textAlign': 'center', 'backgroundColor': 'white', 'padding': '50px', 'borderRadius': '16px', 'boxShadow': '0 4px 20px rgba(0,0,0,0.08)', 'maxWidth': '600px', 'margin': '0 auto'})
        ], style={'padding': '20px'})
    else:
        # Show Data
        # Exposición
        exp_val = row_data.get('ValExpuesto', 0) 
        exp_edif = row_data.get('NumEdificios', 0)
        exp_pob = row_data.get('Poblacion', 0)
        
        # Daño
        de_abs = row_data.get('DanoCompleto_Tot', 0)
        
        # Impacto
        ip_fal_abs = row_data.get('Fallecidos_Tot', 0)
        ip_des_abs = row_data.get('Desplazados_Tot', 0)
        ip_her_abs = row_data.get('Heridos_Tot', 0)
        
        # Pérdidas
        pe_abs_mill = row_data.get('Perdida_Tot', 0)
        pe_rel = row_data.get('PerdidaRel_Tot', 0) * 100

        # Create KPI Grid
        kpi_exposure = html.Div([
            html.H5("Exposición", className="mb-3", style={'color': '#0a2240', 'fontWeight': 'bold'}),
            dbc.Row([
                dbc.Col(create_stat_card("Valor Expuesto", format_number(exp_val, 0), "Millones COP", "bx-money", "Valor total de las edificaciones residenciales expuestas"), md=4, className="mb-4"),
                dbc.Col(create_stat_card("Edificaciones", format_number(exp_edif, 0), "Und", "bx-building", "Total de edificaciones residenciales"), md=4, className="mb-4"),
                dbc.Col(create_stat_card("Población", format_number(exp_pob, 0), "Hab", "bx-group", "Total de habitantes expuestos"), md=4, className="mb-4"),
            ], className="g-4")
        ], className="mb-4")
        
        kpi_impact = html.Div([
            html.H5("Impacto Estimado del Escenario", className="mb-3", style={'color': '#0a2240', 'fontWeight': 'bold'}),
            dbc.Row([
                dbc.Col(create_stat_card("Pérdida Económica", format_number(pe_abs_mill, 0), "Millones COP", "bx-line-chart", f"Pérdida relativa: {pe_rel:.2f}%"), md=6, className="mb-4"),
                dbc.Col(create_stat_card("Daño Completo", format_number(de_abs, 0), "Edificaciones", "bx-home-circle", "Edificaciones con daño completo esperado"), md=6, className="mb-4"),
            ], className="g-4"),
            
            dbc.Row([
                dbc.Col(create_stat_card("Fallecidos", format_number(ip_fal_abs, 0), "Pers", "bx-user-x", "Fallecidos esperados"), md=4, className="mb-4"),
                dbc.Col(create_stat_card("Heridos", format_number(ip_her_abs, 0), "Pers", "bx-plus-medical", "Heridos esperados"), md=4, className="mb-4"),
                dbc.Col(create_stat_card("Desplazados", format_number(ip_des_abs, 0), "Pers", "bx-walk", "Desplazados esperados"), md=4, className="mb-4"),
            ], className="g-4")
        ])
        
        # Detailed Table
        detailed_table_data = [
            # Exposición
            {"category": "Exposición", "metric": "Valor expuesto", "unit": "Millones de COP", "value": format_number(exp_val, 0)},
            {"category": "Exposición", "metric": "Número de edificaciones", "unit": "No.", "value": format_number(exp_edif, 0)},
            {"category": "Exposición", "metric": "Población", "unit": "No. hab.", "value": format_number(exp_pob, 0)},
            # Daño
            {"category": "Daño estructural absoluto", "metric": "Número de edificaciones con daño completo", "unit": "No.", "value": format_number(de_abs, 2)},
            {"category": "Daño estructural relativo", "metric": "Número relativo de edificaciones con daño completo", "unit": "‰", "value": format_number(row_data.get('DanoCompletoRel_Tot', 0) * 1000, 2)},
             # Impacto humano absoluto
            {"category": "Impacto población absoluto", "metric": "Número de fallecidos", "unit": "No. hab.", "value": format_number(ip_fal_abs, 0)},
            {"category": "Impacto población absoluto", "metric": "Número de desplazados", "unit": "No. hab.", "value": format_number(ip_des_abs, 0)},
            {"category": "Impacto población absoluto", "metric": "Número de heridos", "unit": "No. hab.", "value": format_number(ip_her_abs, 0)},
             # Impacto humano relativo
            {"category": "Impacto población relativo", "metric": "Número relativo de fallecidos", "unit": "hab./100,000 hab.", "value": format_number(row_data.get('FallecidosRel_Tot', 0) * 100000, 2)},
            {"category": "Impacto población relativo", "metric": "Número relativo de desplazados", "unit": "hab./100,000 hab.", "value": format_number(row_data.get('DesplazadosRel_Tot', 0) * 100000, 2)},
            {"category": "Impacto población relativo", "metric": "Número relativo de heridos", "unit": "hab./100,000 hab.", "value": format_number(row_data.get('HeridosRel_Tot', 0) * 100000, 2)},
             # Pérdidas Económicas
            {"category": "Pérdidas económicas absolutas", "metric": "Pérdida económica", "unit": "Millones de COP", "value": format_number(pe_abs_mill, 2)},
            {"category": "Pérdidas económicas relativas", "metric": "Pérdida económica relativa", "unit": "%", "value": format_number(pe_rel, 2)},
        ]
        
        # Prepare grouped rows
        df_table = pd.DataFrame(detailed_table_data)
        category_counts = df_table['category'].value_counts().to_dict()
        
        table_rows = []
        last_category = None
        
        for i, row in enumerate(detailed_table_data):
            current_category = row['category']
            is_new_category = (current_category != last_category)
            
            # Row styling
            row_style = {}
            if i % 2 == 0:
                row_style['backgroundColor'] = 'white'
            else:
                 row_style['backgroundColor'] = '#f8f9fa' # Alternate color
            
            cells = []
            
            # Category Cell (only if new category)
            if is_new_category:
                row_span = category_counts[current_category]
                cells.append(html.Td(current_category, rowSpan=row_span, style={
                    'fontWeight': 'bold', 
                    'color': '#0a2240', 
                    'borderRight': '1px solid #dee2e6', 
                    'backgroundColor': '#e9ecef', 
                    'verticalAlign': 'middle'
                }))
            
            # Metric, Unit, Value
            cells.extend([
                html.Td(row['metric']),
                html.Td(row['unit'], style={'color': '#666'}),
                html.Td(row['value'], style={'fontWeight': 'bold', 'textAlign': 'right', 'color': '#0a2240'})
            ])

            table_rows.append(html.Tr(cells, style=row_style))
            
            last_category = current_category

        detailed_table = html.Div([
            html.H5("Tabla Detallada de Impacto", className="mb-3", style={'color': '#0a2240', 'fontWeight': 'bold', 'marginTop': '30px'}),
            html.Table([
                html.Thead(
                    html.Tr([
                        html.Th("Categoría"),
                        html.Th("Métrica"),
                        html.Th("Unidad"),
                        html.Th("Valor", style={'textAlign': 'right'}),
                    ])
                ),
                html.Tbody(table_rows)
            ], className='modern-table')
        ], className="mb-5")
        
        content_div = html.Div([
            kpi_exposure,
            kpi_impact,
            detailed_table
        ], style={'maxWidth': '1400px', 'margin': '0 auto', 'padding': '0 20px'})
        
    return html.Div([
        header,
        description_section,
        content_div,
        html.Div(style={'height': '100px'})
    ], style={
        'height': '100vh', 
        'overflowY': 'auto', 
        'backgroundColor': '#f0f2f5', 
        'paddingTop': '180px',
        'paddingBottom': '20px',
        'fontFamily': '"Poppins", sans-serif'
    })
