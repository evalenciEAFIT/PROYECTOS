# Guía de Despliegue en Servidor Propio (VPS o Físico)

Actualmente, el proyecto está configurado para desplegarse fácilmente en **Google App Engine** mediante `app.yaml` y el script `deploy.sh`. Sin embargo, si deseas hacer el despliegue en un servidor propio Linux (por ejemplo: Ubuntu/Debian en AWS EC2, DigitalOcean, o un servidor físico en las instalaciones del DAGRAN/EAFIT), esta guía te mostrará el paso a paso profesional.

La arquitectura recomendada para producción en un servidor propio es:
`Nginx (Proxy Inverso + Servidor de Estáticos)` ➔ `Gunicorn (Servidor WSGI)` ➔ `Aplicación Dash (Flask)`

---

## Paso 1: Requisitos Previos en el Servidor

Accede por SSH a tu servidor y asegúrate de tener instalados los paquetes base y Python 3.12 (u otra versión compatible con Dash y GeoPandas).

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y python3-pip python3-venv nginx git
```

⚠️ **Nota importante de librerías geoespaciales:** La librería `geopandas` en producción requiere paquetes del sistema operativo C++ subyacentes.

```bash
sudo apt install -y gdal-bin libgdal-dev build-essential
```

---

## Paso 2: Copiar el Código y Preparar Entorno Virtual

Sube los archivos de este directorio a una carpeta en tu servidor. Supongamos que lo alojarás en `/var/www/visor_cartografico`.

```bash
# Navegar a la carpeta del proyecto
cd /var/www/visor_cartografico

# Crear el entorno virtual (aislamiento de dependencias)
python3 -m venv venv

# Activar el entorno virtual
source venv/bin/activate

# Instalar los requerimientos. Se asume que Gunicorn está incluido por el app.yaml
pip install -r requirements.txt
```

---

## Paso 3: Probar Gunicorn Manualmente

Gunicorn actuará como el servidor "fuerte" multiproceso. El script `run.py` o el comando `flask run` NO deben usarse en producción. Para probar que Gunicorn funciona, ejecuta:

```bash
# Estamos apuntando al objeto 'server' que está dentro de app/app.py
gunicorn --bind 0.0.0.0:8000 app.app:server --workers 3 --timeout 120
```

* **--workers 3:** Se recomienda asignar `(2 x Número de Cores CPU) + 1`.
* **--timeout 120:** Dash Leaflet cargando GeoPackages puede tomar un poco; 120 segundos es el mismo timeout usado en el App Engine.

Presiona `CTRL+C` para detenerlo si no arrojó errores graves.

---

## Paso 4: Crear Servicio con `systemd` (Demonio)

Para que Gunicorn arranque automáticamente al prender el servidor y se reinicie en caso de caída, creamos un servicio del sistema.

Crea un archivo llamado `/etc/systemd/system/visor.service`:

```bash
sudo nano /etc/systemd/system/visor.service
```

Con el siguiente contenido (Ajusta el usuario y rutas si lo clonaste diferente):

```ini
[Unit]
Description=Gunicorn daemon para Visor Cartografico Riesgo Sismico
After=network.target

[Service]
User=tu_usuario_servidor
Group=www-data
WorkingDirectory=/var/www/visor_cartografico
Environment="PATH=/var/www/visor_cartografico/venv/bin"
# Ejecutar gunicorn mapeando al puerto 8000 exclusivamente interno
ExecStart=/var/www/visor_cartografico/venv/bin/gunicorn --workers 3 --bind 127.0.0.1:8000 app.app:server --timeout 120

[Install]
WantedBy=multi-user.target
```

Inicia y habilita el servicio para siempre:

```bash
sudo systemctl start visor
sudo systemctl enable visor
```

---

## Paso 5: Nginx como Proxy Inverso

Configura Nginx para que escuche por el puerto 80 (y 443 para HTTPS) y direccione el tráfico hacia el Gunicorn que está corriendo internamente.

Crea un sitio de Nginx:

```bash
sudo nano /etc/nginx/sites-available/visor
```

Escribe lo siguiente:

```nginx
server {
    listen 80;
    server_name tu_dominio.com o_tu_ip_publica;

    # Opcional pero recomendado: Servir assets directamente desde Nginx (Muy veloz)
    location /assets {
        alias /var/www/visor_cartografico/app/assets;
    }

    # Proxy a la app Dash
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

Activa la configuración creando un enlace simbólico y reinicia:

```bash
sudo ln -s /etc/nginx/sites-available/visor /etc/nginx/sites-enabled
sudo nginx -t     # Validar sintaxis
sudo systemctl restart nginx
```

---

## Paso 6 (Opcional): Seguridad Certificado SSL Gratis

Si el visor cuenta con un dominio válido (e.g., `visor.eafit.edu.co` o `riesgo-sismico.co`), deberías habilitar el candado de seguridad (HTTPS).

```bash
sudo apt install certbot python3-certbot-nginx -y
sudo certbot --nginx -d tu_dominio.com
```

¡Y eso es todo! La arquitectura responderá con la misma fluidez y robustez que un despliegue convencional en la nube de Google.
