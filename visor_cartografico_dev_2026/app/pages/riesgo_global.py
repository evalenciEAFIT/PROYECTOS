import data_service
import glob
import os
import pandas as pd
import numpy as np
from dash import html, dcc
import plotly.express as px
import plotly.graph_objects as go

# Formatter helper
def format_number(val, decimals=0):
    """Formatea cantidades numéricas insertando separadores de miles y el número dictado de cifras decimales, útil para presentación en KPIs."""
    if pd.isna(val):
        return "N/A"
    try:
        if decimals == 0:
             return f"{val:,.0f}"
        return f"{val:,.{decimals}f}"
    except:
        return str(val)

def get_risk_data(municipality):
    """Obtiene la primera fila de datos de la hoja 'riesgoag' (riesgo global agregado) del archivo de resumen Excel del municipio."""
    try:
        BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        DATA_DIR = os.path.join(BASE_DIR, 'data')
        
        base_path = os.path.join(DATA_DIR, 'municipios', municipality)
        
        # Priority 1: Exact match ResumenTOTAL{Municipality}.xlsx
        target_file = os.path.join(base_path, f"ResumenTOTAL{municipality}.xlsx")
        
        file_path = None
        if os.path.exists(target_file):
            file_path = target_file
        else:
             # Priority 2: Wildcard fallback
            pattern = os.path.join(base_path, f"ResumenTOTAL*{municipality}*.xlsx")
            files = glob.glob(pattern)
            
            if not files:
                 # Priority 3: Any ResumenTOTAL
                 pattern_fallback = os.path.join(base_path, "ResumenTOTAL*.xlsx")
                 files = glob.glob(pattern_fallback)
            
            if files:
                file_path = files[0]

        if file_path:
            # Read 'riesgoag' sheet
            df = pd.read_excel(file_path, sheet_name='riesgoag')
            if not df.empty:
                return df.iloc[0]
                
        return None
    except Exception as e:
        print(f"Error loading risk data for {municipality}: {e}")
        return None

def get_curves_data(municipality):
    """Carga los datos de curvas de excedencia agregadas ('curvasag') desde el archivo Excel del municipio especificado y retorna un DataFrame."""
    try:
        BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        DATA_DIR = os.path.join(BASE_DIR, 'data')
        
        base_path = os.path.join(DATA_DIR, 'municipios', municipality)
        
        # Priority 1: Exact match ResumenTOTAL{Municipality}.xlsx
        target_file = os.path.join(base_path, f"ResumenTOTAL{municipality}.xlsx")
        
        file_path = None
        if os.path.exists(target_file):
            file_path = target_file
        else:
             # Priority 2: Wildcard fallback
            pattern = os.path.join(base_path, f"ResumenTOTAL*{municipality}*.xlsx")
            files = glob.glob(pattern)
            
            if not files:
                 # Priority 3: Any ResumenTOTAL
                 pattern_fallback = os.path.join(base_path, "ResumenTOTAL*.xlsx")
                 files = glob.glob(pattern_fallback)
            
            if files:
                file_path = files[0]

        if file_path:
            # Read 'curvasag' sheet
            df = pd.read_excel(file_path, sheet_name='curvasag')
            return df
        return None
    except Exception as e:
        print(f"Error loading curves data for {municipality}: {e}")
        return None

def generate_exceedance_chart(df, x_col, title, x_label, multiplier=1):
    """Dibuja un gráfico de línea de tipo logarítmico para las curvas de excedencia acoplando una escala multiplicadora opcional."""
    if df is None or df.empty or x_col not in df.columns:
        return html.Div(f"No hay datos para {title}", style={'textAlign': 'center'})

    # Prepare Data
    df_plot = df.sort_values('tasa')
    
    # Scale Data
    df_plot['scaled_val'] = df_plot[x_col] * multiplier
    
    # Create Figure
    fig = px.line(df_plot, x='scaled_val', y='tasa', log_y=True, hover_data={'PeriodoRetorno': ':.0f'})
    
    fig.update_traces(
        line_color='#0a2240', 
        line_width=3, 
        name="Curva Excedencia"
    )

    # Add invisible dummy trace to force yaxis2 to have the same range as yaxis
    fig.add_trace(go.Scatter(
        x=df_plot['scaled_val'],
        y=df_plot['tasa'],
        mode='lines',
        opacity=0,
        hoverinfo='skip',
        yaxis='y2',
        showlegend=False
    ))
    
    # Return Periods lines
    return_periods = [50, 475, 975]
    tickvals = [1/rp for rp in return_periods]
    ticktext = [f"<b>{rp}</b>" for rp in return_periods]
    
    for rp in return_periods:
        fig.add_hline(y=1/rp, line_dash="dash", line_color="red", line_width=1)
        # Add annotation for the line if needed, but axis labels might be enough

    fig.update_layout(
        title=dict(text=f"<b>{title}</b>", font=dict(size=14, color='#0a2240')),
        xaxis_title=x_label,
        yaxis_title="Tasa de excedencia (1/año)",
        plot_bgcolor='white',
        paper_bgcolor='white',
        margin=dict(l=60, r=70, t=50, b=50), # Increased margins for axes
        height=400,
        xaxis=dict(showgrid=True, gridcolor='#eee', zeroline=False),
        yaxis=dict(
            type='log', 
            showgrid=True, 
            gridcolor='#eee',
            tickformat=".1e",
            title_font=dict(color="black"),
            tickfont=dict(color="black")
        ),
        yaxis2=dict(
            title="Periodo de retorno (años)",
            title_font=dict(color="#d62728"), # Red color
            overlaying="y",
            side="right",
            type="log",
            tickmode="array",
            tickvals=tickvals,
            ticktext=ticktext,
            tickfont=dict(color="#d62728"), # Red tick labels
            showgrid=False,
            # matches='y' removed to allow custom tick text/vals
        )
    )
    return dcc.Graph(figure=fig, config={'displayModeBar': False})

def layout(municipality=None):
    """Despliega el layout general para mostrar el riesgo anual promedio (AAL) a nivel municipal usando tarjetas, tablas detalladas y gráficas."""
    if not municipality:
        municipality = "Caucasia" 

    row_data = get_risk_data(municipality)
    curves_df = get_curves_data(municipality)
    
    title = f"Afectaciones anuales promedio a nivel de municipio - {data_service.get_municipality_display_name(municipality)}"
    
import dash_bootstrap_components as dbc

# ... (Imports remain the same) ...

# --- Helper for KPI Cards (Copied/Adapted from Analysis Model) ---
def create_stat_card(title, value, unit, icon, description=None, card_id=None):
    """Genera un componente visual tipo tarjeta (KPI Card) usando Dash Bootstrap para destacar métricas clave de forma atractiva."""
    
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
       id=card_id,
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

# ... (Previous functions) ...

def layout(municipality=None):
    if not municipality:
        municipality = "Caucasia" 

    row_data = get_risk_data(municipality)
    curves_df = get_curves_data(municipality)
    
    title = "Afectaciones anuales promedio a nivel de municipio"
    
    # Header Section (Updated Style)
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
            html.Span("Las afectaciones anuales promedio estiman el impacto esperado cada año. Se calcula sumando el costo de cada evento ponderado por su frecuencia. Esta métrica es clave para la planificación a largo plazo.", 
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

    # --- Summary KPIs Section ---
    table_content = html.Div("No hay datos de resumen disponibles", style={'padding': '20px'})

    if row_data is not None:
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
        # Group 1: Exposure
        kpi_exposure = html.Div([
            html.H5("Exposición", className="mb-3", style={'color': '#0a2240', 'fontWeight': 'bold'}),
            dbc.Row([
                dbc.Col(create_stat_card("Valor Expuesto", format_number(exp_val, 2), "Millones COP", "bx-money", "Valor total de las edificaciones residenciales expuestas", card_id="kpi-exp-val"), md=4, className="mb-4"),
                dbc.Col(create_stat_card("Edificaciones", format_number(exp_edif, 2), "Und", "bx-building", "Total de edificaciones residenciales", card_id="kpi-exp-edif"), md=4, className="mb-4"),
                dbc.Col(create_stat_card("Población", format_number(exp_pob, 2), "Hab", "bx-group", "Total de habitantes expuestos", card_id="kpi-exp-pob"), md=4, className="mb-4"),
            ], className="g-4")
        ], className="mb-4")
        
        # Group 2: Losses & Damages
        kpi_impact = html.Div([
            html.H5("Impacto Anual Promedio (AAL)", className="mb-3", style={'color': '#0a2240', 'fontWeight': 'bold'}),
            dbc.Row([
                dbc.Col(create_stat_card("Pérdida Económica", format_number(pe_abs_mill, 2), "Millones COP", "bx-line-chart", f"Pérdida relativa: {pe_rel:.2f}%", card_id="kpi-imp-pe"), md=6, className="mb-4"),
                dbc.Col(create_stat_card("Daño Completo", format_number(de_abs, 2), "Edificaciones", "bx-home-circle", "Promedio anual de edificaciones con daño completo", card_id="kpi-imp-dc"), md=6, className="mb-4"),
            ], className="g-4"),
            
            dbc.Row([
                dbc.Col(create_stat_card("Fallecidos", format_number(ip_fal_abs, 2), "Pers", "bx-user-x", "Promedio anual de fallecidos", card_id="kpi-imp-fal"), md=4, className="mb-4"),
                dbc.Col(create_stat_card("Heridos", format_number(ip_her_abs, 2), "Pers", "bx-plus-medical", "Promedio anual de heridos", card_id="kpi-imp-her"), md=4, className="mb-4"),
                dbc.Col(create_stat_card("Desplazados", format_number(ip_des_abs, 2), "Pers", "bx-walk", "Promedio anual de desplazados", card_id="kpi-imp-des"), md=4, className="mb-4"),
            ], className="g-4")
        ])
        
        # Detailed Table
        detailed_table_data = [
            # Exposición
            {"category": "Exposición", "metric": "Valor expuesto", "unit": "Millones de COP", "value": format_number(exp_val, 2)},
            {"category": "Exposición", "metric": "Número de edificaciones", "unit": "No.", "value": format_number(exp_edif, 2)},
            {"category": "Exposición", "metric": "Población", "unit": "No. hab.", "value": format_number(exp_pob, 2)},
            # Daño
            {"category": "Daño estructural absoluto", "metric": "Número promedio anual de edificaciones con daño completo", "unit": "No.", "value": format_number(de_abs, 2)},
            {"category": "Daño estructural relativo", "metric": "Número promedio anual relativo de edificaciones con daño completo", "unit": "‰", "value": format_number(row_data.get('DanoCompletoRel_Tot', 0) * 1000, 2)},
             # Impacto humano absoluto
            {"category": "Impacto población absoluto", "metric": "Número promedio anual de fallecidos", "unit": "No. hab.", "value": format_number(ip_fal_abs, 2)},
            {"category": "Impacto población absoluto", "metric": "Número promedio anual de desplazados", "unit": "No. hab.", "value": format_number(ip_des_abs, 2)},
            {"category": "Impacto población absoluto", "metric": "Número promedio anual de heridos", "unit": "No. hab.", "value": format_number(ip_her_abs, 2)},
             # Impacto humano relativo
            {"category": "Impacto población relativo", "metric": "Número promedio anual relativo de fallecidos", "unit": "hab./100,000 hab.", "value": format_number(row_data.get('FallecidosRel_Tot', 0) * 100000, 2)},
            {"category": "Impacto población relativo", "metric": "Número promedio anual relativo de desplazados", "unit": "hab./100,000 hab.", "value": format_number(row_data.get('DesplazadosRel_Tot', 0) * 100000, 2)},
            {"category": "Impacto población relativo", "metric": "Número promedio anual relativo de heridos", "unit": "hab./100,000 hab.", "value": format_number(row_data.get('HeridosRel_Tot', 0) * 100000, 2)},
             # Pérdidas Económicas
            {"category": "Pérdidas económicas absolutas", "metric": "Pérdida promedio anual", "unit": "Millones de COP", "value": format_number(pe_abs_mill, 2)},
            {"category": "Pérdidas económicas relativas", "metric": "Pérdida promedio anual relativa", "unit": "%", "value": format_number(pe_rel, 2)},
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
            
            cells.extend([
                html.Td(row['metric']),
                html.Td(row['unit'], style={'color': '#666'}),
                html.Td(row['value'], style={'fontWeight': 'bold', 'textAlign': 'right', 'color': '#0a2240'})
            ])

            table_rows.append(html.Tr(cells, style=row_style))
            
            last_category = current_category

        detailed_table = html.Div([
            html.H5("Tabla Detallada de Riesgo", className="mb-3", style={'color': '#0a2240', 'fontWeight': 'bold', 'marginTop': '30px'}),
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
        
        table_content = html.Div([
            kpi_exposure,
            kpi_impact,
            detailed_table
        ], style={'maxWidth': '1400px', 'margin': '0 auto', 'padding': '0 20px'})
        
    # --- Charts Section ---
    charts_content = html.Div("No hay datos de curvas disponibles", style={'padding': '20px'})
    
    if curves_df is not None:
        # Generate 10 Charts
        # 1. Pérdidas Económicas
        c1 = generate_exceedance_chart(curves_df, 'Perdida_Tot', "Pérdidas económicas absolutas", "Millones de COP")
        c2 = generate_exceedance_chart(curves_df, 'PerdidaRel_Tot', "Pérdidas económicas relativas", "Pérdida relativa (%)", multiplier=100)
        
        # 2. Fallecidos
        c3 = generate_exceedance_chart(curves_df, 'Fallecidos_Tot', "Fallecidos absolutos", "Número de fallecidos")
        c4 = generate_exceedance_chart(curves_df, 'FallecidosRel_Tot', "Fallecidos relativos", "Fallecidos por 100k hab.", multiplier=100000)
        
        # 3. Heridos
        c5 = generate_exceedance_chart(curves_df, 'Heridos_Tot', "Heridos absolutos", "Número de heridos")
        c6 = generate_exceedance_chart(curves_df, 'HeridosRel_Tot', "Heridos relativos", "Heridos por 100k hab.", multiplier=100000)
        
        # 4. Desplazados
        c7 = generate_exceedance_chart(curves_df, 'Desplazados_Tot', "Desplazados absolutos", "Número de desplazados")
        c8 = generate_exceedance_chart(curves_df, 'DesplazadosRel_Tot', "Desplazados relativos", "Desplazados por 100k hab.", multiplier=100000)
        
        # 5. Edificios Daño Completo
        c9 = generate_exceedance_chart(curves_df, 'DanoCompleto_Tot', "Daño completo absoluto", "Edificaciones")
        c10 = generate_exceedance_chart(curves_df, 'DanoCompletoRel_Tot', "Daño completo relativo", "Daño por mil (‰)", multiplier=1000)
        
        charts_content = html.Div([
            html.H3("Curvas de excedencia", style={'color': '#0a2240', 'marginBottom': '20px', 'marginTop': '40px', 'fontSize': '1.3rem', 'textAlign': 'center'}),
            html.Div([
                html.Div(c1, className="chart-container"), html.Div(c2, className="chart-container"),
                html.Div(c3, className="chart-container"), html.Div(c4, className="chart-container"),
                html.Div(c5, className="chart-container"), html.Div(c6, className="chart-container"),
                html.Div(c7, className="chart-container"), html.Div(c8, className="chart-container"),
                html.Div(c9, className="chart-container"), html.Div(c10, className="chart-container"),
            ], className="charts-grid")
        ], style={'padding': '20px 40px', 'backgroundColor': '#f8f9fa'})

    return html.Div([
        header,
        description_section,
        table_content,
        charts_content,
        html.Div(style={'height': '100px'})
    ], style={
        'height': '100vh', 
        'overflowY': 'auto', 
        'backgroundColor': '#f0f2f5', 
        'paddingTop': '180px',
        'paddingBottom': '20px',
        'fontFamily': '"Poppins", sans-serif'
    })
