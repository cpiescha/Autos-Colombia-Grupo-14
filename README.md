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

## Cargar los datos de prueba

El archivo `backend/scripts/seed.sql` es un script SQL que llena PostgreSQL con los datos iniciales necesarios para probar la aplicación: celdas, clientes, vehículos, mensualidades, operarios, permanencias abiertas y comprobantes. A este tipo de archivo también se lo conoce como **semilla**.

### Base nueva

No hay que ejecutar el archivo manualmente. Al usar por primera vez:

```bash
docker compose up --build
```

PostgreSQL ejecuta primero `backend/scripts/schema.sql` para crear las tablas y después `backend/scripts/seed.sql` para cargar los datos.

### Base ya creada

Si el volumen `postgres_data` ya existe, Docker no vuelve a ejecutar los scripts iniciales. Aplicar la semilla manualmente según la terminal:

**Git Bash, Linux o macOS**

```bash
docker compose exec -T db psql -U autos_colombia -d autos_colombia < backend/scripts/seed.sql
```

**PowerShell**

```powershell
Get-Content backend/scripts/seed.sql -Raw |
  docker compose exec -T db psql -U autos_colombia -d autos_colombia
```

El script es repetible: conserva los movimientos y comprobantes existentes, no duplica los catálogos principales y no recrea una permanencia de demostración que ya fue cerrada. Para restaurar exactamente los dos casos de salida iniciales se debe reiniciar voluntariamente el volumen con `docker compose down -v` y volver a levantar el entorno.

### Datos disponibles

| Uso | Datos |
|---|---|
| Ingreso de carros | `ABC123`, `CAR101`, `CAR202`, `CAR303`, `DEF456` |
| Ingreso de motos | `XYZ99A`, `MOT101`, `MOT202` |
| Rechazo por mensualidad vencida | `VEN001` |
| Salida de carro en una base nueva | comprobante `AC-INS001-OPEN` |
| Salida de moto en una base nueva | comprobante `AC-MOT303-OPEN` |

En una base que ya tenía movimientos, consultar **Vehículos presentes** para usar el comprobante activo que se conserva en esa permanencia.

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

## Partes del proyecto

La aplicación sigue una arquitectura de tres capas. Angular presenta los formularios y resultados; FastAPI aplica las reglas de negocio; PostgreSQL conserva el estado. El frontend nunca asigna una celda por cuenta propia.

```text
frontend/
  src/app/pages/       Pantallas de entrada, salida, ocupación, reportes y corrección
  src/app/services/    Comunicación HTTP con FastAPI
  src/app/models/      Tipos usados por las pantallas
backend/
  app/api/             Endpoints HTTP
  app/services/        Reglas de entrada, salida, ocupación y corrección
  app/models/          Entidades SQLAlchemy
  app/schemas/         Datos de entrada y respuesta de la API
  app/db/              Conexión y operaciones de PostgreSQL
  scripts/schema.sql   Tablas, tipos, relaciones y restricciones
  scripts/seed.sql     Datos iniciales y casos de demostración
  tests/               Pruebas automatizadas pendientes de ejecución final
docs/                  Recorrido y evidencia manual
docker-compose.yml     Inicia frontend, backend y PostgreSQL
.env.example           Variables de entorno de desarrollo
```

### Flujo de una operación

1. El usuario realiza una acción en Angular.
2. `AccesoService` envía la solicitud a `/api`.
3. FastAPI valida la mensualidad, el vehículo, el comprobante y la disponibilidad.
4. PostgreSQL guarda el movimiento dentro de una transacción.
5. FastAPI devuelve la celda o el resultado confirmado y Angular lo muestra.

Para conocer todos los endpoints disponibles, iniciar el entorno y abrir <http://localhost:8080/docs>.
