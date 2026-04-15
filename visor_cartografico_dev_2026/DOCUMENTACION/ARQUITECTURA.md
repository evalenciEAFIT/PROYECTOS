# Arquitectura del Visor Cartográfico de Exposición y Riesgos

Este documento proporciona una descripción detallada de la arquitectura técnica, la estructura de componentes y el flujo de datos de la aplicación **Visor Cartográfico**.

---

## 1. Visión General de la Arquitectura

La aplicación está construida utilizando **Python** y el framework **Dash (Plotly)**, siguiendo un patrón de diseño modular que separa la lógica de presentación (Frontend) de la lógica de procesamiento de datos y negocio (Backend).

### Tecnologías Principales
*   **Core Framework**: `Dash` (v2.x) para la creación de la aplicación web interactiva.
*   **Diseño UI/UX**: `Dash Bootstrap Components` (DBC) y CSS personalizado para un diseño responsivo y moderno, incluyendo temas "Glassmorphism".
*   **Visualización Geoespacial**: `Dash Leaflet` para mapas interactivos de alto rendimiento y `GeoPandas` para el manejo de geometrías.
*   **Procesamiento de Datos**: `Pandas` y `NumPy` para la manipulación estadística y tabular de datos de exposición.
*   **Gráficos Estadísticos**: `Plotly Graph Objects` para visualizaciones de datos detalladas y personalizables.

---

## 2. Estructura del Proyecto

El proyecto sigue una estructura jerárquica organizada por funcionalidad:

```text
visor_cartografico_dev_2026/
├── app/                        # Código fuente de la aplicación
│   ├── assets/                 # Recursos estáticos (CSS, Imágenes, JS)
│   │   ├── style.css           # Estilos globales y temas
│   │   └── dashExtensions_default.js # Scripts clientside (Dash Extensions)
│   ├── data/                   # (Referencia) Directorio de datos
│   ├── pages/                  # Módulos de páginas individuales
│   │   ├── analisis_model.py   # Dashboard de "Análisis de Exposición"
│   │   ├── perdida_economica.py # Módulos de cálculo de riesgo (ejemplo)
│   │   └── ...
│   ├── app.py                  # Punto de entrada principal (Main Application)
│   └── data_service.py         # Capa de acceso a datos y lógica de negocio
├── data/                       # Repositorio de datos (fuera del código fuente)
│   └── municipios/             # Datos organizados por municipio
│       └── [Nombre_Municipio]/
│           ├── Manzanas[Nombre].gpkg   # Geometrías base
│           ├── ModeloExposicion...xlsx # Datos tabulares detallados
│           └── ...
└── requirements.txt            # Dependencias del proyecto
```

---

## 3. Componentes Principales

### 3.1. `app.py` (Controlador Principal)
Actúa como el orquestador de la aplicación. Sus responsabilidades son:
*   **Inicialización**: Configura la instancia de Dash, temas externos y metatags.
*   **Routing**: Maneja la navegación entre páginas (`dcc.Location`) basándose en la URL.
*   **Layout Global**: Define la estructura base que persiste entre páginas (Barra lateral de navegación, Mapa de fondo persistente, Contenedores de contenido).
*   **Callbacks Globales**: Gestiona la interacción de alto nivel, como la selección del municipio, actualizaciones del mapa principal y la visibilidad del menú lateral.

### 3.2. `data_service.py` (Capa de Servicios de Datos)
Centraliza toda la lógica de lectura, transformación y agregación de datos. Abstrae la complejidad de los archivos físicos para el resto de la app.
*   **Manejo de Archivos**: Localiza automáticamente archivos `.gpkg` y `.xlsx` basados en convenciones de nombres.
*   **Agregación Estadística**: Contiene lógicas complejas (`_aggregate_manzana_stats`) para resumir datos de edificaciones individuales a nivel de manzana (agrupando por pisos, taxonomía, etc.).
*   **Operaciones Espaciales**: Realiza uniones espaciales (`spatial joins`) y proyecciones de coordenadas (EPSG:4326) usando GeoPandas.

### 3.3. Módulos de Páginas (ej. `pages/analisis_model.py`)
Cada archivo en `pages/` representa una vista o tablero específico.
*   **Arquitectura de Vistas**: Cada módulo exporta una función `layout(municipality)` que retorna la interfaz gráfica específica para ese contexto.
*   **Callbacks Locales**: Define su propia lógica de interactividad (ej. filtrar una tabla, actualizar un gráfico al seleccionar una fila) mediante una función de registro `register_callbacks(app)`.
*   **Componentes UI**: Implementa componentes visuales reutilizables como Tarjetas KPI (`create_stat_card`) y gráficos (`generate_horizontal_bar_chart`).

---

## 4. Flujo de Datos

### 4.1. Carga Inicial
1.  El usuario accede a la aplicación.
2.  `app.py` consulta `data_service.get_available_municipios()` para poblar el selector de búsqueda.

### 4.2. Selección de Municipio
1.  El usuario selecciona un municipio en el menú lateral.
2.  **Actualización del Mapa**:
    *   `app.py` llama a `data_service.get_map_data()`.
    *   Se lee el GeoPackage del municipio y el Excel de exposición.
    *   Se realiza un `merge` para unir geometrías con estadísticas.
    *   Se retorna un objeto GeoJSON que `dash-leaflet` renderiza.
3.  **Filtrado de Navegación**: Se habilitan los enlaces a los tableros de análisis.

### 4.3. Visualización de Tableros (ej. Análisis de Modelo)
1.  El usuario navega a `/analisis-modelo`.
2.  `app.py` detecta el cambio de URL e invoca `analisis_model.layout(municipio)`.
3.  La página llama a `data_service.get_summary_report_data()`:
    *   Calcula totales municipales (Suma de Valor Expuesto, Población, Edificios).
    *   Computa distribuciones porcentuales (Tipologías constructivas, Rangos de pisos).
4.  Se renderiza el Dashboard con KPIs, Gráficos y Tabla de Manzanas.

### 4.4. Interactividad "Drill-down"
1.  El usuario hace clic en una fila de la tabla de manzanas.
2.  Un callback local en `analisis_model.py` se activa.
3.  Se invoca `data_service.get_manzana_detail_data()` para obtener los registros "Top 15" de esa manzana específica.
4.  Se muestra un panel lateral o modal con el detalle específico y un mini-mapa de localización.

---

## 5. Decisiones de Diseño Clave

*   **Persistencia del Mapa**: El contenedor del mapa (`map-view-container`) se mantiene en el DOM incluso al navegar a otras páginas (usando `{display: none}` en lugar de eliminarlo). Esto evita recargas costosas de las capas geográficas y mejora la experiencia de usuario.
*   **Procesamiento "On-the-fly" vs Pre-calculado**:
    *   La aplicación lee datos crudos (.xlsx, .gpkg) y los procesa en tiempo real. Esto facilita la actualización de datos (simplemente reemplazando archivos) sin necesitar una base de datos compleja, adecuado para el volumen de datos actual.
*   **Estilizado Clientside**: Se utiliza `dash-extensions` para inyectar funciones JavaScript pequeñas que manejan el estilizado de características del mapa (colores según valores), descargando al servidor de tareas puramente visuales.
*   **Diseño Modular de Callbacks**: Al separar los callbacks en las páginas correspondientes y registrarlos explícitamente, se evita crear un archivo `app.py` monolítico e inmanejable.

---
