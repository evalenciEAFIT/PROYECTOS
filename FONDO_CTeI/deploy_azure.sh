#!/bin/bash
# Script para desplegar la aplicación en Azure (Azure App Service)

# === Configuración de tu cuenta y proyecto de Azure ===
EMAIL="evalenci@eafit.edu.co"
APP_NAME="FCTeI"
RESOURCE_GROUP="FCTeI-rg"
LOCATION="centralus" # Intentamos en 'centralus' pues en 'eastus' indicaba no tener cuota disponible.
SKU="F1" # F1 es el plan gratuito (ideal para cuentas universitarias sin cuota para Basic VMs)

echo "=========================================================="
echo " INICIANDO DESPLIEGUE EN AZURE"
echo " Servicio: $APP_NAME"
echo " Cuenta: $EMAIL"
echo "=========================================================="

# (El uso de MFA en EAFIT hace que la contraseña estática en bash no esté permitida)

# Verificar si Azure CLI está instalado
if ! command -v az &> /dev/null; then
    echo "Error: El comando 'az' (Azure CLI) no está instalado o no se encuentra en tu PATH."
    echo "Por favor, instálalo antes de intentar desplegar."
    echo "En Fedora puedes usar: sudo rpm --import https://packages.microsoft.com/keys/microsoft.asc && sudo sh -c 'echo -e \"[azure-cli]\nname=Azure CLI\nbaseurl=https://packages.microsoft.com/yumrepos/azure-cli\nenabled=1\ngpgcheck=1\ngpgkey=https://packages.microsoft.com/keys/microsoft.asc\" > /etc/yum.repos.d/azure-cli.repo' && sudo dnf install -y azure-cli"
    exit 1
fi

echo "1. Autenticando en Azure..."
# Verificamos si ya hay una sesión activa para no tener que loguearnos siempre
if az account show &> /dev/null; then
    echo "Ya tienes una sesión activa en Azure CLI. Continuando..."
else
    echo "Microsoft requiere autenticación con MFA (Segundo Factor), por lo que deberás usar el navegador para loguearte."
    echo "Iniciando sesión..."
    
    # Se intentará usar device-code y fallback al login habitual si device-code no te agrada o falla. 
    # Generalmente "az login" bastará.
    az login || {
        echo "Error: No se pudo completar el inicio de sesión interactivo."
        exit 1
    }
fi

# Intentar seleccionar automáticamente tu cuenta/tenante principal por precaución
az account set --name "$EMAIL" &> /dev/null || true

# Estableciendo la cuenta o tenante por defecto si aplica, 
# alternativamente el comando solicita explícitamente configurar si tienes múltiples subscripciones.
# az account set --subscription "<TU_ID_DE_SUBSCRIPCION>" # Descomenta y ajusta si manejas varias suscripciones

echo "2. Redirigiendo al directorio del backend..."
# Cambiamos al directorio de la aplicación banco_app
cd /home/edi/PROYECTOS/FONDO_CTeI/banco_app || exit 1

echo "3. Empacando archivos localmente en un archivo ZIP seguro..."
rm -f /tmp/bancoapp_deploy.zip 2>/dev/null
zip -q -r /tmp/bancoapp_deploy.zip . -x "*.git*" -x "*.vscode*" -x "*.env*"

echo "4. Desplegando NodeJS (Zip Deploy) en Azure App Service..."
if az webapp deployment source config-zip --src /tmp/bancoapp_deploy.zip \
    --name $APP_NAME \
    --resource-group $RESOURCE_GROUP; then

    echo "========================================="
    echo "¡Despliegue en Azure finalizado con éxito!"
    echo "Tu aplicación web está disponible de forma segura en: https://$APP_NAME.azurewebsites.net"
    echo "========================================="
else
    echo "=================================================================="
    echo "                 ⚠️ ¡ERROR EN EL DESPLIEGUE! ⚠️                  "
    echo "=================================================================="
    echo "La herramienta de Azure ha devuelto un error al procesar tu solicitud."
    echo "Dependiendo de lo que viste en la pantalla anterior, aquí hay posibles soluciones:"
    echo ""
    echo "▶ CASO 1: ERROR DE COMPILACIÓN (Build failed)"
    echo "  Revisa el enlace proporcionado arriba en 'Please check the build logs'."
    echo "  Por lo general, al subir código a la nube, Azure compila todo desde cero."
    echo "  Si da error, puede ser por librerías nativas incompatibles (como SQLite) o"
    echo "  una versión de Node.js cruzada. Asegúrate de ignorar 'node_modules' usando un archivo .azureignore."
    echo ""
    echo "▶ CASO 2: ERROR DE CUOTA DE TIPO DE MÁQUINA (Limit: 0 / Exceeded)"
    echo "  Tu suscripción institucional no tiene suficientes cuotas para los planes 'Dev/Test'."
    echo "  Si usas Free (F1), intenta cambiar la variable \$LOCATION (línea 8 del script)"
    echo "  a 'westus', 'southcentralus' o 'brazilsouth', ya que 'centralus' puede estar lleno."
    echo ""
    echo "▶ CASO 3: ERROR DE AUTENTICACIÓN"
    echo "  Tu sesión de consola expiró. Ejecuta 'az logout' seguido de 'az login' en tu terminal."
    echo "=================================================================="
    exit 1
fi
