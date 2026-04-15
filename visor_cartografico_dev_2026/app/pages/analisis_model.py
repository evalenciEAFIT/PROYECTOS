import dash
from dash import dcc, html, Input, Output, State, callback, ALL, MATCH, dash_table
import dash_bootstrap_components as dbc
import pandas as pd
import plotly.graph_objects as go
import data_service
import json
import dash_leaflet as dl

# =============================================================================
# CONSTANTES Y CONFIGURACIÓN
# =============================================================================
# Definición de estilos globales y temas para los gráficos
CHART_THEME = {
    'background': 'rgba(0,0,0,0)',
    'text_color': '#0a2240',
    'font': 'Poppins, sans-serif',
    'colors': ['#0a2240', '#1f3a5f', '#36537e', '#4e6d9e', '#6888bf'],
    'accent': '#f5c800'
}

GLOSARIO_DATA = {
    "BQ_M": "muros de bahareque",
    "CR_M": "muros de concreto reforzado",
    "CR_PRMM": "pórticos resistentes a momento de concreto reforzado con muros adosados",
    "CR_SC": "sistemas combinados de concreto reforzado",
    "MC_M": "muros de mampostería confinada",
    "MD_M": "muros de madera",
    "MD_PL": "pórticos livianos de madera",
    "MNR_M": "muros de mampostería no reforzada",
    "MR_M": "muros de mampostería reforzada",
    "PR_M": "muros prefabricados",
    "TA_M": "muros de tapia"
}

# Ordenamiento específico para gráficos de distribución de pisos
FLOOR_ORDER = [
    'Edificaciones con 1 piso', 
    'Edificaciones con 2-3 pisos', 
    'Edificaciones con 4-5 pisos', 
    'Edificaciones con 6-10 pisos', 
    'Edificaciones con 11 o más pisos'
]

TAX_ORDER = [
    "BQ_M",
    "CR_M",
    "CR_PRMM",
    "CR_SC",
    "MC_M",
    "MD_M",
    "MD_PL",
    "MNR_M",
    "MR_M",
    "PR_M",
    "TA_M"
]

STYLES = {
    'header_gradient': 'linear-gradient(135deg, #ffffff 0%, #f8f9fa 100%)',
    'kpi_border': 'none',
    'text_color': '#2c3e50',
    'card_shadow': '0 10px 30px -5px rgba(0,0,0,0.05)',
    'card_hover': '0 20px 40px -5px rgba(0,0,0,0.1)',
    'table_header_bg': '#ffffff',
    'data_bar_color': 'rgba(13, 110, 253, 0.15)'
}

# ... (omitted GLOSSARY_DATA) ...

# =============================================================================
# FUNCIONES AUXILIARES DE VISUALIZACIÓN
# =============================================================================

# ... (generate_chart_config and charts) ...

# =============================================================================
# COMPONENTES UI (TARJETAS Y GRÁFICOS)
# =============================================================================

def create_stat_card(title, value, card_id=None):
    """
    Crea una tarjeta KPI (Key Performance Indicator) estilizada.
    Incluye un icono, un título, el valor principal y un tooltip con la definición.
    """
    icon_map = {
        "Total edificaciones": "bx-building",
        "Población total": "bx-user",
        "Valor de reposición": "bx-dollar-circle"
    }
    
    tooltip_map = {
        "Total edificaciones": "Número de edificaciones: Cantidad de edificaciones residenciales a nivel del municipio. Una edificación se refiere a una estructura que contiene una o más viviendas.",
        "Población total": "Número de habitantes del municipio.",
        "Valor de reposición": "Valor económico total de las edificaciones residenciales del municipio (componentes estructurales y no estructurales). Representa el costo de reconstrucción bajo la normativa sismo-resistente vigente."
    }
    
    icon = icon_map.get(title, "bx-stats")
    tooltip_text = tooltip_map.get(title, "")
    
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
            
            # Column 2: Content (Title, Value, Description)
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
                    # Value
                    html.H2(value, style={
                        'color': '#0a2240', 
                        'fontSize': '1.8rem', 
                        'fontWeight': '700',
                        'fontFamily': "'Poppins', sans-serif",
                        'margin': '0 0 12px 0',
                        'lineHeight': '1.1',
                        'wordBreak': 'break-word'
                    }),
                    # Description
                    html.P(tooltip_text, style={
                        'fontSize': '0.8rem',
                        'color': '#64748b',
                        'lineHeight': '1.5',
                        'marginBottom': '0'
                    })
                ], style={'display': 'flex', 'flexDirection': 'column'}),
                className="ps-3"
            )
        ], className="g-0 align-items-start h-100"),
        
    ], className="kpi-card p-4 h-100", 
       id=card_id,
       style={
           'backgroundColor': 'white', 
           'borderRadius': '16px', 
           'boxShadow': '0 4px 6px -1px rgba(0, 0, 0, 0.05)',
           'border': '1px solid #f1f5f9',
           'position': 'relative',
           'transition': 'all 0.3s ease'
       })
    
    return card_content

def generate_html_distribution(title, data_dict):
    numeric_items = {k: v for k, v in data_dict.items() if isinstance(v, (int, float))}
    
    if "Edificaciones con 1 piso" in numeric_items:
         order = [
             'Edificaciones con 1 piso', 
             'Edificaciones con 2-3 pisos', 
             'Edificaciones con 4-5 pisos', 
             'Edificaciones con 6-10 pisos', 
             'Edificaciones con 11 o más pisos'
         ]
         sorted_items = [(k, numeric_items.get(k, 0)) for k in order if k in numeric_items]
    else:
        sorted_items = sorted(numeric_items.items(), key=lambda x: x[1], reverse=True)
        
    total = sum(numeric_items.values())
    rows = []
    
    for label, value in sorted_items:
        pct = (value / total * 100) if total > 0 else 0
        rows.append(html.Div([
            html.Div([
                html.Span(label, className="fw-bold", style={'fontSize': '0.85rem', 'color': '#333'}),
                html.Span(f"{int(value):,} ({pct:.1f}%)".replace(",", "."), style={'fontSize': '0.85rem', 'color': '#555'})
            ], className="d-flex justify-content-between mb-1"),
            html.Div([
                html.Div(style={
                    'width': f'{pct}%', 'height': '6px',
                    'background': 'linear-gradient(90deg, #0d6efd 0%, #6ea8fe 100%)',
                    'borderRadius': '6px', 'boxShadow': '0 1px 2px rgba(13, 110, 253, 0.2)'
                })
            ], style={'width': '100%', 'backgroundColor': '#f1f3f5', 'borderRadius': '6px', 'height': '6px', 'marginBottom': '16px'})
        ]))
        
    return html.Div([
        html.H6(title, className="fw-bold mb-3", style={'color': '#2c3e50', 'fontSize': '1rem', 'letterSpacing': '0.3px'}),
        html.Div(rows)
    ])

# =============================================================================
# MODULOS DE LAYOUT (SECCIONES DE LA PÁGINA)
# =============================================================================

def create_header(municipality):
    """Genera el encabezado de la página con el nombre del municipio."""
    return html.Div([
        html.Div([
            html.Div([
                html.Div([
                    html.H1(f"Análisis de Exposición", style={
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

def create_description_section():
    """Genera una alerta informativa sobre el contenido del panel."""
    return dbc.Alert([
        html.Div([
            html.I(className="bx bx-info-circle", style={'fontSize': '1.5rem', 'marginRight': '12px', 'color': '#0284c7'}),
            html.Span("Este panel presenta un análisis detallado del modelo de exposición, incluyendo estadísticas agregadas y distribuciones por características estructurales.", 
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

def create_kpi_section(totals):
    """Genera la fila de tarjetas KPI con los totales del municipio."""
    total_edificios = totals.get('NumeroEdificios', 0)
    total_poblacion = totals.get('Ocupacion', 0)
    total_valor = totals.get('ValorReposicion', 0)
    
    formatted_valor = f"${total_valor:,.0f}".replace(",", ".")
    formatted_edificios = f"{total_edificios:,.0f}".replace(",", ".")
    formatted_poblacion = f"{total_poblacion:,.0f}".replace(",", ".")
    
    return html.Div([
        dbc.Row([
            dbc.Col(create_stat_card("Total edificaciones", formatted_edificios, "edificios"), md=4, className="mb-4 animate-in"),
            dbc.Col(create_stat_card("Población total", formatted_poblacion, "poblacion"), md=4, className="mb-4 animate-in"),
            dbc.Col(create_stat_card("Valor de reposición", formatted_valor, "valor"), md=4, className="mb-4 animate-in"),
        ], className="g-4")
    ], style={'marginBottom': '32px'})

def generate_horizontal_bar_chart(data_dict, title, height=320, manual_order=None):
    """Genera un gráfico de barras horizontales usando Plotly Graph Objects."""
    numeric_items = {k: v for k, v in data_dict.items() if isinstance(v, (int, float))}
    
    if manual_order:
        # Sort based on provided list, treat missing keys as 0 if needed or just skip
        # We perform a safe get, defaulting to 0 for keys in manual_order
        sorted_items = []
        for k in manual_order:
            # Only include if in data_dict or if we want to show zeros (user implied specific list)
            # Let's include them even if 0 to maintain consistent layout
            val = numeric_items.get(k, 0)
            sorted_items.append((k, val))
    else:
        sorted_items = sorted(numeric_items.items(), key=lambda x: x[1], reverse=True)
    
    labels = [k for k, v in sorted_items]
    values = [v for k, v in sorted_items]
    total = sum(numeric_items.values())

    n_items = len(values)
    dynamic_height = max(height, n_items * 36 + 70)
    
    n_bars = len(values)
    colors = []
    for i in range(n_bars):
        ratio = i / max(n_bars - 1, 1) if n_bars > 1 else 0
        
        # All Blue Gradient (Navy to Light Blue)
        # Navy: 10, 34, 64
        # Light Blue: 78, 109, 158
        
        r = int(10 + (78 - 10) * ratio)
        g = int(34 + (109 - 34) * ratio)
        b = int(64 + (158 - 64) * ratio)
        
        colors.append(f'rgb({r},{g},{b})')
        
    text_vals = [f"{v:,.0f} ({(v/total*100):.1f}%)" if total > 0 else "0 (0.0%)" for v in values]
    
    # Prepare customdata for tooltip (Full Name)
    # If the key exists in GLOSARIO_DATA, use it, otherwise use the label itself
    custom_data = [GLOSARIO_DATA.get(label, label) for label in labels]

    fig = go.Figure(data=[
        go.Bar(
            y=labels, 
            x=values,
            orientation='h',
            text=text_vals,
            customdata=custom_data,
            textposition='inside',
            insidetextanchor='start',
            textfont=dict(size=11, color='white', family='Poppins, sans-serif', weight=600),
            marker=dict(
                color=colors, 
                line=dict(width=0),
                cornerradius=5
            ),
            hovertemplate='<b>%{customdata}</b><br>Cantidad: %{x:,.0f}<br>Porcentaje: %{text}<extra></extra>'
        )
    ])
    
    fig.update_layout(
        title=dict(
            text=f"<b>{title}</b>" if title else None, 
            x=0.02, 
            xanchor='left', 
            font=dict(size=13, color="#1e293b", family='Poppins, sans-serif')
        ) if title else None,
        showlegend=False,
        height=dynamic_height,
        bargap=0.22,
        margin=dict(l=5, r=25, t=45 if title else 12, b=12),
        xaxis=dict(visible=False, showgrid=False, zeroline=False),
        yaxis=dict(
            autorange="reversed", 
            showgrid=False, 
            tickfont=dict(size=11, color='#334155', family='Poppins, sans-serif', weight=500),
            tickmode='linear',
            ticklabelposition='outside left'
        ),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(family='Poppins, sans-serif'),
        hoverlabel=dict(
            bgcolor='#0f172a',
            font_size=12,
            font_family='Poppins, sans-serif',
            font_color='white',
            bordercolor='#f5c800'
        )
    )
    return dcc.Graph(figure=fig, config={'displayModeBar': False}, style={'borderRadius': '10px', 'height': f'{dynamic_height}px'})


def create_charts_section(floor_data, tax_data):
    """Genera una sección que combina gráficos descriptivos e información tabulada sobre la distribución de pisos y taxonomías estructurales."""
     # Create Glossary Tooltip Content
    glossary_items = [html.H6("GLOSARIO DE MACRO-TAXONOMÍAS", style={'color': '#f5c800', 'fontWeight': 'bold', 'marginBottom': '10px', 'fontSize': '0.9rem', 'borderBottom': '1px solid rgba(255,255,255,0.2)', 'paddingBottom': '5px'})]
    
    glossary_items.extend([html.Div([
        html.Span(f"{k}: ", style={'fontWeight': 'bold', 'color': '#fff'}),
        html.Span(v, style={'color': '#ccc'})
    ], style={'fontSize': '0.8rem', 'marginBottom': '4px', 'textAlign': 'left'}) for k, v in GLOSARIO_DATA.items()])

    return dbc.Card([
        dbc.CardBody([
            html.Div([
                html.H4("Distribución característica", className="mb-0", style={'color': '#0a2240', 'fontWeight': 'bold', 'fontFamily': "'Poppins', sans-serif"}),
            ], className="d-flex align-items-center mb-4"),

            html.Div([
                html.Div(generate_horizontal_bar_chart(floor_data, "Por pisos", height=320, manual_order=FLOOR_ORDER), 
                         className="p-3 h-100", 
                         style={'backgroundColor': 'white', 'borderRadius': '16px', 'boxShadow': STYLES['card_shadow']}),
                html.Div([
                     # Custom Header with Icon and Chart
                     html.Div([
                         html.Div([
                            html.H5("Por taxonomía (Global)", style={'color': '#1e293b', 'fontWeight': 'bold', 'fontSize': '13px', 'margin': '0', 'fontFamily': "'Poppins', sans-serif"}),
                            html.I(className="bx bx-info-circle", id="tax-glossary-target", style={'fontSize': '1.1rem', 'color': '#0a2240', 'cursor': 'pointer', 'marginLeft': '6px'}),
                            dbc.Tooltip(
                                glossary_items,
                                target="tax-glossary-target",
                                placement="left",
                                style={'backgroundColor': 'rgba(10, 34, 64, 0.98)', 'color': 'white', 'padding': '15px', 'borderRadius': '8px', 'boxShadow': '0 8px 32px rgba(0,0,0,0.3)', 'maxWidth': '350px'}
                            )
                         ], style={'display': 'flex', 'alignItems': 'center', 'marginBottom': '10px', 'marginLeft': '5px'}),
                         
                         generate_horizontal_bar_chart(tax_data, None, height=320, manual_order=TAX_ORDER)
                     ], className="p-3 mb-3", style={'backgroundColor': 'white', 'borderRadius': '16px', 'boxShadow': STYLES['card_shadow']})
                ])
            ], style={'display': 'grid', 'gridTemplateColumns': 'repeat(auto-fit, minmax(400px, 1fr))', 'gap': '24px', 'marginBottom': '20px'})
        ])
    ], className="shadow-none border-0 mb-4 bg-transparent", style={'marginTop': '20px'})


def create_manzana_table_section(manzanas_list):
    """
    Crea la tabla interactiva (Dash DataTable) con el detalle por manzana.
    Configura columnas, formatos numéricos, estilos condicionales y tooltips.
    """
    if not manzanas_list:
        return html.Div()
    
    # Prepare sorted taxonomy keys for consistent column order
    tax_keys = sorted(GLOSARIO_DATA.keys())

    # Define columns with custom formatting
    columns = [
        {
            'name': ['', 'Manzana'], 
            'id': 'manzana',
            'type': 'text',
            'presentation': 'markdown'
        },
        {
            'name': ['Totales', 'Edificios'], 
            'id': 'edificios',
            'type': 'numeric',
            'format': {'specifier': ',.0f', 'locale': {'group': '.', 'decimal': ','}}
        },
        {
            'name': ['Totales', 'Población'], 
            'id': 'poblacion',
            'type': 'numeric',
            'format': {'specifier': ',.0f', 'locale': {'group': '.', 'decimal': ','}}
        },
        {
            'name': ['Totales', 'Valor ($)'], 
            'id': 'valor',
            'type': 'numeric',
            'format': {'specifier': '$,.0f', 'locale': {'group': '.', 'decimal': ','}}
        },
        {
            'name': ['Distribución Pisos', 'Edificaciones con 1 piso'], 
            'id': 'pisos_1',
            'type': 'numeric'
        },
        {
            'name': ['Distribución Pisos', 'Edificaciones con 2-3 pisos'], 
            'id': 'pisos_2_3',
            'type': 'numeric'
        },
        {
            'name': ['Distribución Pisos', 'Edificaciones con 4-5 pisos'], 
            'id': 'pisos_4_5',
            'type': 'numeric'
        },
        {
            'name': ['Distribución Pisos', 'Edificaciones con 6-10 pisos'], 
            'id': 'pisos_6_10',
            'type': 'numeric'
        },
        {
            'name': ['Distribución Pisos', 'Edificaciones con 11 o más pisos'], 
            'id': 'pisos_11_mas',
            'type': 'numeric'
        }
    ]
    
    # Add Taxonomy Columns dynamically
    TAX_HEADERS = {
        "BQ_M": "BQ_M: muros de bahareque",
        "CR_M": "CR_M: muros de concreto reforzado",
        "CR_PRMM": "CR_PRMM: pórticos resistentes a momento de concreto reforzado con muros adosados",
        "CR_SC": "CR_SC: sistemas combinados de concreto reforzado",
        "MC_M": "MC_M: muros de mampostería confinada",
        "MD_M": "MD_M: muros de madera",
        "MD_PL": "MD_PL: pórticos livianos de madera",
        "MNR_M": "MNR_M: muros de mampostería no reforzada",
        "MR_M": "MR_M: muros de mampostería reforzada",
        "PR_M": "PR_M: muros prefabricados",
        "TA_M": "TA_M: muros de tapia"
    }

    header_tooltips = {}

    for key in tax_keys:
        col_id = f'tax_{key}'
        # Use Short Name in Header
        columns.append({
            'name': ['Distribución Taxonomía', key],
            'id': col_id,
            'type': 'numeric'
        })
        # Use Long Name in Tooltip
        header_tooltips[col_id] = {
            'value': TAX_HEADERS.get(key, key),
            'type': 'markdown'
        }

    # Prepare data for DataTable
    table_data = []
    for idx, manzana in enumerate(manzanas_list):
        manz_id = manzana.get('manz_ccnct', f'MZ-{idx}')
        num_edificios = manzana.get('NumeroEdificios', 0)
        poblacion = manzana.get('Ocupacion', 0)
        valor = manzana.get('ValorReposicion', 0)
        
        # Calculate percentages for visual bars
        pisos_1 = manzana.get('pisos_1', 0)
        pisos_2_3 = manzana.get('pisos_2_3', 0)
        pisos_4_5 = manzana.get('pisos_4_5', 0)
        pisos_6_10 = manzana.get('pisos_6_10', 0)
        pisos_11_mas = manzana.get('pisos_11_mas', 0)
        
        row_data = {
            'id': idx,
            'manzana': manz_id,
            'edificios': int(num_edificios),
            'poblacion': int(poblacion),
            'valor': int(valor),
            'pisos_1': int(pisos_1),
            'pisos_2_3': int(pisos_2_3),
            'pisos_4_5': int(pisos_4_5),
            'pisos_6_10': int(pisos_6_10),
            'pisos_11_mas': int(pisos_11_mas)
        }
        
        # Add taxonomy fields
        for k in tax_keys:
            # Note: tax keys in data service usually come as tax_BQ_M
            # We already use the same ID logic for columns: tax_{key}
            val = manzana.get(f"tax_{k}", 0)
            row_data[f"tax_{k}"] = int(val)
            
        table_data.append(row_data)

    # Base Conditional Styles
    data_conditional = [
        # Zebra striping
        {
            'if': {'row_index': 'odd'},
            'backgroundColor': '#fafbfc'
        },
        # Hover effect
        {
            'if': {'state': 'active'},
            'backgroundColor': '#f0f9ff',
            'border': '1px solid #0d6efd'
        },
        # Highlight edificios column
        {
            'if': {'column_id': 'edificios'},
            'fontWeight': '600',
            'color': '#0a2240'
        },
        # Highlight high values in pisos columns
        {
            'if': {
                'filter_query': '{pisos_1} > 50',
                'column_id': 'pisos_1'
            },
            'backgroundColor': 'rgba(13, 110, 253, 0.15)',
            'fontWeight': '600',
            'color': '#0a2240'
        },
        {
            'if': {
                'filter_query': '{pisos_2_3} > 50',
                'column_id': 'pisos_2_3'
            },
            'backgroundColor': 'rgba(13, 110, 253, 0.15)',
            'fontWeight': '600',
            'color': '#0a2240'
        },
        {
            'if': {
                'filter_query': '{pisos_4_5} > 50',
                'column_id': 'pisos_4_5'
            },
            'backgroundColor': 'rgba(13, 110, 253, 0.15)',
            'fontWeight': '600',
            'color': '#0a2240'
        },
        {
            'if': {
                'filter_query': '{pisos_6_10} > 50',
                'column_id': 'pisos_6_10'
            },
            'backgroundColor': 'rgba(13, 110, 253, 0.15)',
            'fontWeight': '600',
            'color': '#0a2240'
        },
        {
            'if': {
                'filter_query': '{pisos_11_mas} > 50',
                'column_id': 'pisos_11_mas'
            },
            'backgroundColor': 'rgba(13, 110, 253, 0.15)',
            'fontWeight': '600',
            'color': '#0a2240'
        }
    ]
    
    # Add conditional formatting for Taxonomy columns
    for key in tax_keys:
        col_id = f'tax_{key}'
        data_conditional.append({
            'if': {
                'filter_query': f'{{{col_id}}} > 10', # Highlight significant values
                'column_id': col_id
            },
            'backgroundColor': 'rgba(13, 110, 253, 0.1)', # Light blue
            'fontWeight': '600',
            'color': '#0a2240'
        })

    return dbc.Card([
        dbc.CardBody([
            # Header
            html.Div([
                html.Div([
                    html.I(className="bx bx-table", style={'fontSize': '1.8rem', 'color': '#f5c800', 'marginRight': '12px'}),
                    html.Div([
                        html.H4("Detalle por Manzana", className="mb-0", style={'color': '#0a2240', 'fontWeight': 'bold', 'fontFamily': "'Poppins', sans-serif"}),
                        html.Span(f"{len(manzanas_list)} manzanas registradas", style={'fontSize': '0.85rem', 'color': '#64748b', 'fontWeight': '500'})
                    ])
                ], style={'display': 'flex', 'alignItems': 'center'}),
                
            ], className="d-flex justify-content-between align-items-center mb-4"),
            
            # DataTable
            dash_table.DataTable(
                id='manzanas-table',
                columns=columns,
                data=table_data,
                
                # Styling
                style_table={
                    'overflowX': 'auto',
                    'borderRadius': '12px',
                    'boxShadow': '0 2px 8px rgba(10, 34, 64, 0.1)',
                    'border': '1px solid rgba(10, 34, 64, 0.1)'
                },
                style_header={
                    'backgroundColor': '#f8f9fa',
                    'fontWeight': '700',
                    'fontSize': '0.75rem',
                    'color': '#0a2240',
                    'textAlign': 'center',
                    'padding': '12px 8px',
                    'borderBottom': '1px solid #dee2e6',
                    'textTransform': 'uppercase',
                    'letterSpacing': '0.5px',
                    'fontFamily': "'Poppins', sans-serif"
                },
                style_cell={
                    'textAlign': 'center',
                    'padding': '12px 8px',
                    'fontSize': '0.85rem',
                    'fontFamily': "'Poppins', sans-serif",
                    'borderBottom': '1px solid #f1f5f9',
                    'whiteSpace': 'normal',
                    'height': 'auto',
                    'minWidth': '80px'
                },
                style_data={
                    'backgroundColor': 'white',
                    'color': '#334155'
                },
                style_cell_conditional=[
                    {
                        'if': {'column_id': 'manzana'},
                        'textAlign': 'left',
                        'fontWeight': '600',
                        'color': '#0a2240',
                        'minWidth': '120px'
                    }
                ],
                style_data_conditional=data_conditional,
                
                # Interactivity
                sort_action='native',
                sort_mode='multi',
                filter_action='native',
                page_action='native',
                page_size=15,
                page_current=0,
                
                # Selection
                row_selectable='single',
                selected_rows=[],
                
                # Merge duplicate headers
                merge_duplicate_headers=True,
                
                # Tooltip
                tooltip_data=[
                    {
                        'manzana': {'value': f"Código: {row['manzana']}", 'type': 'markdown'},
                    } for row in table_data
                ],
                # Tooltip for Headers
                tooltip_header=header_tooltips,
                tooltip_duration=None,
                
                # CSS
                css=[
                    {
                        'selector': '.dash-table-tooltip',
                        'rule': 'background-color: #0f172a; color: white; font-size: 0.85rem; padding: 8px 12px; border-radius: 6px;'
                    }
                ]
            ),
            
            # Selected row details (expandable)
            html.Div(id='manzana-detail-container', style={'marginTop': '24px'})
            
        ], style={'padding': '24px'})
    ], style={
        'backgroundColor': 'white', 
        'borderRadius': '18px', 
        'boxShadow': '0 10px 40px -10px rgba(0,0,0,0.08)',
        'border': '1px solid rgba(0,0,0,0.04)',
        'marginTop': '24px'
    })





# =============================================================================
# EXPORTACIÓN DEL LAYOUT PRINCIPAL
# =============================================================================

def layout(municipality):
    """
    Función principal llamada por app.py para renderizar la página.
    Orquesta la carga de datos y la composición de todas las secciones.
    """
    if not municipality:
        return html.Div(
            html.Div([
                html.I(className="bx bx-error-circle mb-3", style={"fontSize": "4rem", "color": "#cbd5e0"}),
                html.H3("Seleccione un municipio", className="text-muted")
            ], className="d-flex flex-column align-items-center justify-content-center h-100"),
            className="p-5", style={"height": "80vh"}
        )

    data, manzanas_list = process_report_data(municipality)
    
    if not data:
         return html.Div([
             dbc.Alert([
                 html.I(className="bx bx-error-circle", style={'fontSize': '1.5rem', 'marginRight': '12px'}),
                 html.Span(f"No hay datos de exposición disponibles para {data_service.get_municipality_display_name(municipality)}.")
             ], color="warning", className="d-flex align-items-center")
         ], className="p-4")
    
    if 'error' in data:
         return html.Div([
             dbc.Alert([
                 html.I(className="bx bx-error", style={'fontSize': '1.5rem', 'marginRight': '12px'}),
                 html.Span(f"Error: {data['error']}")
             ], color="danger", className="d-flex align-items-center")
         ], className="p-4")

    # Layout Components
    header_section = create_header(municipality)
    desc_section = create_description_section()
    kpi_section = create_kpi_section(data['totals'])
    charts_section = create_charts_section(data['floor_data'], data['tax_data'])
    manzana_table_section = create_manzana_table_section(manzanas_list)
    
    # Store municipality and manzanas data for callbacks
    mun_store = dcc.Store(id='analisis-municipality-store', data=municipality)
    manzanas_store = dcc.Store(id='analisis-manzanas-store', data=manzanas_list)

    return html.Div([
        mun_store,
        manzanas_store,
        header_section,
        desc_section,
        
        # Main content container
        html.Div([
            html.Div(kpi_section, style={'maxWidth': '1400px', 'margin': '0 auto'}),
            html.Div(charts_section, style={'maxWidth': '1400px', 'margin': '0 auto'}),
            html.Div(manzana_table_section, style={'maxWidth': '1400px', 'margin': '0 auto'}),
            html.Div(style={'height': '150px'}) # Bottom Margin Spacer
        ], className="px-4", id="analisis-content-container"),
        
        # Scroll to top button
        html.Button([
            html.I(className="bx bx-chevron-up", style={'fontSize': '1.5rem'})
        ], 
        id='scroll-to-top-btn',
        className='scroll-to-top-btn',
        style={
            'position': 'fixed',
            'bottom': '30px',
            'right': '30px',
            'width': '50px',
            'height': '50px',
            'borderRadius': '50%',
            'backgroundColor': '#10b981',
            'color': 'white',
            'border': 'none',
            'boxShadow': '0 4px 20px rgba(16, 185, 129, 0.4)',
            'cursor': 'pointer',
            'display': 'none',  # Hidden by default, shown via clientside callback
            'alignItems': 'center',
            'justifyContent': 'center',
            'transition': 'all 0.3s ease',
            'zIndex': '1000'
        })
        
    ], style={
        'height': '100vh', 
        'overflowY': 'auto', 
        'backgroundColor': '#f0f2f5', 
        'paddingTop': '180px',
        'paddingBottom': '20px',
        'fontFamily': "'Poppins', sans-serif"
    }, id='analisis-main-container')

def process_report_data(municipality):
    """
    Carga y procesa los datos del reporte desde data_service.
    Prepara estructuras de datos optimizadas para los gráficos (pisos, taxonomía).
    """
    json_data = data_service.get_summary_report_data(municipality)
    if not json_data:
        return None, None
        
    try:
        report = json.loads(json_data)
        if 'error' in report:
            return {'error': report['error']}, None
            
        totals = report.get('totals', {})
        manzanas_list = report.get('manzanas', [])
        
        # Process Floor Data
        floor_keys = ['pisos_1', 'pisos_2_3', 'pisos_4_5', 'pisos_6_10', 'pisos_11_mas']
        floor_labels = [
            'Edificaciones con 1 piso', 
            'Edificaciones con 2-3 pisos', 
            'Edificaciones con 4-5 pisos', 
            'Edificaciones con 6-10 pisos', 
            'Edificaciones con 11 o más pisos'
        ]
        floor_data = {lbl: totals.get(key, 0) for key, lbl in zip(floor_keys, floor_labels)}

        # Process Taxonomy Data (Strictly User Glossary)
        tax_data = {}
        for k in GLOSARIO_DATA.keys():
            # Match keys from data service which usually have 'tax_' prefix
            data_key = f"tax_{k}"
            val = totals.get(data_key, 0)
            # Use Key (BQ_M) as label as requested implicitly by having a separate glossary
            tax_data[k] = val
                 
        return {
            'totals': totals,
            'floor_data': floor_data,
            'tax_data': tax_data
        }, manzanas_list
        
    except Exception as e:
        return {'error': str(e)}, None

# =============================================================================
# REGISTRO DE CALLBACKS
# =============================================================================

def register_callbacks(app):
    """Registra los callbacks específicos de esta página en la app principal."""
    # Callback for showing detailed charts when a row is selected
    @app.callback(
        Output('manzana-detail-container', 'children'),
        [Input('manzanas-table', 'selected_rows'),
         Input('manzanas-table', 'data')],
        [State('analisis-municipality-store', 'data')]
    )
    def display_manzana_details(selected_rows, table_data, municipality):
        """Callback que se dispara al seleccionar una fila en la tabla; renderiza detalles estadísticos, gráficas interactivas y un mapa Leaflet para la manzana específica."""
        if not selected_rows or not table_data:
            return html.Div()
        
        # Get the selected row data
        selected_idx = selected_rows[0]
        selected_manzana = table_data[selected_idx]
        
        # Get full manzana data from store
        manz_id = selected_manzana['manzana']
        
        # Prepare floor data for chart
        floor_data = {
            'Edificaciones con 1 piso': selected_manzana.get('pisos_1', 0),
            'Edificaciones con 2-3 pisos': selected_manzana.get('pisos_2_3', 0),
            'Edificaciones con 4-5 pisos': selected_manzana.get('pisos_4_5', 0),
            'Edificaciones con 6-10 pisos': selected_manzana.get('pisos_6_10', 0),
            'Edificaciones con 11 o más pisos': selected_manzana.get('pisos_11_mas', 0)
        }
        
        # Prepare taxonomy data for chart
        tax_data = {k: 0 for k in GLOSARIO_DATA.keys()} # Initialize with all keys
        for k in GLOSARIO_DATA.keys():
            # Keys in table_data were added with 'tax_' prefix in create_manzana_table_section
            data_key = f"tax_{k}"
            val = selected_manzana.get(data_key, 0)
            if val > 0:
                tax_data[k] = val
        
        # --- Generate Map Component ---
        map_component = html.Div()
        try:
            if municipality:
                gdf = data_service.get_manzanas_geometry(municipality)
                if not gdf.empty:
                    # Filter for selected vs others
                    if 'manz_ccnct' in gdf.columns:
                        gdf['manz_ccnct'] = gdf['manz_ccnct'].astype(str)
                        
                    selected_gdf = gdf[gdf['manz_ccnct'] == str(manz_id)]
                    
                    if not selected_gdf.empty:
                        # Compute bounds/center
                        bounds = selected_gdf.total_bounds
                        
                        # Separate for styling performance (two layers)
                        other_gdf = gdf[gdf['manz_ccnct'] != str(manz_id)]

                        map_bounds = [[float(bounds[1]), float(bounds[0])], [float(bounds[3]), float(bounds[2])]]
                        
                        map_component = html.Div([
                            html.H6("Ubicación Geográfica", style={'fontSize': '0.9rem', 'fontWeight': '600', 'color': '#0a2240', 'marginBottom': '10px', 'fontFamily': "'Poppins', sans-serif"}),
                            dl.Map([
                                dl.LayersControl([
                                    dl.BaseLayer(dl.TileLayer(url="https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png"), name="Claro"),
                                    dl.BaseLayer(dl.TileLayer(url="https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png"), name="Voyager"),
                                    dl.BaseLayer(dl.TileLayer(url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"), name="Oscuro"),
                                    dl.BaseLayer(dl.TileLayer(url="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"), name="Satélite"),
                                    dl.BaseLayer(dl.TileLayer(url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"), name="Geográfico", checked=True),
                                    dl.BaseLayer(dl.TileLayer(url="https://server.arcgisonline.com/ArcGIS/rest/services/World_Street_Map/MapServer/tile/{z}/{y}/{x}"), name="Callejero")
                                ], position="topright"),
                                # Selected Layer Only
                                dl.GeoJSON(
                                    data=json.loads(selected_gdf.to_json()),
                                    style={'color': '#0d6efd', 'weight': 3, 'opacity': 1, 'fillOpacity': 0.6, 'fillColor': '#0d6efd'}
                                )
                            ], bounds=map_bounds, style={'width': '100%', 'height': '350px', 'borderRadius': '12px'}, zoomControl=False)
                        ], className="map-detail-wrapper", style={'marginTop': '20px', 'borderTop': '1px solid #eee', 'paddingTop': '20px'})
        except Exception as e:
            print(f"Error creating detail map: {e}")
            
        return dbc.Card([
            dbc.CardBody([
                html.Div([
                    html.I(className="bx bx-bar-chart", style={'fontSize': '1.5rem', 'color': '#0a2240', 'marginRight': '10px'}),
                    html.H5(f"Detalle de Manzana {manz_id}", style={'margin': '0', 'color': '#0a2240', 'fontWeight': '600', 'fontFamily': "'Poppins', sans-serif"})
                ], style={'display': 'flex', 'alignItems': 'center', 'marginBottom': '20px'}),
                
                # Summary stats
                dbc.Row([
                    dbc.Col([
                        html.Div([
                            html.Div(
                                html.I(className="bx bx-building", style={'fontSize': '1.4rem', 'color': '#0a2240'}),
                                style={'background': 'rgba(10, 34, 64, 0.1)', 'borderRadius': '50%', 'width': '36px', 'height': '36px', 'display': 'flex', 'alignItems': 'center', 'justifyContent': 'center', 'marginRight': '10px'}
                            ),
                            html.Div([
                                html.Div("Edificios", style={'fontSize': '0.75rem', 'color': '#64748b', 'textTransform': 'uppercase', 'fontFamily': "'Poppins', sans-serif"}),
                                html.Div(f"{selected_manzana['edificios']:,}", style={'fontSize': '1.3rem', 'fontWeight': '700', 'color': '#0a2240', 'fontFamily': "'Poppins', sans-serif"})
                            ])
                        ], style={'display': 'flex', 'alignItems': 'center', 'padding': '12px', 'backgroundColor': 'white', 'borderRadius': '10px', 'boxShadow': '0 2px 6px rgba(0,0,0,0.04)'})
                    ], md=4),
                    dbc.Col([
                        html.Div([
                            html.Div(
                                html.I(className="bx bx-user", style={'fontSize': '1.4rem', 'color': '#0a2240'}),
                                style={'background': 'rgba(10, 34, 64, 0.1)', 'borderRadius': '50%', 'width': '36px', 'height': '36px', 'display': 'flex', 'alignItems': 'center', 'justifyContent': 'center', 'marginRight': '10px'}
                            ),
                            html.Div([
                                html.Div("Población", style={'fontSize': '0.75rem', 'color': '#64748b', 'textTransform': 'uppercase', 'fontFamily': "'Poppins', sans-serif"}),
                                html.Div(f"{selected_manzana['poblacion']:,}", style={'fontSize': '1.3rem', 'fontWeight': '700', 'color': '#0a2240', 'fontFamily': "'Poppins', sans-serif"})
                            ])
                        ], style={'display': 'flex', 'alignItems': 'center', 'padding': '12px', 'backgroundColor': 'white', 'borderRadius': '10px', 'boxShadow': '0 2px 6px rgba(0,0,0,0.04)'})
                    ], md=4),
                    dbc.Col([
                        html.Div([
                            html.Div(
                                html.I(className="bx bx-dollar-circle", style={'fontSize': '1.4rem', 'color': '#0a2240'}),
                                style={'background': 'rgba(10, 34, 64, 0.1)', 'borderRadius': '50%', 'width': '36px', 'height': '36px', 'display': 'flex', 'alignItems': 'center', 'justifyContent': 'center', 'marginRight': '10px'}
                            ),
                            html.Div([
                                html.Div("Valor", style={'fontSize': '0.75rem', 'color': '#64748b', 'textTransform': 'uppercase', 'fontFamily': "'Poppins', sans-serif"}),
                                html.Div(f"${selected_manzana['valor']:,.0f}", style={'fontSize': '1.3rem', 'fontWeight': '700', 'color': '#0a2240', 'fontFamily': "'Poppins', sans-serif"})
                            ])
                        ], style={'display': 'flex', 'alignItems': 'center', 'padding': '12px', 'backgroundColor': 'white', 'borderRadius': '10px', 'boxShadow': '0 2px 6px rgba(0,0,0,0.04)'})
                    ], md=4)
                ], className="mb-4"),
                
                # Charts
                dbc.Row([
                    dbc.Col([
                        html.H6("Distribución por Número de Pisos", style={'fontSize': '0.9rem', 'fontWeight': '600', 'color': '#0a2240', 'marginBottom': '16px', 'fontFamily': "'Poppins', sans-serif"}),
                        generate_horizontal_bar_chart(floor_data, "", height=250, manual_order=FLOOR_ORDER)
                    ], md=6),
                    dbc.Col([
                        html.Div([
                            html.H6("Distribución por Taxonomía", style={'fontSize': '0.9rem', 'fontWeight': '600', 'color': '#0a2240', 'margin': '0', 'fontFamily': "'Poppins', sans-serif"}),
                            html.I(className="bx bx-info-circle", id=f"manz-tax-tooltip-{manz_id}", style={'fontSize': '1.2rem', 'color': '#0a2240', 'cursor': 'pointer', 'marginLeft': '8px'}),
                            dbc.Tooltip(
                                [html.H6("GLOSARIO DE MACRO-TAXONOMÍAS", style={'color': '#f5c800', 'fontWeight': 'bold', 'marginBottom': '10px', 'fontSize': '0.9rem', 'borderBottom': '1px solid rgba(255,255,255,0.2)', 'paddingBottom': '5px'})] + 
                                [html.Div([
                                    html.Span(f"{k}: ", style={'fontWeight': 'bold', 'color': '#fff'}),
                                    html.Span(v, style={'color': '#ccc'})
                                ], style={'fontSize': '0.8rem', 'marginBottom': '4px', 'textAlign': 'left'}) for k, v in GLOSARIO_DATA.items()],
                                target=f"manz-tax-tooltip-{manz_id}",
                                placement="left",
                                style={'backgroundColor': 'rgba(10, 34, 64, 0.98)', 'color': 'white', 'padding': '15px', 'borderRadius': '8px', 'boxShadow': '0 8px 32px rgba(0,0,0,0.3)', 'maxWidth': '350px'}
                            )
                        ], style={'display': 'flex', 'alignItems': 'center', 'marginBottom': '16px'}),
                        generate_horizontal_bar_chart(tax_data, "", height=250, manual_order=TAX_ORDER)
                    ], md=6)
                ]),
                
                # Map Section
                map_component
                
            ])
        ], style={
            'backgroundColor': '#fffbf0',
            'border': '2px solid #f5c800',
            'borderRadius': '12px',
            'marginTop': '16px',
            'boxShadow': '0 4px 12px rgba(245, 200, 0, 0.15)'
        })
    
    # Callback for exporting table data

    
    # Clientside callback for scroll-to-top button visibility and functionality
    app.clientside_callback(
        """
        function(n_clicks) {
            const container = document.getElementById('analisis-main-container');
            const button = document.getElementById('scroll-to-top-btn');
            
            if (!container || !button) return window.dash_clientside.no_update;
            
            // Show/hide button based on scroll position
            container.addEventListener('scroll', function() {
                if (container.scrollTop > 300) {
                    button.style.display = 'flex';
                } else {
                    button.style.display = 'none';
                }
            });
            
            // Scroll to top on click
            if (n_clicks) {
                container.scrollTo({
                    top: 0,
                    behavior: 'smooth'
                });
            }
            
            return window.dash_clientside.no_update;
        }
        """,
        Output('scroll-to-top-btn', 'n_clicks'),
        Input('scroll-to-top-btn', 'n_clicks')
    )

