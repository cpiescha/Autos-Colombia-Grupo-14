# Autos Colombia — Grupo 14

Aplicación académica para gestionar la entrada y salida de vehículos del parqueadero **Autos Colombia**. Permite registrar vehículos, controlar la ocupación por categoría (automóvil y moto), emitir comprobantes de entrada y salida, corregir asignaciones de celda y auditar la operación bajo cuentas internas con perfiles diferenciados.

La Iteración 2 agrega autenticación con token firmado, administración de operadores y celdas, y pruebas opt-in de concurrencia real sobre PostgreSQL 16.

---

## Tabla de contenido

- [Qué hace la aplicación](#qué-hace-la-aplicación)
- [Perfiles y permisos](#perfiles-y-permisos)
- [Tecnologías](#tecnologías)
- [Arquitectura](#arquitectura)
- [Requisitos](#requisitos)
- [Configuración local](#configuración-local)
- [Iniciar el entorno con Docker](#iniciar-el-entorno-con-docker)
- [Cuentas iniciales](#cuentas-iniciales)
- [Datos de prueba](#datos-de-prueba)
- [Recorrido de entrega](#recorrido-de-entrega)
- [Endpoints principales](#endpoints-principales)
- [Verificaciones automatizadas](#verificaciones-automatizadas)
- [Despliegue y publicación](#despliegue-y-publicación)
- [Solución de problemas](#solución-de-problemas)
- [Estructura del repositorio](#estructura-del-repositorio)
- [Documentación complementaria](#documentación-complementaria)

---

## Qué hace la aplicación

- **Entrada de vehículos**: valida la placa contra el registro interno, asigna automáticamente una celda compatible con la categoría y genera un comprobante con número único.
- **Salida de vehículos**: se realiza exclusivamente con el comprobante activo, muestra una vista previa de la permanencia y confirma el movimiento en una transacción.
- **Ocupación y vehículos presentes**: lista en tiempo real las celdas ocupadas, libres e inactivas y permite consultar los comprobantes abiertos.
- **Corrección de celda**: desde **Vehículos presentes** se puede corregir la celda de una permanencia abierta cuando el vehículo quedó mal ubicado. Queda registrada la cuenta responsable.
- **Administración de celdas**: alta, cambio de estado (activa/inactiva) y baja. Una celda con historial no se elimina físicamente: se inactiva para conservar auditoría.
- **Administración de operadores**: alta, listado y anulación lógica. Las cuentas anuladas conservan el historial relacionado.
- **Administración de vehículos y clientes**: consulta de clientes registrados y alta de vehículos asociados. No hay CRUD completo de clientes en esta entrega.
- **Reportes e historial**: consulta la ocupación actual y recupera desde PostgreSQL las permanencias cerradas con sus operadores, comprobantes y correcciones de celda, incluso después de recargar la aplicación.
- **Auditoría**: cada entrada, corrección y salida persiste la cuenta responsable. Las cuentas anuladas pierden acceso aunque conserven un token no vencido.

## Perfiles y permisos

| Capacidad | OPERADOR | ADMINISTRADOR |
|---|:---:|:---:|
| Iniciar sesión | ✔ | ✔ |
| Registrar entradas, correcciones y salidas | ✔ | ✔ |
| Consultar ocupación, vehículos presentes y reportes | ✔ | ✔ |
| Alta y edición de operadores | — | ✔ |
| Alta, edición y baja de celdas | — | ✔ |
| Alta de vehículos y consulta de clientes | — | ✔ |

Un operador autenticado que intenta un recurso administrativo recibe `403 FORBIDDEN`. Una solicitud sin sesión recibe `401 INVALID_SESSION`.

---

## Tecnologías

- **Frontend**: Angular 22 + TypeScript
- **Backend**: FastAPI + Python 3.12 + SQLAlchemy
- **Base de datos**: PostgreSQL 16
- **Orquestación**: Docker Compose
- **Autenticación**: JWT firmado (HS256) con TTL configurable y revalidación de la cuenta en cada request

## Arquitectura

Tres capas separadas. Angular presenta formularios y resultados; FastAPI concentra las reglas de negocio; PostgreSQL conserva el estado. El frontend nunca asigna una celda por cuenta propia.

```text
┌──────────────┐    HTTPS/REST    ┌──────────────┐    SQL     ┌──────────────┐
│  Angular 22  │ ───────────────▶ │  FastAPI     │ ─────────▶ │ PostgreSQL 16│
│  :4200       │   Bearer token   │  :8000/8080  │            │  :5432       │
└──────────────┘                  └──────────────┘            └──────────────┘
```

Flujo de una operación autenticada:

1. El empleado inicia sesión; Angular guarda el token y lo revalida con `GET /api/auth/me`.
2. Un interceptor adjunta `Authorization: Bearer <token>` a toda llamada `/api`.
3. FastAPI vuelve a consultar la cuenta activa y aplica los permisos del perfil.
4. FastAPI valida las reglas del vehículo, la celda y el movimiento.
5. PostgreSQL guarda los cambios junto con la cuenta responsable dentro de una transacción.
6. Angular muestra solo el resultado confirmado por la API.

El detalle técnico está en [`docs/ARQUITECTURA_TECNICA_AUTOS_COLOMBIA.md`](docs/ARQUITECTURA_TECNICA_AUTOS_COLOMBIA.md).

---

## Requisitos

- Git
- Docker Desktop con Docker Compose v2

No es necesario instalar Angular, Python ni PostgreSQL en el equipo anfitrión; todo corre dentro de contenedores.

## Configuración local

1. Clonar el repositorio:

   ```bash
   git clone https://github.com/cpiescha/Autos-Colombia-Grupo-14.git
   cd Autos-Colombia-Grupo-14
   ```

2. Crear el archivo local de variables de entorno:

   ```bash
   cp .env.example .env
   ```

3. Definir un `AUTH_SECRET` aleatorio de **al menos 32 caracteres**. Sin esta variable, Compose se detiene y no levanta el backend. Un ejemplo seguro para generar uno:

   ```bash
   # Linux/macOS/Git Bash
   openssl rand -hex 32

   # PowerShell
   -join ((48..57) + (65..90) + (97..122) | Get-Random -Count 48 | ForEach-Object { [char]$_ })
   ```

   Pegar el resultado en `AUTH_SECRET=` dentro de `.env`.

4. (Opcional) Ajustar los puertos locales si `4200` u `8080` están ocupados.

### Variables de entorno

| Variable | Uso | Valor por defecto |
|---|---|---|
| `AUTH_SECRET` | Firma los tokens de acceso (mínimo 32 caracteres) | **Obligatoria, sin valor por defecto** |
| `AUTH_TTL_MINUTES` | Duración del token en minutos | `60` |
| `AUTH_ALGORITHM` | Algoritmo JWT permitido | `HS256` |
| `POSTGRES_DB` | Nombre de la base de datos | `autos_colombia` |
| `POSTGRES_USER` | Usuario de PostgreSQL | `autos_colombia` |
| `POSTGRES_PASSWORD` | Contraseña de PostgreSQL | `autos_colombia_dev` |
| `BACKEND_PORT` | Puerto del backend en el host | `8080` |
| `FRONTEND_PORT` | Puerto del frontend en el host | `4200` |

El archivo `.env` está en `.gitignore` y no se versiona.

---

## Iniciar el entorno con Docker

```bash
docker compose up --build
```

Al terminar el arranque, los servicios quedan disponibles en:

- **Frontend**: <http://localhost:4200>
- **Backend**: <http://localhost:8080>
- **Salud del backend**: <http://localhost:8080/api/health>
- **Documentación interactiva de la API**: <http://localhost:8080/docs>

Para dejarlo corriendo en segundo plano:

```bash
docker compose up --build -d
docker compose ps
```

Verificar el estado:

```bash
docker compose ps
curl http://localhost:8080/api/health
```

### Detener el entorno

```bash
docker compose down
```

El volumen nombrado `postgres_data` conserva los datos cuando se detienen o recrean los contenedores. Para reiniciar solo las aplicaciones:

```bash
docker compose restart frontend backend
```

### Reiniciar desde cero

```bash
docker compose down -v
docker compose up --build
```

> `down -v` elimina el volumen y todos los datos locales. Úsese solo cuando se quiera reiniciar la base desde cero. El siguiente `up --build` vuelve a ejecutar `schema.sql` y `seed.sql`.

### Ver logs

```bash
docker compose logs -f backend
docker compose logs -f frontend
docker compose logs -f db
```

---

## Cuentas iniciales

El seed automático crea tres cuentas internas con contraseñas hasheadas con bcrypt:

| Usuario | Clave | Rol |
|---|---|---|
| `admin` | `Admin2026` | ADMINISTRADOR |
| `operario1` | `Operario2026` | OPERADOR |
| `operario2` | `Operario2026` | OPERADOR |

Las cuentas se crean una única vez, cuando PostgreSQL ejecuta `backend/scripts/schema.sql` y `backend/scripts/seed.sql` sobre un volumen vacío. Si el volumen ya existe, Docker **no** vuelve a ejecutarlos; en ese caso usar el bloque [Base ya creada](#base-ya-creada) o reiniciar el volumen con `docker compose down -v`.

> **Cambiar las contraseñas** antes de cualquier despliegue real: generar un hash nuevo con bcrypt y actualizar `user_accounts.password_hash` mediante un script SQL propio.

---

## Datos de prueba

El archivo `backend/scripts/seed.sql` llena PostgreSQL con los datos iniciales (celdas, clientes, vehículos, mensualidades, operarios, permanencias abiertas y comprobantes). A este tipo de archivo también se lo conoce como **semilla**.

### Base nueva

No hay que ejecutar nada manual. En el primer `docker compose up --build`, PostgreSQL corre `schema.sql` y luego `seed.sql` automáticamente.

### Base ya creada

Si el volumen `postgres_data` ya existe y se quiere incorporar cuentas internas y celdas administrables sin borrar los movimientos existentes, ejecutar `t17_user_accounts.sql`, `t18_parking_spots.sql` y `seed.sql` dentro de una sola transacción.

**Git Bash, Linux o macOS**

```bash
cat backend/scripts/t17_user_accounts.sql \
    backend/scripts/t18_parking_spots.sql \
    backend/scripts/seed.sql |
  docker compose exec -T db psql \
    -v ON_ERROR_STOP=1 \
    --single-transaction \
    -U autos_colombia \
    -d autos_colombia
```

**PowerShell**

```powershell
Get-Content -Raw @(
  "backend/scripts/t17_user_accounts.sql"
  "backend/scripts/t18_parking_spots.sql"
  "backend/scripts/seed.sql"
) |
  docker compose exec -T db psql `
    -v ON_ERROR_STOP=1 `
    --single-transaction `
    -U autos_colombia `
    -d autos_colombia
```

`ON_ERROR_STOP` junto con `--single-transaction` evita conservar una actualización parcial si alguno falla. Los movimientos y comprobantes existentes se mantienen.

### Datos disponibles

| Uso | Datos |
|---|---|
| Ingreso de carros | `ABC123`, `CAR101`, `CAR202`, `CAR303`, `DEF456` |
| Ingreso de motos | `XYZ99A`, `MOT101`, `MOT202` |
| Rechazo por mensualidad vencida | `VEN001` |
| Salida de carro en una base nueva | comprobante `AC-INS001-OPEN` |
| Salida de moto en una base nueva | comprobante `AC-MOT303-OPEN` |

En una base con movimientos propios, consultar **Vehículos presentes** para obtener el comprobante activo.

---

## Recorrido de entrega

1. Iniciar sesión como `operario1` o `admin`.
2. Consultar una placa vigente o vencida.
3. Registrar una entrada; la API asigna una celda compatible y emite el comprobante.
4. Registrar la salida usando el comprobante y confirmar la vista previa.
5. Revisar ocupación, vehículos presentes y el historial de permanencias cerradas y correcciones.
6. Corregir la celda de una permanencia abierta desde **Vehículos presentes**.
7. (Admin) Crear un operador y una celda, inactivarlos y verificar que las cuentas anuladas quedan sin acceso.

El registro guiado completo y los datos esperados están en [`docs/VERIFICACION_MANUAL_ITERACION_1.md`](docs/VERIFICACION_MANUAL_ITERACION_1.md).

---

## Endpoints principales

Lista no exhaustiva. La definición completa está en <http://localhost:8080/docs>.

### Autenticación (T19)

- `POST /api/auth/login`: valida usuario/clave y devuelve un token Bearer.
- `GET /api/auth/me`: devuelve la cuenta activa asociada al token.
- `POST /api/auth/logout`: valida la sesión; el frontend elimina el token local.

El backend vuelve a consultar la cuenta en cada solicitud autenticada, por lo que una cuenta anulada deja de operar aunque su token siga vigente.

### Administración de operadores (T20, solo ADMINISTRADOR)

- `GET /api/operadores`: lista cuentas con rol `OPERADOR`.
- `POST /api/operadores`: crea una cuenta activa con rol `OPERADOR`. La clave debe tener entre 8 y 72 bytes y se guarda con bcrypt.
- `PATCH /api/operadores/{id}/estado`: recibe `{"estado":"ACTIVA"}` o `{"estado":"ANULADA"}`.

Usuario repetido devuelve `409 USERNAME_EXISTS`. El alta normaliza el usuario a minúsculas y admite letras, números, punto y guion bajo después de una letra inicial.

### Administración de celdas (T21)

- `GET /api/celdas`: operador o administrador; devuelve ID, código, categoría, estado, placa actual e historial.
- `POST /api/celdas`: solo administrador; `codigo` y `categoria` (`MOTO` o `AUTOMOVIL`).
- `PATCH /api/celdas/{id}`: solo administrador; `{"estado":"ACTIVA"}` o `{"estado":"INACTIVA"}`.
- `DELETE /api/celdas/{id}`: solo administrador; elimina físicamente si no tiene historial; si lo tiene, la inactiva.

Una celda ocupada no puede inactivarse ni retirarse (`409 SPOT_OCCUPIED`). Las celdas inactivas quedan fuera de la asignación automática y de las correcciones.

### Operación (T22-T25)

- `POST /api/entradas`: registra la entrada y asigna una celda compatible.
- `POST /api/correcciones`: corrige la celda de una permanencia abierta.
- `POST /api/salidas/preview`: vista previa de la salida.
- `POST /api/salidas`: confirma la salida.
- `GET /api/movimientos/activos`: lista las permanencias abiertas.
- `GET /api/movimientos/historial`: recupera permanencias cerradas y sus correcciones persistidas.
- `GET /api/reportes/ocupacion`: resume capacidad y ocupación actual.

---

## Verificaciones automatizadas

### Suite rápida (SQLite en memoria)

```bash
cd backend
python -m venv .venv
# Windows PowerShell: .venv\Scripts\Activate.ps1
# Bash: source .venv/Scripts/activate
pip install -r requirements-dev.txt
pytest
```

### T26 — Concurrencia real contra PostgreSQL 16

Opt-in: no corre en la suite rápida y requiere Docker arriba.

```bash
RUN_T26_DOCKER=1 .venv/Scripts/python.exe -m pytest -q tests/test_t26_runtime.py
```

Cubre: dos operadores simultáneos sin compartir celda, competencia por la única celda compatible (`FOR UPDATE SKIP LOCKED`), negación a operadores, auditoría de vehículos, invalidación de sesión al anular una cuenta, y regresión del flujo entrada → corrección → reporte → vista previa → salida.

El resultado y los escenarios están en [`docs/VERIFICACION_T26.md`](docs/VERIFICACION_T26.md).

---

## Despliegue y publicación

Esta entrega está pensada para evaluación académica local con Docker Compose. Lineamientos mínimos para un entorno expuesto:

1. **Secretos**: nunca versionar `.env`. Generar `AUTH_SECRET` y `POSTGRES_PASSWORD` con alta entropía por entorno y rotarlos. Usar el gestor de secretos del proveedor (AWS Secrets Manager, Azure Key Vault, GitHub Actions secrets, etc.).
2. **Credenciales por defecto**: antes de exponer la app, cambiar las contraseñas de `admin`, `operario1` y `operario2`.
3. **Red**: publicar únicamente el frontend (`:4200`) y la API (`:8080`) detrás de un reverse proxy con TLS (Nginx, Caddy o Traefik). PostgreSQL no debe exponer puertos al host.
4. **Persistencia**: en producción, respaldar el volumen `postgres_data` con una política de backups del proveedor; no depender del volumen local de Docker.
5. **Compose de producción**: separar un `docker-compose.prod.yml` sin bind-mounts de código, con `restart: always` y variables provistas por el entorno, no por `.env`.
6. **Observabilidad**: habilitar logs centralizados (`docker compose logs` → agregador) y un monitor sobre `/api/health`.

### Publicar los cambios en GitHub

```bash
git checkout -b feat/mi-cambio
# trabajar, commitear en slices chicas
git push -u origin feat/mi-cambio
gh pr create --base main --head feat/mi-cambio --fill
```

Convención de commits: [Conventional Commits](https://www.conventionalcommits.org/) (`feat:`, `fix:`, `test:`, `docs:`, `chore:` …).

---

## Solución de problemas

| Síntoma | Causa probable | Acción |
|---|---|---|
| `required variable AUTH_SECRET is missing a value` | `.env` no definido o `AUTH_SECRET` vacío | Crear `.env` desde `.env.example` y asignar una cadena ≥ 32 caracteres |
| Login válido falla con `401` | Token firmado con otro `AUTH_SECRET` | Volver a loguearse después de regenerar el secreto |
| Las cuentas iniciales no existen | El volumen `postgres_data` se creó sin los scripts actualizados | Ejecutar el bloque [Base ya creada](#base-ya-creada) o `docker compose down -v` y reiniciar |
| Puerto 4200/8080 ocupado | Otro servicio local usa el puerto | Cambiar `FRONTEND_PORT` o `BACKEND_PORT` en `.env` |
| `pg_isready` nunca queda healthy | El volumen quedó corrupto tras un corte brusco | `docker compose down -v` y reintentar |
| Frontend muestra pantalla en blanco | Backend aún no sano | Esperar al healthcheck o revisar `docker compose logs backend` |

---

## Estructura del repositorio

```text
frontend/
  src/app/pages/       Login, operación, operadores, celdas y vehículos
  src/app/services/    Comunicación autenticada con FastAPI
  src/app/models/      Tipos usados por las pantallas
backend/
  app/api/             Endpoints HTTP
  app/services/        Reglas de entrada, salida, ocupación y corrección
  app/models/          Entidades SQLAlchemy
  app/schemas/         Datos de entrada y respuesta de la API
  app/db/              Conexión y operaciones de PostgreSQL
  scripts/schema.sql   Tablas, tipos, relaciones y restricciones
  scripts/seed.sql     Datos iniciales y casos de demostración
  tests/               Pruebas de API, permisos, persistencia y concurrencia (T26)
docs/                  Recorrido, arquitectura y evidencia manual
docker-compose.yml     Orquesta frontend, backend y PostgreSQL
.env.example           Variables de entorno de desarrollo
```

## Documentación complementaria

- [`docs/PRD_Autos_Colombia_Iteracion_1.md`](docs/PRD_Autos_Colombia_Iteracion_1.md) · requisitos funcionales de la Iteración 1
- [`docs/PRD_Autos_Colombia_Iteracion_2.md`](docs/PRD_Autos_Colombia_Iteracion_2.md) · requisitos funcionales de la Iteración 2
- [`docs/ARQUITECTURA_TECNICA_AUTOS_COLOMBIA.md`](docs/ARQUITECTURA_TECNICA_AUTOS_COLOMBIA.md) · decisiones técnicas
- [`docs/VERIFICACION_MANUAL_ITERACION_1.md`](docs/VERIFICACION_MANUAL_ITERACION_1.md) · recorrido manual de la Iteración 1
- [`docs/VERIFICACION_T26.md`](docs/VERIFICACION_T26.md) · evidencia de concurrencia y regresión T26
- [`docs/PLAN_DESARROLLO_GITHUB.md`](docs/PLAN_DESARROLLO_GITHUB.md) · plan de desarrollo y uso de GitHub
