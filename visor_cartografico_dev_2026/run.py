# =============================================================================
# SCRIPT DE EJECUCIÓN LOCAL - SERVIDOR DE DESARROLLO
# =============================================================================
# Este archivo es el punto de entrada para ejecutar la aplicación en modo desarrollo local.
# NO se usa en producción (Google App Engine usa gunicorn directamente).

# Importar la instancia de la aplicación Dash desde el módulo principal
from app.app import app

# Bloque principal: Se ejecuta solo cuando se llama directamente este script
if __name__ == '__main__':
    # Iniciar el servidor de desarrollo de Flask/Dash
    # - debug=True: Habilita el modo debug (auto-reload al detectar cambios, mensajes de error detallados)
    # - port=5001: Puerto en el que escucha el servidor (evita conflicto con puerto 5000 usado por AirPlay en macOS)
    app.run(debug=True, port=5001)