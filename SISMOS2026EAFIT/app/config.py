"""
Módulo de Configuración Global (config.py)
=============================================================================
Este módulo centraliza todas las variables de configuración, referencias de
directorios, estilos base y diccionarios estáticos del aplicativo web.
Permite editar fácilmente la configuración o las traducciones visuales
sin tener que modificar la lógica de negocio subyacente o múltiples archivos.
"""

import os

# =============================================================================
# 1. CONFIGURACIÓN DE RUTAS Y DIRECTORIOS DEL SISTEMA
# =============================================================================
# APP_DIR: Apunta al directorio del código fuente ('app/')
APP_DIR = os.path.dirname(os.path.abspath(__file__))

# PROJECT_ROOT y BASE_DIR: Suben un nivel para referirse a la raíz 'visor_cartografico_...'
PROJECT_ROOT = os.path.dirname(APP_DIR)
BASE_DIR = PROJECT_ROOT # Alias para mantener compatibilidad con algunos componentes

# DATA_DIR: Ruta base a la carpeta de datos estructurados (archivos Gpkg, Excel)
DATA_DIR = os.path.join(PROJECT_ROOT, "data")

# BASE_DATA_PATH: Ruta a la cartografía específica de cada uno de los municipios
BASE_DATA_PATH = os.path.join(DATA_DIR, "municipios")


# =============================================================================
# 2. CONSTANTES DE INTERFAZ DE USUARIO (GUI)
# =============================================================================
# custom_style: Extiende o sobrescribe las variables CSS o estilos de Dash
custom_style = {
    'sidebar-expanded': {
        'width': '350px' # Establece un ancho más amplio para menús detallados
    }
}


# =============================================================================
# 3. DICCIONARIO PARA ETIQUETADO EN PANTALLA (APP_LABELS)
# =============================================================================
# Traduce los identificadores técnicos de columnas/bases de datos a texto comprensible 
# y bien formateado para gráficos, leyendas en mapas interactivos y menús.
APP_LABELS = {
    # --- Variables Principales de Exposición ---
    'ValorReposicion': 'Valor de Reposición Total', 
    'NumeroEdificios': 'Número Total de Edificaciones', 
    'Ocupacion': 'Población Expuesta', 
    'Residentes': 'Residentes',
    
    # --- Clasificación por Rangos de Pisos ---
    'pisos_1': 'Edificaciones de 1 piso',
    'pisos_2_3': 'Edificaciones de 2 a 3 pisos', 
    'pisos_4_5': 'Edificaciones de 4 a 5 pisos', 
    'pisos_6_10': 'Edificaciones de 6 a 10 pisos', 
    'pisos_11_mas': 'Edificaciones de 11 o más pisos',
    
    # --- Taxonomía Estructural (Identificador técnico original -> Nombre detallado) ---
    'tax_BQ_M': 'BQ_M: muros de bahareque',
    'tax_CR_M': 'CR_M: muros de concreto reforzado',
    'tax_CR_PRMM': 'CR_PRMM: pórticos resistentes a momento de concreto reforzado con muros adosados',
    'tax_CR_SC': 'CR_SC: sistemas combinados de concreto reforzado',
    'tax_MC_M': 'MC_M: muros de mampostería confinada',
    'tax_MD_M': 'MD_M: muros de madera',
    'tax_MD_PL': 'MD_PL: pórticos livianos de madera',
    'tax_MNR_M': 'MNR_M: muros de mampostería no reforzada',
    'tax_MR_M': 'MR_M: muros de mampostería reforzada',
    'tax_PR_M': 'PR_M: muros prefabricado',
    'tax_TA_M': 'TA_M: muros de tapia',
    
    # --- Mapeos Directos para Redundancia (Sin sufijo "tax_") ---
    'BQ_M': 'BQ_M: muros de bahareque',
    'CR_M': 'CR_M: muros de concreto reforzado',
    'CR_PRMM': 'CR_PRMM: pórticos resistentes a momento de concreto reforzado con muros adosados',
    'CR_SC': 'CR_SC: sistemas combinados de concreto reforzado',
    'MC_M': 'MC_M: muros de mampostería confinada',
    'MD_M': 'MD_M: muros de madera',
    'MD_PL': 'MD_PL: pórticos livianos de madera',
    'MNR_M': 'MNR_M: muros de mampostería no reforzada',
    'MR_M': 'MR_M: muros de mampostería reforzada',
    'PR_M': 'PR_M: muros prefabricado',
    'TA_M': 'TA_M: muros de tapia'
}


# =============================================================================
# 4. TRADUCTOR DE CÓDIGOS DE MUNICIPIOS
# =============================================================================
# Las carpetas del sistema descartan tildes y ñ. MUNICIPIOS_DICT corrige
# esto en tiempo de ejecución para mostrarlos con ortografía impecable.
MUNICIPIOS_DICT = {
    'Abejorral': 'Abejorral',
    'Abriaqui': 'Abriaquí',
    'Alejandria': 'Alejandría',
    'Amaga': 'Amagá',
    'Amalfi': 'Amalfi',
    'Andes': 'Andes',
    'Angelopolis': 'Angelópolis',
    'Angostura': 'Angostura',
    'Anori': 'Anorí',
    'Anza': 'Anzá',
    'Apartado': 'Apartadó',
    'Arboletes': 'Arboletes',
    'Argelia': 'Argelia',
    'Armenia': 'Armenia',
    'Bagre': 'El Bagre',
    'Belmira': 'Belmira',
    'Betania': 'Betania',
    'Betulia': 'Betulia',
    'Briceno': 'Briceño',
    'Buritica': 'Buriticá',
    'Caceres': 'Cáceres',
    'Caicedo': 'Caicedo',
    'Campamento': 'Campamento',
    'Canasgordas': 'Cañasgordas',
    'Caracoli': 'Caracolí',
    'Caramanta': 'Caramanta',
    'Carepa': 'Carepa',
    'CarmenViboral': 'El Carmen de Viboral',
    'Carolina': 'Carolina del Príncipe',
    'Caucasia': 'Caucasia',
    'Ceja': 'La Ceja',
    'Chigorodo': 'Chigorodó',
    'Cisneros': 'Cisneros',
    'CiudadBolivar': 'Ciudad Bolívar',
    'Cocorna': 'Cocorná',
    'Concepcion': 'Concepción',
    'Concordia': 'Concordia',
    'Dabeiba': 'Dabeiba',
    'Donmatias': 'Donmatías',
    'Ebejico': 'Ebéjico',
    'Entrerrios': 'Entrerríos',
    'Fredonia': 'Fredonia',
    'Frontino': 'Frontino',
    'Giraldo': 'Giraldo',
    'GomezPlata': 'Gómez Plata',
    'Granada': 'Granada',
    'Guadalupe': 'Guadalupe',
    'Guarne': 'Guarne',
    'Guatape': 'Guatapé',
    'Heliconia': 'Heliconia',
    'Hispania': 'Hispania',
    'Ituango': 'Ituango',
    'Jardin': 'Jardín',
    'Jerico': 'Jericó',
    'Liborina': 'Liborina',
    'Maceo': 'Maceo',
    'Marinilla': 'Marinilla',
    'Montebello': 'Montebello',
    'Murindo': 'Murindó',
    'Mutata': 'Mutatá',
    'Narino': 'Nariño',
    'Nechi': 'Nechí',
    'Necocli': 'Necoclí',
    'Olaya': 'Olaya',
    'Penol': 'El Peñol',
    'Peque': 'Peque',
    'Pintada': 'La Pintada',
    'Pueblorrico': 'Pueblorrico',
    'PuertoBerrio': 'Puerto Berrío',
    'PuertoNare': 'Puerto Nare',
    'PuertoTriunfo': 'Puerto Triunfo',
    'Remedios': 'Remedios',
    'Retiro': 'El Retiro',
    'Rionegro': 'Rionegro',
    'Sabanalarga': 'Sabanalarga',
    'Salgar': 'Salgar',
    'SanAndresCuerquia': 'San Andrés de Cuerquia',
    'SanCarlos': 'San Carlos',
    'SanFrancisco': 'San Francisco',
    'SanJeronimo': 'San Jerónimo',
    'SanJoseMontana': 'San José de la Montaña',
    'SanJuanUraba': 'San Juan de Urabá',
    'SanLuis': 'San Luis',
    'SanPedroMilagros': 'San Pedro de los Milagros',
    'SanPedroUraba': 'San Pedro de Urabá',
    'SanRafael': 'San Rafael',
    'SanRoque': 'San Roque',
    'SanVicenteFerrer': 'San Vicente Ferrer',
    'SantaBarbara': 'Santa Bárbara',
    'SantaFeAntioquia': 'Santa Fe de Antioquia',
    'SantaRosaOsos': 'Santa Rosa de Osos',
    'SantoDomingo': 'Santo Domingo',
    'Santuario': 'El Santuario',
    'Segovia': 'Segovia',
    'Sonson': 'Sonsón',
    'Sopetran': 'Sopetrán',
    'Tamesis': 'Támesis',
    'Taraza': 'Tarazá',
    'Tarso': 'Tarso',
    'Titiribi': 'Titiribí',
    'Toledo': 'Toledo',
    'Turbo': 'Turbo',
    'Union': 'La Unión',
    'Uramita': 'Uramita',
    'Urrao': 'Urrao',
    'Valdivia': 'Valdivia',
    'Valparaiso': 'Valparaíso',
    'Vegachi': 'Vegachí',
    'Venecia': 'Venecia',
    'VigiaFuerte': 'Vigía del Fuerte',
    'Yali': 'Yalí',
    'Yarumal': 'Yarumal',
    'Yolombo': 'Yolombó',
    'Yondo': 'Yondó',
    'Zaragoza': 'Zaragoza'
}
