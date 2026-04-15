# Visor Cartográfico de Riesgo Sísmico de Antioquia

Este proyecto es una aplicación web interactiva desarrollada para permitir la visualización y el análisis de la exposición, vulnerabilidad y pérdidas potenciales (económicas, civiles y humanas) ante condiciones de riesgo sísmico en el departamento de Antioquia, Colombia.

El aplicativo ha sido diseñado originalmente en un convenio liderado por la **Universidad EAFIT** para uso de la **Gobernación de Antioquia / DAGRAN**.

---

## Arquitectura de la Aplicación

La aplicación se enmarca en un patrón **Dashboard Interactivo y Analítico** y sigue una arquitectura de Monolito Modular desarrollado enteramente en Python.

### Stack Tecnológico

1. **Frontend / Presentación:**
   - **Plotly Dash:** Actúa como motor para las interacciones reactivas de la UI sin necesidad de construir un backend separado o programar mucho Javascript explícito.
   - **Dash Bootstrap Components:** Define la grilla y la estética responsiva general de la interfaz de usuario.
   - **Dash Leaflet:** Proporciona un visor interactivo de mapas web extremadamente eficiente. Soporta estilos dinámicos de los *tiles* y renderiza capas Vectoriales Complejas (Geometries) aceleradas por hardware usando clientes JS.
2. **Backend / Servidor:**
   - **Flask & Gunicorn:** El servidor Dash es en el fondo una aplicación en Flask; manejada usando *Gunicorn* para escenarios de producción.
3. **Capa de Procesamiento Geográfico de Datos:**
   - **GeoPandas & Pandas:** Se encargan del núcleo algorítmico, que consiste en cargar archivos *GeoPackage* (.gpkg) y *Excels* (.xlsx), realizar cruces ("Spatial Joins" y "Tabular Joins"), deducir sumatorias a nivel de manzana y preparar los *GeoDataFrames* resultantes de vuelta al Frontend en tiempo real.

---

## Estructura de Módulos (Directorio)

La organización de la base de código promueve una clara separación por responsabilidades (Single Responsibility Principle):

* `run.py`: Punto de entrada de desarrollo local. Levanta la aplicación en modo `debug` y proporciona la configuración base del servidor local (puerto convencional `5001`).
* `deploy.sh` & `app.yaml`: Rutinas y manifiestos dedicados para los entornos de despliegue productivo y alojamientos en ecosistemas nativos cloud como **Google Cloud App Engine** (o Cloud Run).

### Carpeta `app/` (Lógica de Negocio Principal)

Es el core donde reside toda la lógica de construcción del mapa y los modelos.

* `app.py`: Es el controlador primordial de la estructura Single Page Application (SPA). Orquesta los esquemas de navegación (routing), inicializa los mapas de *Leaflet*, monta los contenedores condicionales y registra todos los *callbacks* en los que reacciona la interfaz globalmente.
* `config.py`: Módulo estático puro. **Centraliza todas las configuraciones**, parámetros estéticos y mapeos lexicográficos vitales (e.g., `APP_LABELS`, traductor de nombres de municipios sin tildes, estilos GUI personalizados, rutas y directorios absolutos del sistema).
* `data_service.py`: **Capa DAO (Data Access Object) y de Servicios Analíticos.** Abstrayendo la interacción directa con la base de datos (archivos `.gpkg` & `.xlsx`), este módulo localiza los archivos correspondientes a cada municipio, unifica el modelo de exposición e inyecta las estadísticas para presentarlas (funciones auxiliadoras centralizadas como `_read_gpkg_if_exists`, `get_map_data`).
* `pages/`: Cada análisis puntual (pérdidas económicas, distribución espacial o análisis determinista por escenarios) reside en su propio sub-módulo con diseños que se inyectan en tiempo de ejecución de acuerdo a la ruta URL actual, fomentando el desacoplamiento de lógicas gráficas.

### Carpeta `data/municipios/`

Bajo esta estructura de directorios estática descansa toda la información preprocesada. Cada subcarpeta (por ejemplo, `/Abejorral/`) dispone de su propia cartografía vectorizada básica (`ManzanasAbejorral.gpkg`, `MunicipioAbejorral.gpkg`) y su inventario de edificaciones detallado tabulado en formato Excel (`ModeloExposicionManzanaAbejorral.xlsx`).

---

## Análisis de Implementación Técnica (Casos y Patrones)

Para solucionar problemas de renderizado espacial extremo y escalabilidad, la implementación del proyecto usa métodos sofisticados:

**1. Interfaz Reactiva y Estado SPA:**
Mediante componentes abstractos de carga (`dcc.Loading`) y manejadores de enlaces directos de rutas Dash (`dcc.Location`), la aplicación evita recargas completas (paginación dura) al servidor. La pesada capa de renderización vectorial del mapa principal está **siempre** presente e intocable dentro de un contenedor en el DOM, ahorrando inmensos recursos de red y re-procesamiento cada vez que se cambia la URL.

**2. Lazy-Loading (Carga Estricta Bajo Demanda):**
Por las grandes dimensiones geográficas del departamento de Antioquia, no se cargan las manzanas, ni modelos estadísticos masivos en memoria inicialmente. La aplicación sube a memoria interna únicamente un GeoDataFrame de bordes ligeros como inventario general base para las etiquetas (`tooltips`). Toda la algoritmia de correlación se ejecuta explícitamente y al vuelo **solamente** una vez que se selecciona un municipio específico haciendo llamadas asincrónicas.

**3. Data-Driven Javascript Styling:**
Para fomentar un rendimiento fluido al manejar muchísimos polígonos interactivos o contornos. En lugar de que Python aplique dinámicamente colores uno-por-uno cada vez que el índice o dropdown seleccionado cambia construyendo inmensos archivos `GeoJSON` de transferencia, la aplicación usa objetos funcionales insertados *Namespace Javascript ("dash_extensions")* dentro de interacciones nativas *Dash-Leaflet*.

**4. Accesibilidad WCAG Independiente Continua:**
Incluye accesibilidad avalada (WCAG 2.1) inyectada nativamente por Javascript del cliente (*`clientside_callback`*). Delegando tareas simples como la activación del modo oscuro general mediante *High-Contrast* o el engrosamiento del tamaño y tipografía del cuerpo, este proceso ahorra sobrecargas al servidor backend en iteraciones donde no es necesario el cómputo en Python.
