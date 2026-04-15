#!/bin/bash

# ==============================================================================
#  rama.sh — Script de Sincronización TOTAL
#  Proyecto: Riesgo Sísmico (Visor Cartográfico)
#  Repositorio: https://github.com/evalenciEAFIT/riesgo_sismico
# ==============================================================================

# Colores Premium
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[0;33m'
RED='\033[0;31m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Configuración
SOURCE_DIR="/home/edi/PROYECTOS/visor_cartografico_dev_2026"
TARGET_DIR="/home/edi/SISMOS2026EAFIT"
GITHUB_REPO="https://github.com/evalenciEAFIT/riesgo_sismico"
BRANCH="main"

echo -e "${CYAN}🚀 Iniciando sincronización TOTAL (incluyendo datos) para: ${YELLOW}riesgo_sismico${NC}"

# 1. Preparar Directorio de Destino
if [ ! -d "$TARGET_DIR" ]; then
    echo -e "${BLUE}▶ Creando directorio de destino...${NC}"
    mkdir -p "$TARGET_DIR"
fi

# 2. Sincronización Completa (Sin exclusiones de datos)
echo -e "${BLUE}▶ Sincronizando todos los archivos y datos...${NC}"
rsync -av --delete \
    --exclude='venv/' \
    --exclude='__pycache__/' \
    --exclude='.git/' \
    --exclude='*.pyc' \
    --exclude='.pytest_cache' \
    --exclude='.env' \
    "$SOURCE_DIR/" "$TARGET_DIR/"

# 3. Inicialización/Configuración del Repositorio Git
cd "$TARGET_DIR" || exit

if [ ! -d ".git" ]; then
    echo -e "${BLUE}▶ Inicializando repositorio Git...${NC}"
    git init -b "$BRANCH"
fi

# Asegurar Remote Correcto
git remote remove origin 2>/dev/null
git remote add origin "$GITHUB_REPO"

# 4. .gitignore Permisivo (Solo ignora lo estrictamente necesario)
echo -e "${BLUE}▶ Actualizando .gitignore para permitir datos...${NC}"
cat <<EOF > .gitignore
venv/
__pycache__/
*.pyc
.env
.pytest_cache
EOF

# 5. Operaciones de Git
echo -e "${BLUE}▶ Preparando commit con datos...${NC}"
git add .

if git diff --cached --quiet; then
    echo -e "${YELLOW}ℹ No hay cambios nuevos para subir.${NC}"
else
    COMMIT_MSG="Full Backup: $(date '+%Y-%m-%d %H:%M') - Incluye carpeta data"
    git commit -m "$COMMIT_MSG"
    echo -e "${GREEN}✓ Cambios (incluyendo data/) comprometidos localmente.${NC}"
fi

# 6. Despliegue TOTAL a GitHub
echo -e "${BLUE}▶ Subiendo todo a GitHub (esto puede tardar por el tamaño de data/)...${NC}"
# Usamos force para asegurar que el repositorio remoto refleje exactamente el estado local con datos
if git push origin "$BRANCH" --force; then
    echo -e "${GREEN}╔════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║  ✓ RESPALDO TOTAL COMPLETADO EXITOSAMENTE                      ║${NC}"
    echo -e "${GREEN}╚════════════════════════════════════════════════════════════════╝${NC}"
else
    echo -e "${RED}✘ Error al subir a GitHub.${NC}"
    echo -e "${YELLOW}💡 Verifica que ningún archivo individual supere los 100MB.${NC}"
    exit 1
fi
