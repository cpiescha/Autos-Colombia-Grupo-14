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

## Datos de demostración

La carga es idempotente e incluye 80 celdas, varios carros y motos con mensualidad vigente, un caso vencido y dos permanencias abiertas para probar salida.

| Uso | Datos |
|---|---|
| Ingreso de carros | `ABC123`, `CAR101`, `CAR202`, `CAR303`, `DEF456` |
| Ingreso de motos | `XYZ99A`, `MOT101`, `MOT202` |
| Rechazo por mensualidad vencida | `VEN001` |
| Salida de carro | comprobante `AC-INS001-OPEN` |
| Salida de moto | comprobante `AC-MOT303-OPEN` |

En una base ya creada, aplicar las nuevas semillas sin borrar movimientos existentes:

```bash
docker compose exec -T db psql -U autos_colombia -d autos_colombia < backend/scripts/seed.sql
```

## Recorrido de entrega

1. Consultar una placa vigente o vencida.
2. Registrar una entrada; la API asigna una celda compatible y genera el comprobante.
3. Registrar la salida usando obligatoriamente el comprobante y confirmar la vista previa.
4. Revisar ocupación, vehículos presentes y reportes.
5. Corregir la celda de una permanencia abierta desde **Vehículos presentes**.

El registro guiado y los datos esperados están en [`docs/VERIFICACION_MANUAL_ITERACION_1.md`](docs/VERIFICACION_MANUAL_ITERACION_1.md).

## Verificaciones automatizadas (pendientes)

El proyecto conserva las pruebas en `backend/tests/`, pero las pruebas unitarias, de integración y la prueba concurrente T13 se ejecutarán en una etapa posterior según la decisión del equipo. No se declara T13 verificada hasta probar dos ingresos simultáneos contra PostgreSQL.

Cuando corresponda ejecutarlas:

```bash
cd backend
python -m venv .venv
# Windows PowerShell: .venv\Scripts\Activate.ps1
# Bash: source .venv/Scripts/activate
pip install -r requirements-dev.txt
pytest
```

## Estructura

```text
frontend/            Aplicación Angular
backend/app/         API FastAPI
backend/scripts/     Esquema, restricciones y semillas PostgreSQL
backend/tests/       Pruebas automatizadas pendientes de ejecución final
docs/                Recorrido y evidencia manual
docker-compose.yml   Entorno local reproducible
.env.example         Variables locales de ejemplo
```
