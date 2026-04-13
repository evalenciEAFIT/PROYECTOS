#!/bin/bash

# ==============================================================================
#  rama.sh — Script de sincronización del Visor Cartográfico
#  Propósito: Actualizar el repositorio 'PROYECTOS' con el estado actual
# ==============================================================================

# Colores para una salida premium
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[0;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Configuración de rutas
SOURCE_DIR="/home/edi/PROYECTOS/visor_cartografico_dev_2026"
TARGET_DIR="/home/edi/PROYECTOS/PROYECTOS/SISMOS2026EAFIT"
REPO_DIR="/home/edi/PROYECTOS/PROYECTOS"

echo -e "${BLUE}▶ Iniciando actualización del Visor Cartográfico...${NC}"

# 1. Sincronizar archivos (excluyendo entornos virtuales y temporales)
echo -e "${BLUE}▶ Sincronizando archivos con el repositorio...${NC}"
rsync -av --delete \
    --exclude='venv/' \
    --exclude='__pycache__/' \
    --exclude='.git/' \
    --exclude='*.pyc' \
    --exclude='.pytest_cache' \
    --exclude='.env' \
    "$SOURCE_DIR/" "$TARGET_DIR/"

# 2. Operaciones de Git
echo -e "${BLUE}▶ Preparando envío a GitHub (evalenciEAFIT/PROYECTOS)...${NC}"
cd "$REPO_DIR" || exit

# Actualizar para evitar conflictos
git pull origin main --rebase

git add .

# Verificar si hay cambios antes de hacer commit
if git diff --cached --quiet; then
    echo -e "${YELLOW}ℹ No hay cambios nuevos detectados.${NC}"
else
    COMMIT_MSG="Visor Cartográfico: Actualización automática $(date '+%Y-%m-%d %H:%M:%S')"
    git commit -m "$COMMIT_MSG"
    echo -e "${GREEN}✓ Archivos comprometidos localmente.${NC}"
fi

# 3. Push a GitHub
# Verificamos si hay commits locales que no estén en el servidor
COMMITS_PENDING=$(git log origin/main..main --oneline 2>/dev/null)

if [ -n "$COMMITS_PENDING" ]; then
    echo -e "${BLUE}▶ Subiendo cambios nuevos a GitHub...${NC}"
    if git push origin main; then
        echo -e "${GREEN}╔════════════════════════════════════════════════════════════════╗${NC}"
        echo -e "${GREEN}║  ✓ ACTUALIZACIÓN COMPLETADA EXITOSAMENTE                       ║${NC}"
        echo -e "${GREEN}╚════════════════════════════════════════════════════════════════╝${NC}"
    else
        echo -e "${RED}✘ Error al subir a GitHub.${NC}"
        echo -e "${YELLOW}💡 Sugerencias:${NC}"
        echo -e "   1. Verifica tu conexión a internet."
        echo -e "   2. Asegúrate de que tu Personal Access Token (PAT) sea válido."
        echo -e "   3. Si ves 'Rejected', intenta ejecutar: git pull origin main --rebase"
        exit 1
    fi
else
    echo -e "${GREEN}╔════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║  ✓ TODO ESTÁ AL DÍA EN GITHUB (Nada nuevo por subir)           ║${NC}"
    echo -e "${GREEN}╚════════════════════════════════════════════════════════════════╝${NC}"
fi
