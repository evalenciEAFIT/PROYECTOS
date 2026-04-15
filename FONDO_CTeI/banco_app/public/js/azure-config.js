/**
 * ARCHIVO DE CONFIGURACIÓN DE AZURE AD
 * -------------------------------------------------------------
 * Administre aquí los parámetros de conexión SSO al inquilino de Azure.
 * Este archivo no debe ser alterado dinámicamente.
 */

window.AZURE_CONFIG = {
    // 1. Client ID (Application ID) de la aplicación registrada en Entra ID / Azure AD
    clientId: "TU_AZURE_CLIENT_ID",

    // 2. Directorio (Tenant)
    // Para admitir múltiples organizaciones Microsoft (Multi-tenant): "https://login.microsoftonline.com/common"
    // Para admitir SOLO usuarios @eafit.edu.co: "https://login.microsoftonline.com/TU_TENANT_ID_AQUI"
    authority: "https://login.microsoftonline.com/common",

    // 3. URL a la que Azure regresará tras el inicio de sesión exitoso.
    // Usar 'window.location.origin' lo ajusta automáticamente al dominio actual (ej: localhost o servidor prod)
    redirectUri: window.location.origin
};
