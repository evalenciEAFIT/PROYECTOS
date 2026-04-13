# FONDO_CTeI — Plataforma de Gestión de Fondos de Investigación

Sistema web para la **administración y trazabilidad de recursos financieros** del Fondo de Ciencia, Tecnología e Innovación (CTeI) de la Universidad EAFIT.

---

## ¿Qué problema resuelve?

La gestión de fondos de investigación en una universidad involucra múltiples actores (docentes, grupos de investigación, vicerrectoría) y flujos financieros complejos que históricamente se manejaban en hojas de cálculo, sin trazabilidad ni control de estados.

**FONDO_CTeI** centraliza este proceso proporcionando:

- **Visibilidad en tiempo real** del saldo, ingresos y egresos por cuenta.
- **Flujo de aprobación** para solicitudes de gasto, con historial auditado de estados.
- **Jerarquías de cuentas** que permiten ver el movimiento consolidado de un grupo de investigación o escuela.
- **Autenticación institucional** via Active Directory o Azure SSO de EAFIT, sin gestión de contraseñas propias.
- **Categorización configurable** de movimientos (ingresos, egresos, transferencias).

---

## ¿Qué hace la aplicación?

### 📊 Dashboard Financiero
Vista consolidada por cuenta con KPIs: saldo actual, total de ingresos y egresos.

### 💸 Gestión de Transacciones
Registro de movimientos financieros clasificados en tres tipos:
- **Ingresos**: Transferencia Fondo CTeI, Reconocimiento en Investigación, Donaciones, etc.
- **Egresos**: Insumos, Infraestructura, Eventos académicos, Reactivos, etc.
- **Transferencias**: Entre cuentas de la comunidad académica.

### 🔄 Flujo de Aprobación (Estado de solicitudes)
Los egresos pasan por un ciclo de estados con historial auditado:

```
solicitada → en estudio → aprobada / rechazada → en ejecución → terminada
```

Cada cambio de estado registra la fecha y un comentario del responsable.

### 🏛️ Jerarquías de Cuentas
Un cabecera (ej. Vicerrectoría) puede ver el consolidado de todas las cuentas dependientes (grupos de investigación, escuelas).

### 📡 Actualizaciones en Tiempo Real
Usa Server-Sent Events (SSE) para reflejar cambios inmediatamente en todos los navegadores conectados, sin necesidad de recargar.

### 🔒 Autenticación Institucional
Dos modos de autenticación según entorno:
- **LDAP / Active Directory** EAFIT (`ldap://ad.eafit.edu.co:389`)
- **Azure SSO** — el usuario se autentica en Microsoft y la plataforma verifica que su cuenta esté registrada.

### 💾 Backup
Descarga directa de la base de datos SQLite desde la interfaz (`/api/backup-db`).

---

## Stack Tecnológico

| Capa | Tecnología |
|------|-----------|
| Backend | Node.js + Express |
| Base de Datos | SQLite3 |
| Autenticación | LDAP (ldapjs) + Azure Entra ID (SSO) |
| Frontend | HTML5 + CSS3 + JavaScript Vanilla |
| Despliegue | Azure App Service, Azure Container |
| Tiempo Real | Server-Sent Events (SSE) |

---

## Estructura del Proyecto

```
FONDO_CTeI/
├── banco_app/              # Aplicación principal
│   ├── index.js            # Servidor Express + todas las rutas API
│   ├── views/index.html    # Frontend (SPA en HTML/CSS/JS)
│   ├── public/             # Assets estáticos (CSS, JS, logos)
│   ├── categorias.json     # Categorías de transacciones (editable)
│   ├── banco.db            # Base de datos SQLite (no versionada)
│   ├── .env.template       # Plantilla de variables de entorno
│   └── package.json
├── init_db.py              # Script de inicialización / migración de BD
├── datos-FONDOSCTeI.xlsx   # Datos fuente originales (Excel)
├── deploy.sh               # Despliegue estándar
├── deploy_azure.sh         # Despliegue en Azure App Service
├── deploy_training.sh      # Despliegue en entorno de entrenamiento
└── rama.sh                 # Script de sincronización con GitHub
```

---

## Instalación y Ejecución Local

### Prerequisitos
- Node.js >= 18.x
- npm >= 9.x

### Pasos

```bash
# 1. Instalar dependencias
cd banco_app
npm install

# 2. Configurar variables de entorno
cp .env.template .env
# Editar .env según el entorno (ver sección de configuración)

# 3. Inicializar la base de datos (primera vez)
cd ..
python3 init_db.py

# 4. Iniciar servidor de desarrollo
cd banco_app
npm run dev
```

La aplicación quedará disponible en: **http://localhost:3000**

> **Credencial de desarrollo**: usuario `admin`, contraseña `123`.

---

## Configuración (`.env`)

```env
PORT=3000

# Habilitar validación con Active Directory EAFIT
USE_ACTIVE_DIRECTORY=false
LDAP_URL=ldap://ad.eafit.edu.co:389
```

---

## API — Endpoints Principales

| Método | Ruta | Descripción |
|--------|------|-------------|
| `POST` | `/api/login` | Login local o vía LDAP |
| `POST` | `/api/azure-login` | Login post-SSO Azure |
| `GET` | `/api/cuentas` | Listado de cuentas + jerarquías |
| `POST` | `/api/cuentas` | Crear cuenta nueva |
| `PUT` | `/api/cuentas/:id` | Actualizar datos de cuenta |
| `GET` | `/api/resumen` | KPIs financieros del dashboard |
| `POST` | `/api/cuentas/:id/transaccion` | Registrar transacción |
| `GET` | `/api/cuentas/:id/transacciones` | Historial de una cuenta |
| `GET` | `/api/movimientos` | Todos los movimientos (con jerarquía) |
| `PUT` | `/api/transacciones/:id/estado` | Cambiar estado de solicitud |
| `GET` | `/api/categorias` | Obtener categorías configuradas |
| `PUT` | `/api/categorias` | Actualizar categorías |
| `GET` | `/api/stream` | Stream SSE de actualizaciones |
| `GET` | `/api/backup-db` | Descargar backup de la BD |

---

## Despliegue en Azure

```bash
# Despliegue en Azure App Service
./deploy_azure.sh

# Despliegue en entorno de entrenamiento
./deploy_training.sh
```

---

## Sincronización con GitHub

```bash
# Desde la raíz del proyecto
./rama
```

Este script sincroniza el código fuente al repositorio `evalenciEAFIT/PROYECTOS/FONDO_CTeI` excluyendo automáticamente: `node_modules/`, archivos `.db` (datos sensibles) y `.env`.

---

## Desarrollado por

**Universidad EAFIT** — Vicerrectoría de Investigación  
Escuela de Ingeniería y Ciencias Aplicadas
