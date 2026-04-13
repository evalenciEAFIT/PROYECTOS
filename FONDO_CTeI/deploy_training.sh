#!/bin/bash
# Script para desplegar la aplicación de ENTRENAMIENTO en Google Cloud (Cloud Run)

# === Configuración de tu cuenta y proyecto GCP ===
EMAIL="edison.valencia.eafit@gmail.com"
PROJECT_ID="financiero-idi"
SERVICE_NAME="fctei-entrenamiento"
REGION="us-central1"

echo "=========================================================="
echo " INICIANDO DESPLIEGUE EN GCP: $PROJECT_ID (ENTRENAMIENTO)"
echo " Servicio: $SERVICE_NAME"
echo " Cuenta: $EMAIL"
echo "=========================================================="

echo "1. Autenticando y configurando GCP (si requiere login, sigue el link de GCP)..."
# gcloud auth login $EMAIL # (Opcional, descomenta si necesitas pedir token nuevamente)
gcloud config set account $EMAIL
gcloud config set project $PROJECT_ID

echo "2. Redirigiendo al directorio del backend..."
# Cambiamos al directorio de la aplicación banco_app
cd /home/edi/PROYECTOS/FONDO_CTeI/banco_app || exit 1

echo "3. Desplegando en Google Cloud Run (Ambiente de Entrenamiento)..."
# Se asume que no necesitas un Dockerfile y gcloud utilizará Cloud Build automáticamente
gcloud run deploy $SERVICE_NAME \
    --source . \
    --region $REGION \
    --allow-unauthenticated \
    --port 3000 \
    --project $PROJECT_ID

echo "========================================="
echo "¡Despliegue de entrenamiento finalizado!"
echo "========================================="
