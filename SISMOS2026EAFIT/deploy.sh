#!/bin/bash

# Script de Despliegue para Visor Cartográfico
# Proyecto GCP: riesgosismico

# Stop immediately if a command exits with a non-zero status
set -e

echo "========================================"
echo "Iniciando despliegue a Google App Engine"
echo "========================================"

# Validation
if [ ! -f "requirements.txt" ]; then
    echo "ERROR: No se encontró requirements.txt"
    exit 1
fi

if ! grep -q "gunicorn" "requirements.txt"; then
    echo "ERROR: gunicorn no está en requirements.txt (Requerido para App Engine)"
    exit 1
fi

# Asegurar que estamos en el proyecto correcto
echo "Configurando proyecto: riesgosismico..."
gcloud config set project riesgosismico

# Desplegar
echo "Ejecutando gcloud app deploy..."
gcloud app deploy --quiet

echo "========================================"
echo "Despliegue finalizado exitosamente."
echo "URL: https://riesgosismico.uc.r.appspot.com"
echo "========================================"
