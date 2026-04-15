#!/bin/bash

# Este script despliega únicamente el Dashboard en Google Cloud Run

# Proyecto GCP objetivo
PROJECT_ID="repositorio-sama"
PROJECT_NUMBER="372574562914" 
REGION="us-central1"

echo "============================================="
echo "   Iniciando Despliegue de SAMA en GCP Run   "
echo "============================================="

# 1. Establecer el proyecto activo en gcloud
echo "Configurando el proyecto de GCP ($PROJECT_ID)..."
gcloud config set project $PROJECT_ID

# 2. Obtenemos la URL de la API actualmente desplegada
API_URL=$(gcloud run services describe sama-api --platform managed --region $REGION --project $PROJECT_ID --format 'value(status.url)')
echo "-> URL de la API actual: $API_URL"

# 3. Despliegue del Dashboard
echo "Desplegando Aplicación Web SAMA Dashboard..."
gcloud run deploy sama-dashboard \
    --source DASHBOARD/ \
    --region $REGION \
    --project $PROJECT_ID \
    --set-env-vars API_BASE_URL="${API_URL}/api/v1",API_KEY="SamaAPI2026Secure" \
    --allow-unauthenticated \
    --memory 1Gi \
    --timeout 1800 \
    --platform managed

echo "============================================="
echo " Despliegue del Dashboard Completado!!!      "
echo "============================================="
