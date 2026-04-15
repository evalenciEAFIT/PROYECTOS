# =============================================================================
# LIBRERÍAS DE MANEJO DE DATOS
# =============================================================================
import pandas as pd
import geopandas as gpd
import os
import traceback
import json
import numpy as np

# =============================================================================
# CONFIGURACIÓN DE RUTAS Y CONSTANTES
# =============================================================================
from config import APP_DIR, PROJECT_ROOT, BASE_DATA_PATH, MUNICIPIOS_DICT

def get_municipality_display_name(raw_name):
    """
    Retorna el nombre con la ortografía correcta usando el MUNICIPIOS_DICT.
    Si no existe, retorna el nombre tal cual.
    """
    if not raw_name:
        return raw_name
    return MUNICIPIOS_DICT.get(str(raw_name), str(raw_name))


def get_available_municipios():
    """
    Escanea el directorio 'data/municipios' para encontrar carpetas válidas de municipios.
    Retorna una lista ordenada alfabéticamente de los nombres de carpeta.
    """
    try:
        if not os.path.exists(BASE_DATA_PATH): return []
        municipios = [d for d in os.listdir(BASE_DATA_PATH) if os.path.isdir(os.path.join(BASE_DATA_PATH, d))]
        return sorted(municipios)
    except FileNotFoundError: return []

def get_available_cartographies(municipio_name):
    """
    Busca archivos GeoPackage (.gpkg) dentro de la carpeta del municipio especificado.
    Retorna los tipos de cartografía disponibles (ej. Manzanas, Sectores, etc.) eliminando el sufijo del nombre.
    """
    try:
        municipio_path = os.path.join(BASE_DATA_PATH, municipio_name)
        if not os.path.isdir(municipio_path): return []
        files = os.listdir(municipio_path)
        gpkg_files = [f for f in files if f.endswith('.gpkg')]
        cartographies = [f.replace(municipio_name, '').replace('.gpkg', '') for f in gpkg_files]
        return sorted(cartographies)
    except FileNotFoundError: return []

def get_excel_columns(municipio_name):
    """
    Define la lista estándar de columnas que se espera encontrar o generar en los reportes,
    incluyendo variables principales, rangos de pisos y códigos de taxonomía.
    """
    columnas_principales = ['Ocupacion', 'ValorReposicion', 'NumeroEdificios']
    columnas_pisos = ['pisos_1', 'pisos_2_3', 'pisos_4_5', 'pisos_6_10', 'pisos_11_mas']
    columnas_taxonomia = ['tax_BQ_M', 'tax_CR_M', 'tax_CR_PRM', 'tax_CR_PRMM', 'tax_CR_SC', 'tax_MC_M', 'tax_MD_M', 'tax_MD_PL', 'tax_MNR_M', 'tax_MNR+P_M', 'tax_MR_M', 'tax_MX_PL', 'tax_PR_M', 'tax_TA_M']
    return sorted(columnas_principales + columnas_pisos + columnas_taxonomia)

def _get_column_name(df, possible_names):
    return next((name for name in possible_names if name in df.columns), None)

def _get_excel_path(municipio_name):
    base = os.path.join(BASE_DATA_PATH, municipio_name, f"ModeloExposicionManzana{municipio_name}")
    return next((f"{base}.{ext}" for ext in ["xlsx", "xls"] if os.path.exists(f"{base}.{ext}")), None)

def _read_gpkg_if_exists(path):
    if not os.path.exists(path): return gpd.GeoDataFrame()
    gdf = gpd.read_file(path)
    return gdf.to_crs(epsg=4326) if gdf.crs and gdf.crs.to_epsg() != 4326 else gdf

def _aggregate_manzana_stats(group):
    """
    NÚCLEO DE LÓGICA DE AGREGACIÓN:
    Toma un grupo de registros (típicamente edificios individuales) asociados a una manzana
    y calcula las estadísticas resumidas para esa manzana.
    
    Calcula:
    1. Sumatorias totales (Valor Reposición, Nro Edificios, Población).
    2. Distribución por número de pisos (conteos y porcentajes).
    3. Distribución por tipología estructural/taxonomía (conteos y porcentajes).
    """
    # Initialize results dictionary
    results = {}
    
    # 1. Identificar columnas dinámicamente usando alias conocidos
    valor_col = _get_column_name(group, ['ValorReposicion', 'valor_reposicion'])
    edificios_col = _get_column_name(group, ['NumeroEdificios', 'numero_edificios'])
    ocupacion_col = _get_column_name(group, ['Ocupacion', 'Ocupantes', 'ocupantes', 'Residentes', 'residentes'])
    pisos_col = _get_column_name(group, ['NumeroPisos', 'NumerosPisos', 'numero_pisos'])
    tax_col = _get_column_name(group, ['Taxonomia', 'Taxonomía', 'taxonomia'])
    
    # 2. Calcular Totales Generales con conversión a numérico para evitar errores con data sucia (int + str)
    if valor_col: results['ValorReposicion'] = pd.to_numeric(group[valor_col], errors='coerce').sum()
    if edificios_col: results['NumeroEdificios'] = pd.to_numeric(group[edificios_col], errors='coerce').sum()
    if ocupacion_col: results['Ocupacion'] = pd.to_numeric(group[ocupacion_col], errors='coerce').sum()
    
    numero_edificios = results.get('NumeroEdificios', 0)
    
    # Inicializar contadores en 0 para todas las categorías esperadas
    pisos_keys = ['pisos_1', 'pisos_2_3', 'pisos_4_5', 'pisos_6_10', 'pisos_11_mas']
    tax_keys = ['BQ_M','CR_M','CR_PRM','CR_PRMM','CR_SC','MC_M','MD_M','MD_PL','MNR_M','MNR+P_M','MR_M','MX_PL','PR_M','TA_M']
    
    for key in pisos_keys + [f'pct_{k}' for k in pisos_keys]: results[key] = 0
    for key in tax_keys: results[f'tax_{key}'] = 0; results[f'pct_tax_{key}'] = 0
        
    if numero_edificios > 0 and edificios_col:
        # Pisos agg
        if pisos_col:
            pisos = pd.to_numeric(group[pisos_col], errors='coerce').fillna(0)
            edificios_values = pd.to_numeric(group[edificios_col], errors='coerce').fillna(0)
            c_1 = int(edificios_values.loc[pisos == 1].sum())
            results['pisos_1'] = c_1
            c_2_3 = int(edificios_values.loc[pisos.between(2, 3)].sum())
            results['pisos_2_3'] = c_2_3
            c_4_5 = int(edificios_values.loc[pisos.between(4, 5)].sum())
            results['pisos_4_5'] = c_4_5
            c_6_10 = int(edificios_values.loc[pisos.between(6, 10)].sum())
            results['pisos_6_10'] = c_6_10
            c_11_mas = int(edificios_values.loc[pisos >= 11].sum())
            results['pisos_11_mas'] = c_11_mas
            
            total_edificios_pisos = c_1 + c_2_3 + c_4_5 + c_6_10 + c_11_mas
            if total_edificios_pisos > 0:
                results['pct_pisos_1'] = (c_1 / total_edificios_pisos) * 100
                results['pct_pisos_2_3'] = (c_2_3 / total_edificios_pisos) * 100
                results['pct_pisos_4_5'] = (c_4_5 / total_edificios_pisos) * 100
                results['pct_pisos_6_10'] = (c_6_10 / total_edificios_pisos) * 100
                results['pct_pisos_11_mas'] = (c_11_mas / total_edificios_pisos) * 100
        
        # Tax agg
        if tax_col:
            # Create macro_tax column in the group logic locally
            # Be careful not to mutate original group if pandas warns, but apply does usually work on copy or slice
            group = group.copy()
            group['macro_tax'] = group[tax_col].astype(str).str.split('_').str[:2].str.join('_')
            
            # This logic is a bit specific to specific tax naming convention in user's data
            # User provided code:
            # for tax in tax_keys: count = int(tax_counts.get(tax, 0)); results[f'tax_{tax}'] = count
            # This implies 'tax_keys' match exactly the 'macro_tax' values? 
            # Looking at tax_keys: ['BQ_M', 'CR_M', ...]. yes they look like macro tax codes.
            
            # However, we need to map the actual values in 'Taxonomia' column to these keys.
            # The simplified logic: 
            # group['macro_tax']... might produce 'CR_L', 'CR_M' etc.
            # But earlier in data_service we had custom mapping logic.
            # The user snippet uses a simpler approach. I will trust the user snippet logic.
            
            # Re-implementing user snippet logic carefully:
            # group['macro_tax'] = group[tax_col].str.split('_').str[:2].str.join('_'); 
            # tax_counts = group.groupby('macro_tax')[edificios_col].sum()
            
            # But wait, `split('_').str[:2]` on 'CR_LFM_...' -> 'CR_LFM'.
            # 'CR_M' -> 'CR_M'.
            # 'Taxonomia' values like 'CR+LFM+M+3'.
            
            # Let's stick to the user snippet logic EXACTLY for aggregation:
            # It seems to assume the column values are compatible or normalized.
            
            # Alternative: explicit mapping loop like before?
            # User request: "mejorar la aplicacion... para que tenga una fincionalidad similar a [USER CODE]"
            # So I should use THEIR aggregation logic.

            # Their logic line:
            # group['macro_tax'] = group[tax_col].str.split('_').str[:2].str.join('_')
            # tax_counts = group.groupby('macro_tax')[edificios_col].sum()
            
            # Applying it:
            try:
                # Handling if tax_col is not string
                vals = group[tax_col].astype(str)
                # split by _, take first 2 parts, join with _
                macro_tax = vals.apply(lambda x: '_'.join(x.split('_')[:2]))
                
                # Now group by this macro_tax
                edificios_values = pd.to_numeric(group[edificios_col], errors='coerce').fillna(0)
                tax_counts = edificios_values.groupby(macro_tax).sum()
                
                total_edificios_tax = 0
                for tax in tax_keys:
                    count = int(tax_counts.get(tax, 0))
                    results[f'tax_{tax}'] = count
                    total_edificios_tax += count
                    
                if total_edificios_tax > 0:
                     for tax in tax_keys: 
                         results[f'pct_tax_{tax}'] = (results.get(f'tax_{tax}', 0) / total_edificios_tax) * 100
            except Exception as e:
                # Fallback if split fails
                pass

    return pd.Series(results)

def get_map_data(municipio_name, cartography_type, excel_column=None):
    """
    Función Principal para obtener GeoDataFrames listos para mapear.
    Realiza la unión (Merge/Spatial Join) entre:
    1. Geometría espacial (.gpkg) -> Polígonos de manzanas, municipios, etc.
    2. Datos tabulares (.xlsx) -> Inventario de exposición detallado.
    
    Retorna un GeoDataFrame enriquecido con las estadísticas calculadas.
    """
    try:
        municipio_path = os.path.join(BASE_DATA_PATH, municipio_name)
        target_gdf = _read_gpkg_if_exists(os.path.join(municipio_path, f"{cartography_type}{municipio_name}.gpkg"))
        if target_gdf.empty: return target_gdf
        
        excel_path = _get_excel_path(municipio_name)
        manzanas_con_datos_agregados = None
        
        # Procesar datos Excel si existe
        if excel_path:
            df_exposicion = pd.read_excel(excel_path)
            excel_key = 'CodigoManzana2024'
            if excel_key in df_exposicion.columns:
                # AGREGAR datos brutos a nivel de manzana usando la función helper
                # include_groups=False es requerido para compatibilidad con Pandas futuro
                df_agregado = df_exposicion.groupby(excel_key).apply(_aggregate_manzana_stats, include_groups=False).reset_index()
                
                # Cargar capa base de Manzanas para hacer el join tabular
                manzanas_gpkg_path = os.path.join(municipio_path, f"Manzanas{municipio_name}.gpkg")
                if os.path.exists(manzanas_gpkg_path):
                    manzanas_gdf = gpd.read_file(manzanas_gpkg_path)
                    gpkg_key = 'manz_ccnct'
                    if gpkg_key in manzanas_gdf.columns:
                         # Normalizar claves de unión a string
                        manzanas_gdf[gpkg_key] = manzanas_gdf[gpkg_key].astype(str)
                        df_agregado[excel_key] = df_agregado[excel_key].astype(str)
                        
                         # Fix temporal de prefijos si es necesario (ej 'C' + codigo)
                        manzanas_gdf['temp_join_key'] = 'C' + manzanas_gdf[gpkg_key]
                        
                        # MERGE TABULAR: Geometría Manzanas + Datos Agregados
                        manzanas_con_datos_agregados = manzanas_gdf.merge(df_agregado, left_on='temp_join_key', right_on=excel_key, how='left')
                        
        if manzanas_con_datos_agregados is not None:
            if cartography_type.lower() == 'manzanas':
                # Si pedimos manzanas, ya tenemos el resultado listo
                target_gdf = manzanas_con_datos_agregados
            else:
                 # Si pedimos otra capa (ej. Sectores, Veredas), necesitamos transferir los datos
                # desde las manzanas contenidas en esas geometrías mayores (Spatial Join upscaling)
                if target_gdf.crs != manzanas_con_datos_agregados.crs:
                    manzanas_con_datos_agregados = manzanas_con_datos_agregados.to_crs(target_gdf.crs)
                    
                # SPATIAL JOIN: Polígono Mayor contiene Manzanas
                datos_espaciales = gpd.sjoin(target_gdf, manzanas_con_datos_agregados, how="left", predicate="contains")
                
                # Definir reglas de agregación secundaria
                agregaciones_secundarias = {'manz_ccnct': 'count', 'ValorReposicion': 'sum', 'NumeroEdificios': 'sum', 'Ocupacion': 'sum'}
                # Filter valid columns
                agregaciones_secundarias = {k: v for k, v in agregaciones_secundarias.items() if k in datos_espaciales.columns}
                
                if agregaciones_secundarias:
                    # Agrupar por el índice del polígono original para preservar la geometría
                    datos_agregados = datos_espaciales.groupby(datos_espaciales.index).agg(agregaciones_secundarias)
                    datos_agregados = datos_agregados.rename(columns={'manz_ccnct': 'NumeroDeManzanas'})
                    
                    # Unir de vuelta al GeoDataFrame original
                    target_gdf = target_gdf.join(datos_agregados)
                    
        # Proyección final a WGS84 para visualización web
        if target_gdf.crs and target_gdf.crs.to_epsg() != 4326:
            target_gdf = target_gdf.to_crs(epsg=4326)
            
        return target_gdf
    except Exception as e:
        traceback.print_exc()
        return gpd.GeoDataFrame()

def get_manzana_detail_data(municipio_name, manzana_id):
    """
    Obtiene el listado detallado de edificaciones (top 15) para una manzana específica.
    Usado para mostrar tablas de detalle en la interfaz.
    """
    try:
        excel_path = _get_excel_path(municipio_name)
        if not excel_path: return None
        
        df_exposicion = pd.read_excel(excel_path)
        excel_key = 'CodigoManzana2024'
        if excel_key not in df_exposicion.columns: return None
        
        df_exposicion[excel_key] = df_exposicion[excel_key].astype(str)
        manzana_id = str(manzana_id)
        
        # Filtrar por manzana
        manzana_df = df_exposicion[df_exposicion[excel_key] == manzana_id]
        
        # Ordenar por importancia (Valor Reposición)
        ranking_col = 'ValorReposicion'
        if ranking_col in manzana_df.columns:
            manzana_df = manzana_df.sort_values(by=ranking_col, ascending=False)
            
        # Top 15
        manzana_df = manzana_df.head(15)
        
        cols_to_send = ['Taxonomia', 'NumeroPisos', 'AreaConstruida', 'ValorReposicion']
        existing_cols = [col for col in cols_to_send if col in manzana_df.columns]
        
        return manzana_df[existing_cols].to_json(orient='records')
    except Exception as e:
        traceback.print_exc()
        return None

def get_manzanas_geometry(municipio_name):
    """
    Retorna solo la geometría de las manzanas sin datos pesados adjuntos.
    Versión ligera para carga rápida visual.
    """
    try:
        return _read_gpkg_if_exists(os.path.join(BASE_DATA_PATH, municipio_name, f"Manzanas{municipio_name}.gpkg"))
    except Exception as e:
        traceback.print_exc()
        return gpd.GeoDataFrame()

def get_summary_report_data(municipio_name):
    """
    Genera un reporte completo JSON con:
    1. Totales del municipio.
    2. Detalle por cada manzana (para gráficos de barras, análisis de distribución, etc.)
    """
    try:
        municipio_path = os.path.join(BASE_DATA_PATH, municipio_name)
        excel_path = _get_excel_path(municipio_name)
        manzanas_con_datos_agregados = None
        
        if excel_path:
            df_exposicion = pd.read_excel(excel_path)
            excel_key = 'CodigoManzana2024'
            if excel_key in df_exposicion.columns:
                df_agregado = df_exposicion.groupby(excel_key).apply(_aggregate_manzana_stats, include_groups=False).reset_index()
                
                manzanas_gpkg_path = os.path.join(municipio_path, f"Manzanas{municipio_name}.gpkg")
                if os.path.exists(manzanas_gpkg_path):
                    manzanas_gdf = gpd.read_file(manzanas_gpkg_path)
                    gpkg_key = 'manz_ccnct'
                    if gpkg_key in manzanas_gdf.columns:
                        manzanas_gdf[gpkg_key] = manzanas_gdf[gpkg_key].astype(str)
                        df_agregado[excel_key] = df_agregado[excel_key].astype(str)
                        manzanas_gdf['temp_join_key'] = 'C' + manzanas_gdf[gpkg_key]
                        # Inner join para asegurar solo datos válidos
                        manzanas_con_datos_agregados = manzanas_gdf.merge(df_agregado, left_on='temp_join_key', right_on=excel_key, how='inner')
        
        if manzanas_con_datos_agregados is None or manzanas_con_datos_agregados.empty:
            return None
            
        columnas_a_sumar = get_excel_columns(municipio_name)
        totals = {}
        for col in columnas_a_sumar:
            if col in manzanas_con_datos_agregados.columns and pd.api.types.is_numeric_dtype(manzanas_con_datos_agregados[col]):
                totals[col] = manzanas_con_datos_agregados[col].sum()
                
        # Recalcular porcentajes globales basados en los totales sumados
        total_municipal_edificios = totals.get('NumeroEdificios', 0)
        
        if total_municipal_edificios > 0:
            total_edificios_pisos = sum(totals.get(c, 0) for c in get_excel_columns(municipio_name) if c.startswith('pisos_'))
            total_edificios_tax = sum(totals.get(c, 0) for c in get_excel_columns(municipio_name) if c.startswith('tax_'))
            
            for col in get_excel_columns(municipio_name):
                if col.startswith('pisos_') and total_edificios_pisos > 0:
                    totals[f'pct_{col}'] = (totals.get(col, 0) / total_edificios_pisos) * 100
                elif col.startswith('tax_') and total_edificios_tax > 0:
                    totals[f'pct_{col}'] = (totals.get(col, 0) / total_edificios_tax) * 100
                    
        columnas_principales = ['manz_ccnct', 'NumeroEdificios', 'Ocupacion', 'ValorReposicion']
        columnas_pisos_detalle = [item for sublist in [[f'pisos_{s}', f'pct_pisos_{s}'] for s in ['1', '2_3', '4_5', '6_10', '11_mas']] for item in sublist]
        columnas_tax_detalle = [item for sublist in [[f'tax_{t}', f'pct_tax_{t}'] for t in ['CR_PRIMM', 'MC_M', 'MD_PR', 'MNR_M', 'MR_M', 'PR_M', 'TA_M']] for item in sublist]
        
        columnas_reporte = columnas_principales + columnas_pisos_detalle + columnas_tax_detalle
        
        columnas_existentes = [c for c in columnas_reporte if c in manzanas_con_datos_agregados.columns]
        
        manzanas_detalle = manzanas_con_datos_agregados[columnas_existentes].to_dict(orient='records')
        
        reporte = {"totals": totals, "manzanas": manzanas_detalle}
        return json.dumps(reporte, default=int)
    except Exception as e:
        traceback.print_exc()
        return None

def get_scenario_location_data(municipio_name, scenario_id):
    """
    Lee los datos de ubicación de un escenario sísmico (R1/R2) desde Excel.
    Retorna un diccionario con los parámetros del evento (magnitud, profundidad, coordenadas).
    """
    try:
        municipio_path = os.path.join(BASE_DATA_PATH, municipio_name)
        
        # Patron: ResumenTOTAL_{municipio}_{scenario_id}*.xlsx (quitamos el guion bajo extra por si el nombre termina ahí)
        search_pattern = f"ResumenTOTAL_{municipio_name}_{scenario_id}*.xlsx"
        import glob
        files = glob.glob(os.path.join(municipio_path, search_pattern))
        
        if not files:
            return None
            
        # Tomar la primera coincidencia
        file_path = files[0]
        
        df = pd.read_excel(file_path, sheet_name='ruptura')
        if df.empty:
            return None
            
        # Return the first row as dict
        return df.iloc[0].to_dict()
        
    except Exception as e:
        traceback.print_exc()
        return None

def get_municipio_geometry(municipio_name):
    """
    Retorna la geometría del límite municipal (outline).
    Útil para hacer zoom al municipio o dibujar su borde.
    """
    try:
        import glob
        files = glob.glob(os.path.join(BASE_DATA_PATH, municipio_name, "Municipio*.gpkg"))
        return _read_gpkg_if_exists(files[0]) if files else gpd.GeoDataFrame()
    except Exception as e:
        traceback.print_exc()
        return gpd.GeoDataFrame()
