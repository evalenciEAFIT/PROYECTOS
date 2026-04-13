#!/bin/bash

# ==============================================================================
#  rama.sh — Script de sincronización del Proyecto FONDO_CTeI
#  Propósito: Copiar al repositorio 'PROYECTOS' y subir a GitHub
# ==============================================================================

GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[0;33m'
RED='\033[0;31m'
NC='\033[0m'

SOURCE_DIR="/home/edi/PROYECTOS/FONDO_CTeI"
TARGET_DIR="/home/edi/PROYECTOS/PROYECTOS/FONDO_CTeI"
REPO_DIR="/home/edi/PROYECTOS/PROYECTOS"

# 1. Traer cambios remotos primero (evita conflictos)
echo -e "${BLUE}▶ Sincronizando con GitHub...${NC}"
cd "$REPO_DIR" || exit
git pull origin main --rebase 2>&1 | grep -v "Already up to date" || true

# 2. Copiar SOLO código fuente (sin datos sensibles ni temporales)
echo -e "${BLUE}▶ Copiando archivos a PROYECTOS/FONDO_CTeI/...${NC}"
rsync -av --delete \
    --exclude='node_modules/' \
    --exclude='*.db' \
    --exclude='.env' \
    --exclude='*.sqbpro' \
    --exclude='.git/' \
    --exclude='*.log' \
    "$SOURCE_DIR/" "$TARGET_DIR/"

# 3. Git — solo la carpeta FONDO_CTeI
echo -e "${BLUE}▶ Preparando commit (solo FONDO_CTeI/)...${NC}"
git add FONDO_CTeI/

if git diff --cached --quiet; then
    echo -e "${YELLOW}ℹ No hay cambios nuevos en FONDO_CTeI/.${NC}"
else
    git commit -m "FONDO_CTeI: Actualización $(date '+%Y-%m-%d %H:%M')"
    echo -e "${GREEN}✓ Archivos comprometidos localmente.${NC}"
fi

# 4. Push (solo si hay commits pendientes)
COMMITS_PENDING=$(git log origin/main..main --oneline 2>/dev/null)
if [ -n "$COMMITS_PENDING" ]; then
    echo -e "${BLUE}▶ Subiendo a GitHub (evalenciEAFIT/PROYECTOS)...${NC}"
    if git push origin main; then
        echo -e "${GREEN}╔════════════════════════════════════════════════════════════════╗${NC}"
        echo -e "${GREEN}║  ✓ ACTUALIZACIÓN COMPLETADA EXITOSAMENTE                       ║${NC}"
        echo -e "${GREEN}╚════════════════════════════════════════════════════════════════╝${NC}"
    else
        echo -e "${RED}✘ Error al subir a GitHub.${NC}"
        echo -e "${YELLOW}💡 Sugerencias:${NC}"
        echo -e "   1. Verifica tu conexión a internet."
        echo -e "   2. Asegúrate de que tu Personal Access Token (PAT) sea válido."
        echo -e "   3. Si ves 'Rejected': git pull origin main --rebase"
        exit 1
    fi
else
    echo -e "${GREEN}╔════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║  ✓ TODO ESTÁ AL DÍA EN GITHUB (Nada nuevo por subir)           ║${NC}"
    echo -e "${GREEN}╚════════════════════════════════════════════════════════════════╝${NC}"
fi
