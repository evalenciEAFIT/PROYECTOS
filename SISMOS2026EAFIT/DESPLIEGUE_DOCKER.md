# Guía de Despliegue en la Nube mediante DOCKER

Empaquetar la aplicación en un contenedor de **Docker** es la práctica más robusta, moderna y portátil del desarrollo. Te garantiza que tu "Visor Cartográfico" funcionará y se configurará exactamente de la misma manera en AWS, Google Cloud, infraestructura local o Azure sin importar la distribución del servidor host subyacente.

En este repositorio ahora encontrarás el archivo `Dockerfile`. A continuación la guía paso a paso.

---

## Fase 1: Entorno Local y Envase (Build)

### 1. Requisitos

Asegúrate de contar con [Docker Desktop o Engine](https://docs.docker.com/get-docker/) corriendo en tu propia PC o en el equipo de despliegues (CI/CD).

### 2. Construir la Imagen (Docker Build)

Parado dentro de la carpeta del proyecto en la terminal (donde reside tu `run.py` y `Dockerfile`), ejecuta este comando para compilar el sistema abstracto:

```bash
docker build -t visor-sismico:latest .
```

*(Nota Técnica)* Si estás trabajando desde un Mac moderno procesador de Apple Silicon (M1, M2, M3) pero requieres montarlo en la gran mayoría de nubes nativas (que todavía priorizan procesadores de núcleo **Intel**), usa forzosamente banderas Cross-Environment para evitar errores de binarios y que a pesar de que el Build diga "Efectivo", Gunicorn falle en consola:

```bash
docker build --platform linux/amd64 -t visor-sismico:latest .
```

### 3. Ejecución de Pruebas "Production-Grade"

Testea si se compiló correctamente probando tu red de puertos interna conectándola con la abstracción del virtual docker (Se estandarizó a 8080):

```bash
docker run -p 8080:8080 visor-sismico:latest
```

Accede a `http://localhost:8080`.

---

## Fase 2: Pasos hacia Despliegues en la Nube (Cloud Providers)

Selecciona el enfoque de tu proveedor ideal que acopla con el Dockerfile empaquetado. Nosotros te enlistamos **dos recomendaciones base de bajo coste temporal**:

### Opción A (Evolución Natural): Google Cloud Run (Serverless)

Considerando que el sistema base contaba con `app.yaml` que apunta a `Google App Engine`, migrar al servicio moderno "Serverless" *Cloud Run* proveído por el mismo Google y dedicado en 100% a Dockers reducirá enormemente los fallos y limitantes de infraestructura del `App Engine Legacy`.

1. **Sube (Push) tu imagen alojada local a Google Cloud Registry / Artifact Registry:**

```bash
gcloud auth configure-docker
# Asumiendo que tu "id-de-proyecto" en gcp como se vió antes es 'riesgosismico'
docker tag visor-sismico:latest gcr.io/riesgosismico/visor-sismico
docker push gcr.io/riesgosismico/visor-sismico
```

2. **Lanzar la Imagen al aire:**

```bash
gcloud run deploy visor-sismico \
  --image gcr.io/riesgosismico/visor-sismico \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --cpu 2 \
  --memory 1Gi \
  --timeout 300
```

> ***¡Precaución fundamental!*** GeoPandas usa bases analíticas C++. Requieres agregar banderas como la memoria de mínimo `1Gi` explícita, ideal también `cpu 2`, o sobrepasarás los perfiles de la nube estandar forzando crasheas por escasez de RAM ("OOM - Out Of Memory") al desplegar GeoPackages pesados.

### Opción B: Despliegue en VM/Servidor Físico Integrado con Docker

Si no contratas una plataforma autoadministrada y tú mismo compraste la instancia (EC2 nativo, un Dropet en OceanPlatform o servideres EAFIT físicos) donde solamente se limitan a entregarte IPs y consolas SSH:

1. Levanta tu máquina de terminal (Server SSH) e instala Docker subyacente.
2. Clonas el repositorio tuyo desde *GitHub/Gitlab* (si es que la configuraste como privada) incluyendo este `Dockerfile`, y usas comando "build" allá adentro.
3. Para mantenerlo **"Vivo siempre y en modo background"**, usa la bandera de reinicio automatizado `Detach y Restart`. Te exponemos de una vez hacia el público general HTTP convencional en puerto global (El puerto 80):

```bash
docker run -d -p 80:8080 --name daemon-visor-sismico --restart always visor-sismico:latest
```

Ahora el navegador del ciudadano accede al Visor al poner la IP Pública externa del servidor sin poner los pueros `8080` de sufijo explícito en su URL.
