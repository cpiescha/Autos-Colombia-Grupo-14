# Autos Colombia — Grupo 14

Aplicación académica para gestionar la entrada y salida de vehículos del parqueadero Autos Colombia.

## Tecnologías

- Angular 22 y TypeScript
- FastAPI, Python 3.12 y SQLAlchemy
- PostgreSQL 16
- Docker Compose

## Requisitos

- Git
- Docker Desktop con Docker Compose

No es necesario instalar Angular, Python ni PostgreSQL en el equipo anfitrión.

## Configuración

1. Clonar el repositorio.
2. Crear el archivo local de variables de entorno:

   ```bash
   cp .env.example .env
   ```

3. Mantener los valores de desarrollo o reemplazarlos por valores locales no sensibles. El archivo `.env` no se versiona.

## Iniciar el entorno

```bash
docker compose up --build
```

Servicios disponibles:

- Frontend: <http://localhost:4200>
- Backend: <http://localhost:8080>
- Salud del backend: <http://localhost:8080/api/health>
- Documentación de la API: <http://localhost:8080/docs>

El backend usa `8080` en el equipo anfitrión porque está disponible en el entorno de desarrollo. Dentro de Docker conserva el puerto `8000`, por lo que la comunicación interna sigue usando `backend:8000`.

En el primer inicio, PostgreSQL ejecuta automáticamente `backend/scripts/schema.sql` y `backend/scripts/seed.sql`. Esto crea el esquema y carga las 80 celdas y los datos de prueba. Los scripts de inicialización solo se ejecutan cuando el volumen de PostgreSQL está vacío.

Comprobar el estado:

```bash
docker compose ps
curl http://localhost:8080/api/health
```

## Detener el entorno

```bash
docker compose down
```

El volumen nombrado `postgres_data` conserva la información de PostgreSQL cuando se detienen o recrean los contenedores de aplicación. Para reiniciar únicamente las aplicaciones:

```bash
docker compose restart frontend backend
```

> `docker compose down -v` elimina el volumen y todos los datos locales; usarlo solo cuando se quiera reiniciar la base desde cero. El siguiente `docker compose up --build` volverá a crear el esquema y cargar las semillas automáticamente.

## Pruebas del backend

```bash
cd backend
python -m venv .venv
# Windows PowerShell: .venv\Scripts\Activate.ps1
# Bash: source .venv/Scripts/activate
pip install -r requirements-dev.txt
pytest
```

## Estructura inicial

```text
frontend/            Aplicación Angular
backend/app/         API FastAPI
backend/tests/       Pruebas del backend
docker-compose.yml   Entorno local reproducible
.env.example         Variables locales de ejemplo
```

Esta base corresponde a T01. Los modelos, restricciones, semillas y reglas de negocio se implementan en las tareas posteriores del plan.
