import data_service
import glob
import os
import pandas as pd
import numpy as np
import plotly.express as px
from dash import html, dcc

import json

# Data Loading
def get_municipality_description(municipality):
    """Lee el archivo JSON de descripciones para extraer la metodología y fuentes de datos relativas a la pérdida económica del municipio."""
# Definir rutas absolutas
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    DATA_DIR = os.path.join(BASE_DIR, 'data')

    try:
        path = os.path.join(DATA_DIR, "municipio_descriptions.json")
        if os.path.exists(path):
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 1. Get Municipality Entry or Default Entry
            m_data = data.get(municipality, data.get('default', {}))
            
            # 2. Return specific 'economica' dict or empty
            return m_data.get('economica', {})
    except Exception as e:
        print(f"Error loading descriptions: {e}")
    return {}

def get_municipality_data(municipality):
    """Ubica el archivo Excel de resumen para el municipio y extrae la hoja 'curvasag' con datos de pérdida económica agregada."""
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
                file_path = files[0] # Take first match
        
        if file_path:
            # Read 'curvasag' sheet
            df = pd.read_excel(file_path, sheet_name='curvasag')
            return df
            
        return None
    except Exception as e:
        print(f"Error loading data for {municipality}: {e}")
        return None

def generate_exceedance_chart(df, x_col, title, x_label, is_relative=False):
    """Genera la figura interactiva de tasa de excedencia económica con ejes logarítmicos e indicadores de periodo de retorno."""
    if df is None or df.empty:
        return html.Div("No hay datos disponibles para este municipio.", style={'textAlign': 'center', 'padding': '20px'})

    # Prepare Data
    # Sort by Tasa descending (usually it is, but to be sure for plotting lines)
    df_plot = df.sort_values('tasa')
    
    # Create Figure
    # Create Figure with hover data
    fig = px.line(df_plot, x=x_col, y='tasa', log_y=True, hover_data={'PeriodoRetorno': ':.0f'})
    
    # Style Line and Legend Name
    fig.update_traces(
        line_color='#0a2240', 
        line_width=3, 
        name="Curva de excedencia", 
        showlegend=True
    ) # Thicker line, named trace
    
    # Add Legend for Return Periods (Dummy trace)
    fig.add_scatter(
        x=[None], y=[None], 
        mode='lines', 
        line=dict(color='red', dash='dash', width=1), 
        name='Periodo de retorno',
        showlegend=True
    )
    
    # Invisible Dummy Trace to Synchronize yaxis2 range with yaxis
    fig.add_scatter(
        x=df_plot[x_col], 
        y=df_plot['tasa'], 
        yaxis='y2', 
        opacity=0, 
        showlegend=False, 
        hoverinfo='skip'
    )

    # Return Periods to annotate (Lines only)
    return_periods = [50, 475, 975]
    
    for rp in return_periods:
        y_val = 1/rp
        # Add Horizontal Line - RED
        fig.add_hline(y=y_val, line_dash="dash", line_color="red", line_width=1)

    # Secondary Axis Ticks (Return Periods)
    axis_rps = [50, 475, 975]
    tickvals = [1/rp for rp in axis_rps]
    ticktext = [f"<b>{rp}</b>" for rp in axis_rps]

    # Layout Updates
    fig.update_layout(
        title=dict(text=f"<b>{title}</b>", font=dict(size=22, color='#0a2240')),
        xaxis_title=x_label,
        yaxis_title="Tasa de excedencia (1/año)",
        plot_bgcolor='white',
        paper_bgcolor='white',
        margin=dict(l=60, r=60, t=50, b=50), # Reduce right margin as axis takes space
        legend=dict(x=0.01, y=0.01, xanchor='left', yanchor='bottom', bgcolor='rgba(255,255,255,0.8)'), # Position legend
        xaxis=dict(
            rangemode='tozero',
            showgrid=True, 
            gridcolor='#cce5ff', 
            mirror=True, # Show axis on top as well
            ticks='outside',
            showline=True,
            linecolor='#333'
        ), 
        yaxis=dict(
            type='log', # Explicitly set log type
            showgrid=True, 
            gridcolor='#cce5ff', # Blue grid
            minor=dict(showgrid=True, gridcolor='#e6f2ff'), # Lighter blue minor grid
            tickformat=".1e", # Scientific notation with 1 decimal
            dtick=1, # Show tick every power of 10
            showline=True,
            linecolor='#333',
            mirror=False # Right side handled by yaxis2
        ),
        yaxis2=dict(
            title=dict(text="Periodo de retorno (años)", font=dict(color="#d62728")),
            tickfont=dict(color="#d62728"),
            overlaying="y",
            side="right",
            type="log",
            tickmode="array",
            tickvals=tickvals,
            ticktext=ticktext,
            showgrid=False,
            showline=True,
            linecolor='#d62728',
            matches='y' # Force sync with Y axis
        )
    )
    
    return fig

def layout(municipality=None):
    """Construye y organiza el diseño completo de la página de afectaciones económicas, integrando visualizaciones, tablas e información."""
    if not municipality:
        municipality = "Caucasia" # Default fallback for dev

    df = get_municipality_data(municipality)
    
    title = "Pérdida económica"
    
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
        ], style={'maxWidth': '1400px', 'margin': '0 auto', 'padding': '0 20px'})
    ], style={
        'background': 'linear-gradient(135deg, #0a2240 0%, #081a32 100%)',
        'padding': '32px 0',
        'marginBottom': '32px',
        'boxShadow': '0 4px 20px rgba(0,0,0,0.15)',
        'borderBottom': '2px solid #f5c800'
    })

    # Description Section
    desc_data = get_municipality_description(municipality)
    info_section = html.Div([
        html.H4("Información de análisis", style={'color': '#0a2240', 'marginBottom': '10px'}),
        html.P("Costo de reparación de la edificación para todos los niveles de daño directo causados por los sismos (no incluyen consecuencias indirectas que pueden ocurrir después del sismo). Este costo considera que las estructuras deben repararse siguiendo lineamientos de sismo resistencia.", style={'textAlign': 'justify', 'color': '#555', 'fontSize': '0.95rem', 'marginBottom': '15px'}),
        html.Div([
            html.Span([html.B("Metodología: "), desc_data.get('methodology', 'N/A')], style={'marginRight': '20px'}),
            html.Span([html.B("Fuente: "), desc_data.get('source', 'N/A')], style={'marginRight': '20px'}),
            html.Span([html.B("Actualización: "), desc_data.get('last_update', 'N/A')]),
        ], style={'fontSize': '0.9rem', 'color': '#555', 'marginTop': '10px'})
    ], style={
        'backgroundColor': 'white', 
        'padding': '20px 40px', 
        'borderBottom': '1px solid #eee'
    })

    # Charts Section
    if df is not None:
        # Section Header & Description


        # 1. Absolute Loss Chart
        fig_abs = generate_exceedance_chart(
            df, 
            x_col='Perdida_Tot', 
            title="", 
            x_label="Millones de COP"
        )
        
        # 2. Relative Loss Chart
        fig_rel = generate_exceedance_chart(
            df, 
            x_col='PerdidaRel_Tot', 
            title="", 
            x_label="Pérdida relativa (%)",
            is_relative=True
        )
        
        graphs_content = html.Div([

            html.Div([dcc.Graph(figure=fig_abs, config={'displayModeBar': True})], className="chart-card chart-container-responsive"),
            html.Div([dcc.Graph(figure=fig_rel, config={'displayModeBar': True})], className="chart-card chart-container-responsive"),
        ], style={'display': 'flex', 'flexWrap': 'wrap', 'gap': '20px', 'padding': '20px'})
        
        # Data Tables Section
        
        # Helper to create a styled table
        def create_table(df_in, title):
            """Función auxiliar que crea componentes de tabla HTML estilizados para visualizar los datos brutos de pérdidas económicas."""
            table_header = [
                html.Thead(html.Tr([html.Th(col) for col in df_in.columns]))
            ]
            table_body = [
                html.Tbody([
                    html.Tr([
                        html.Td(val) for val in row
                    ]) for index, row in df_in.iterrows()
                ])
            ]
            return html.Div([
                html.H5(title, style={'marginTop': '10px', 'marginBottom': '10px', 'color': '#0a2240', 'fontWeight': '600'}),
                html.Table(table_header + table_body, className='modern-table')
            ])

        # Table 1: Absolute Loss
        df_abs = df[['PeriodoRetorno', 'tasa', 'Perdida_Tot']].copy()
        df_abs.columns = ['Periodo de retorno (años)', 'Tasa de excedencia (1/año)', 'Pérdida absoluta (millones COP)']
        # Format
        df_abs['Tasa de excedencia (1/año)'] = df_abs['Tasa de excedencia (1/año)'].apply(lambda x: f"{x:.5f}")
        df_abs['Pérdida absoluta (millones COP)'] = df_abs['Pérdida absoluta (millones COP)'].apply(lambda x: f"{x:,.0f}")
        
        # Table 2: Relative Loss
        df_rel = df[['PeriodoRetorno', 'tasa', 'PerdidaRel_Tot']].copy()
        df_rel.columns = ['Periodo de retorno (años)', 'Tasa de excedencia (1/año)', 'Pérdida relativa (%)']
        # Format
        df_rel['Tasa de excedencia (1/año)'] = df_rel['Tasa de excedencia (1/año)'].apply(lambda x: f"{x:.5f}")
        df_rel['Pérdida relativa (%)'] = df_rel['Pérdida relativa (%)'].apply(lambda x: f"{x:.4f}")

        data_details = html.Div([
            html.Details([
                html.Summary("Ver tablas de datos", title="Clic para desplegar/ocultar las tablas de datos", style={
                    'cursor': 'pointer', 
                    'color': '#0a2240', 
                    'fontWeight': 'bold', 
                    'fontSize': '1.1rem',
                    'padding': '10px',
                    'backgroundColor': 'white',
                    'borderRadius': '5px',
                    'border': '1px solid #ddd',
                    'width': 'fit-content'
                }),
                html.Div([
                    html.Div(create_table(df_abs, "Datos - Pérdida absoluta"), style={'flex': 1, 'minWidth': '300px', 'maxHeight': '400px', 'overflowY': 'auto'}),
                    html.Div(create_table(df_rel, "Datos - Pérdida relativa"), style={'flex': 1, 'minWidth': '300px', 'maxHeight': '400px', 'overflowY': 'auto'}),
                ], style={
                    'display': 'flex',
                    'flexWrap': 'wrap',
                    'gap': '20px',
                    'backgroundColor': 'white', 
                    'padding': '15px', 
                    'marginTop': '10px', 
                    'borderRadius': '10px',
                    'boxShadow': '0 4px 15px rgba(0,0,0,0.05)',
                })
            ], style={'padding': '0 20px 20px 20px'})
        ])
        
        graphs_content = html.Div([graphs_content, data_details])
        
    else:
        graphs_content = html.Div([
            html.H3(f"No se encontraron datos de curvas para {data_service.get_municipality_display_name(municipality)}", style={'color': '#d9534f'})
        ], style={'padding': '40px', 'textAlign': 'center'})

    return html.Div([
        header,
        info_section,
        graphs_content,
        html.Div(style={'height': '200px', 'width': '100%'}) # Explicit spacer to clear footer
    ], className="page-container", style={
        'height': '100vh', # Use fixed height to enable internal scroll
        'overflowY': 'auto', # Enable vertical scrolling for the page
        'backgroundColor': '#f0f2f5', 
        'paddingBottom': '20px', 
        'paddingTop': '180px', # Add top padding to clear floating header
        'fontFamily': '"Poppins", sans-serif'
    })
