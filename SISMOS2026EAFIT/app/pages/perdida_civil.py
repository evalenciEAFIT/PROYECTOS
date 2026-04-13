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
    """Lee el archivo de metadatos JSON y retorna la sección descriptiva sobre el análisis de daños estructurales (civil) del municipio."""
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
            
            # 2. Return specific 'civil' dict or empty
            return m_data.get('civil', {})
    except Exception as e:
        print(f"Error loading descriptions: {e}")
    return {}

def get_municipality_data(municipality):
    """Identifica el archivo Excel de resumen global del municipio y extrae la hoja 'curvasag' usada para el análisis de daño completo."""
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
    """Crea una figura interactiva de tasa de excedencia empleando Plotly Express configurada con escalas logarítmicas y umbrales base."""
    if df is None or df.empty:
        return html.Div("No hay datos disponibles para este municipio.", style={'textAlign': 'center', 'padding': '20px'})

    df_plot = df.sort_values('tasa')
    
    # Process relative data if needed
    x_data = df_plot[x_col]
    if is_relative:
        x_data = x_data * 1000 # Scaling by 1000 for per 1k buildings
    
    fig = px.line(x=x_data, y=df_plot['tasa'], log_y=True)
    
    fig.update_traces(
        line_color='#0a2240', 
        line_width=3, 
        name="Curva de excedencia", 
        showlegend=True
    )
    
    # Dummy trace for legend
    fig.add_scatter(
        x=[None], y=[None], 
        mode='lines', 
        line=dict(color='red', dash='dash', width=1), 
        name='Periodo de retorno',
        showlegend=True
    )
    
    # Invisible trace for sync
    fig.add_scatter(
        x=x_data, 
        y=df_plot['tasa'], 
        yaxis='y2', 
        opacity=0, 
        showlegend=False, 
        hoverinfo='skip'
    )

    return_periods = [50, 475, 975]
    for rp in return_periods:
        y_val = 1/rp
        fig.add_hline(y=y_val, line_dash="dash", line_color="red", line_width=1)

    axis_rps = [50, 475, 975]
    tickvals = [1/rp for rp in axis_rps]
    ticktext = [f"<b>{rp}</b>" for rp in axis_rps]

    fig.update_layout(
        title=dict(text=f"<b>{title}</b>", font=dict(size=22, color='#0a2240')),
        xaxis_title=x_label,
        yaxis_title="Tasa de excedencia (1/año)",
        plot_bgcolor='white',
        paper_bgcolor='white',
        margin=dict(l=60, r=60, t=50, b=50),
        legend=dict(x=0.01, y=0.01, xanchor='left', yanchor='bottom', bgcolor='rgba(255,255,255,0.8)'),
        xaxis=dict(
            rangemode='tozero', # Ensure starts at 0
            showgrid=True, 
            gridcolor='#cce5ff', 
            mirror=True, 
            ticks='outside',
            showline=True,
            linecolor='#333'
        ), 
        yaxis=dict(
            type='log', 
            showgrid=True, 
            gridcolor='#cce5ff', 
            minor=dict(showgrid=True, gridcolor='#e6f2ff'), 
            tickformat=".1e", 
            dtick=1, 
            showline=True,
            linecolor='#333',
            mirror=False 
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
            matches='y'
        )
    )
    
    return fig

def create_table(df_in, title, col_abs, col_rel, label_abs):
    """Organiza y extrae las columnas del DataFrame de excedencia hacia un formato amigable para ensamblar una tabla HTML."""
    # Prepare Table Data
    df_table = df_in[['PeriodoRetorno', 'tasa', col_abs, col_rel]].copy()
    
    # Scale relative column by 1000
    df_table[col_rel] = df_table[col_rel] * 1000
    
    df_table.columns = ['Periodo (años)', 'Tasa (1/año)', label_abs, 'Relativo (x 1,000 edif)']
    
    # Formatting
    df_table['Tasa (1/año)'] = df_table['Tasa (1/año)'].apply(lambda x: f"{x:.5f}")
    df_table[label_abs] = df_table[label_abs].apply(lambda x: f"{x:,.2f}")
    df_table['Relativo (x 1,000 edif)'] = df_table['Relativo (x 1,000 edif)'].apply(lambda x: f"{x:,.4f}")

    table_header = [
        html.Thead(html.Tr([html.Th(col) for col in df_table.columns]))
    ]
    table_body = [
        html.Tbody([
            html.Tr([
                html.Td(val) for val in row
            ]) for index, row in df_table.iterrows()
        ])
    ]
    return html.Div([
        html.H5(title, style={'marginTop': '10px', 'marginBottom': '10px', 'color': '#0a2240', 'fontWeight': '600'}),
        html.Table(table_header + table_body, className='modern-table')
    ])

def layout(municipality=None):
    """Establece la disposición principal de la vista de daño físico en edificaciones, aglomerando cabecera y el bloque de gráficos y tablas."""
    if not municipality:
        municipality = "Caucasia" 

    df = get_municipality_data(municipality)
    
    title = "Daño completo"
    
    # Header
    # Header
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

    # Description
    desc_data = get_municipality_description(municipality)
    info_section = html.Div([
        html.H4("Información de análisis", style={'color': '#0a2240', 'marginBottom': '10px'}),
        #html.P("Las curvas de excedencia representan el periodo de retorno de las afectaciones económicas, humanas y estructurales en el lugar de análisis. Es decir, las curvas de excedencia indican con qué frecuencia se espera que ocurran diferentes niveles de afectaciones. Las figuras presentan los valores medios.", style={'textAlign': 'justify', 'color': '#555', 'fontSize': '0.95rem', 'marginBottom': '15px', 'fontStyle': 'italic'}),
        html.P("Número de edificaciones que presentan un estado de daño completo como consecuencia de la sacudida del movimiento del terreno. Algunas de estas edificaciones presentan colapso.", style={'marginBottom': '5px'}),
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

    graphs_content = html.Div()

    if df is not None:
        # Section Header & Description

        
        cat = {
            "name": "Daño completo",
            "col_abs": "DanoCompleto_Tot",
            "col_rel": "DanoCompletoRel_Tot",
            "label_abs": "# Edificaciones",
            "label_rel": "Por cada 1,000 edificaciones"
        }

        # Absolute Chart
        fig_abs = generate_exceedance_chart(
            df, 
            x_col=cat['col_abs'], 
            title="", 
            x_label=cat['label_abs']
        )
        
        # Relative Chart
        fig_rel = generate_exceedance_chart(
            df, 
            x_col=cat['col_rel'], 
            title="", 
            x_label=cat['label_rel'],
            is_relative=True
        )

        # Table
        table_div = create_table(df, f"Tabla de datos - {cat['name']}", cat['col_abs'], cat['col_rel'], cat['label_abs'])

        graphs_content = html.Div([

            html.Div([
                html.Div([dcc.Graph(figure=fig_abs, config={'displayModeBar': True})], className="chart-card chart-container-responsive"),
                html.Div([dcc.Graph(figure=fig_rel, config={'displayModeBar': True})], className="chart-card chart-container-responsive"),
            ], style={'display': 'flex', 'flexWrap': 'wrap', 'gap': '20px', 'padding': '20px 0'}),
            
            html.Details([
                html.Summary(f"Ver tablas de datos", title="Clic para desplegar/ocultar las tablas de datos", style={'cursor': 'pointer', 'color': '#0a2240', 'fontWeight': 'bold'}),
                html.Div(table_div, style={'marginTop': '10px', 'maxHeight': '300px', 'overflowY': 'auto', 'padding': '10px', 'border': '1px solid #eee'})
            ], style={'marginBottom': '20px'})
        ], style={'backgroundColor': 'white', 'padding': '20px', 'borderRadius': '8px', 'marginBottom': '20px', 'boxShadow': '0 2px 4px rgba(0,0,0,0.05)'})
        
    else:
        graphs_content = html.Div([
            html.H3(f"No se encontraron datos de curvas para {data_service.get_municipality_display_name(municipality)}", style={'color': '#d9534f'})
        ], style={'padding': '40px', 'textAlign': 'center'})

    return html.Div([
        header,
        info_section,
        html.Div(graphs_content, style={'padding': '20px'}),
        html.Div(style={'height': '100px'}) # Spacer
    ], className="page-container", style={
        'height': '100vh',
        'overflowY': 'auto',
        'backgroundColor': '#f0f2f5', 
        'paddingTop': '180px',
        'paddingBottom': '20px',
        'fontFamily': '"Poppins", sans-serif'
    })
