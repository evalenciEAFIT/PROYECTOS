#!/bin/bash

# Este script despliega únicamente la API en Google Cloud Run

# Proyecto GCP objetivo
PROJECT_ID="repositorio-sama"
PROJECT_NUMBER="372574562914" 
REGION="us-central1"

echo "============================================="
echo "   Iniciando Despliegue de SAMA API en GCP   "
echo "============================================="

# 1. Establecer el proyecto activo en gcloud
echo "Configurando el proyecto de GCP ($PROJECT_ID)..."
gcloud config set project $PROJECT_ID

# 2. Despliegue de la API Web
echo "Desplegando Microservicio SAMA API..."
gcloud run deploy sama-api \
    --source API/ \
    --region $REGION \
    --project $PROJECT_ID \
    --allow-unauthenticated \
    --memory 2Gi \
    --timeout 1800 \
    --platform managed

echo "-> URL de la API desplegada: $(gcloud run services describe sama-api --platform managed --region $REGION --project $PROJECT_ID --format 'value(status.url)')"

echo "============================================="
echo "    Despliegue de la API Completado!!!       "
echo "============================================="
