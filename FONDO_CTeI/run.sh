#!/bin/bash

# Script para iniciar la aplicación localmente

APP_DIR="banco_app"

echo "======================================"
echo "    Iniciando la aplicación local     "
echo "======================================"

# Verificar si el directorio existe
if [ ! -d "$APP_DIR" ]; then
    echo "Error: El directorio $APP_DIR no existe."
    exit 1
fi

cd "$APP_DIR" || exit

# Instalar dependencias si la carpeta node_modules no existe
if [ ! -d "node_modules" ]; then
    echo "Instalando dependencias de Node.js..."
    npm install
fi

echo "Iniciando servidor en modo desarrollo..."
# Usar npm run dev porque estamos en local (tiliza nodemon)
npm run dev
