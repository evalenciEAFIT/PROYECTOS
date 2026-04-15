# ==============================================================================
# VISOR CARTOGRÁFICO DE RIESGO SÍSMICO - PYTHON DOCKERFILE
# ==============================================================================
# Imagen ligera con la penúltima arquitectura de Python segura y purificada.
FROM python:3.12-slim

# Evitar la creación del sistema caché local a capa OS
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Instalar dependencias puras del Kernel OS (C++ y GDAL vital para librerías espaciales GeoPandas/Fiona)
# El flag --no-install-recommends elimina un 20% de peso de librerías en la descarga.
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gdal-bin \
    libgdal-dev \
    gcc \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Establecer la carpeta de trabajo estandarizada del host virtual
WORKDIR /app

# Instalar librerías nativas usando requirements
COPY requirements.txt .

# No-cache-dir fuerza a que dejen de almacenarse binarios residuales ahorrando espacio docker de final.
RUN pip install --no-cache-dir -r requirements.txt

# Incorporar a la capa superior el proyecto per se, exceptuando lo de `.dockerignore`.
COPY . .

# Habilitar un puerto predeterminado (Puede reescribirse dinámicamente en Nubes)
ENV PORT=8080
EXPOSE 8080

# Iniciar Gunicorn acoplado en modo producción con workers equivalentes al de un procesador F2 de App Engine,
# con 120s para evadir interrupciones agresivas tras lecturas demoradas en carga Leaflet.
CMD gunicorn -b :$PORT app.app:server --workers 3 --timeout 120
