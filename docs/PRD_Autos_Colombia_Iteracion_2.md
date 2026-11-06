# PRD — Autos Colombia, Iteración 2

**Producto:** Sistema de información del parqueadero Autos Colombia
**Iteración:** 2 — Gestión de usuarios internos y gestión de celdas
**Estado:** Requisitos confirmados para implementación
**Fuentes:** Actividad Evaluativa 2, PRD de Iteración 1 y sesión sincrónica del 28-10
**Stack vigente:** Angular 22, TypeScript, Angular Material, FastAPI, Python 3.12, SQLAlchemy, PostgreSQL 16 y Docker Compose

## 1. Resumen ejecutivo

La segunda iteración continúa el sistema funcional de entrada y salida construido en la Iteración 1. Su objetivo es reemplazar el operario fijo por cuentas internas autenticadas, diferenciar las facultades del administrador y los operadores, registrar quién ejecuta cada operación y permitir que el administrador gestione las celdas disponibles para el parqueadero.

Esta entrega maneja únicamente dos perfiles: `ADMINISTRADOR` y `OPERADOR`. No incluye cobros, tarifas ni administración de mensualidades; la gestión de pagos pertenece a la Iteración 3.

## 2. Decisiones confirmadas por el profesor

| Tema | Decisión |
|---|---|
| Usuarios de esta iteración | Son cuentas internas de empleados, no un CRUD completo de clientes |
| Perfiles | Solo `ADMINISTRADOR` y `OPERADOR` |
| Acceso | Usuario y contraseña privados por empleado |
| Concurrencia | Como mínimo dos operadores pueden trabajar simultáneamente |
| Administrador | Gestiona operadores y celdas; también puede registrar vehículos, entradas y salidas |
| Operador | Registra vehículos nuevos, entradas y salidas; no administra cuentas ni celdas |
| Corrección de vehículos | Solo el administrador puede editar o retirar un vehículo después de guardarlo |
| Auditoría | Cada movimiento debe identificar al usuario autenticado responsable |
| Celdas | El administrador las crea, consulta, anula/reactiva o retira mediante código y tipo |
| Asignación | Puede ser automática o por selección; se conserva la asignación automática existente |
| Pagos | Fuera de alcance; corresponden a la Iteración 3 |
| GitHub | El trabajo incompleto permanece en ramas o PR draft; `main` debe seguir ejecutable |

## 3. Objetivos

### 3.1 Objetivo general

Incorporar autenticación, autorización por perfil, auditoría operativa y administración de celdas sin romper los flujos de entrada, salida, ocupación y corrección de la Iteración 1.

### 3.2 Objetivos específicos

1. Permitir el ingreso mediante credenciales individuales.
2. Restringir operaciones según el perfil autenticado.
3. Permitir que el administrador gestione cuentas de operadores.
4. Permitir que el administrador gestione celdas por código, tipo y estado.
5. Permitir a ambos perfiles registrar vehículos, entradas y salidas.
6. Reservar para el administrador la modificación o retiro de vehículos guardados.
7. Registrar quién realizó cada movimiento y cambio administrativo.
8. Mantener la integridad y concurrencia de la asignación de celdas existente.

## 4. Actores y permisos

| Acción | Administrador | Operador |
|---|:---:|:---:|
| Iniciar y cerrar sesión | Sí | Sí |
| Consultar vehículos | Sí | Sí |
| Registrar vehículo nuevo | Sí | Sí |
| Editar o retirar vehículo guardado | Sí | No |
| Registrar entrada | Sí | Sí |
| Registrar salida | Sí | Sí |
| Consultar ocupación y movimientos | Sí | Sí |
| Corregir ubicación de una permanencia | Sí | Según alcance conservado de Iteración 1 |
| Crear cuenta de operador | Sí | No |
| Anular o reactivar operador | Sí | No |
| Crear celda | Sí | No |
| Anular, reactivar o retirar celda | Sí | No |

## 5. Alcance

### 5.1 Incluido

- Inicio y cierre de sesión.
- Cuentas internas con usuario único, contraseña protegida, perfil y estado.
- Autorización en FastAPI para administrador y operador.
- Administración de cuentas de operadores.
- Registro del usuario responsable en movimientos y cambios administrativos.
- Registro de vehículos nuevos por ambos perfiles.
- Edición o retiro de vehículos únicamente por el administrador.
- Creación, consulta, anulación, reactivación y retiro controlado de celdas.
- Código único y tipo `MOTO` o `AUTOMOVIL` para cada celda.
- Exclusión de celdas inactivas de la asignación automática.
- Concurrencia de por lo menos dos operadores.
- Adaptación de las pantallas y flujos de la Iteración 1 a la sesión autenticada.

### 5.2 Fuera de alcance

- Gestión de pagos, tarifas, mensualidades o pasarela.
- Recuperación de contraseña por correo electrónico.
- Registro público de usuarios.
- Perfiles adicionales a administrador y operador.
- Autenticación social, OAuth o proveedores externos de identidad.
- Aplicación móvil.
- Integración con RUNT.
- Eliminación de historiales operativos o de auditoría.

## 6. Requisitos funcionales

### Autenticación y perfiles

- **RF-I2-01:** permitir iniciar sesión mediante usuario y contraseña.
- **RF-I2-02:** manejar exclusivamente los perfiles `ADMINISTRADOR` y `OPERADOR`.
- **RF-I2-03:** impedir el acceso y las operaciones de una cuenta anulada.
- **RF-I2-04:** soportar al menos dos sesiones de operadores concurrentes.
- **RF-I2-05:** autorizar cada endpoint en el backend según el perfil.
- **RF-I2-06:** registrar el usuario responsable de cada entrada, salida, alta de vehículo y cambio administrativo.

### Administración de operadores

- **RF-I2-07:** permitir al administrador crear cuentas de operadores con credenciales individuales.
- **RF-I2-08:** permitir al administrador consultar, anular y reactivar operadores sin borrar su historial.
- **RF-I2-09:** permitir al administrador ejecutar todas las funciones operativas.

### Vehículos y operación

- **RF-I2-10:** permitir al administrador editar o retirar vehículos guardados.
- **RF-I2-11:** permitir a administrador y operador registrar un vehículo cuando la placa no exista.
- **RF-I2-12:** permitir a ambos perfiles consultar placas y registrar entradas y salidas.
- **RF-I2-13:** impedir al operador editar o retirar un vehículo después de guardarlo.
- **RF-I2-14:** conservar las reglas de placa única, tipo permitido, asignación compatible y permanencia abierta única.

### Gestión de celdas

- **RF-I2-15:** permitir al administrador crear celdas con código único y tipo `MOTO` o `AUTOMOVIL`.
- **RF-I2-16:** permitir al administrador consultar, anular y reactivar celdas.
- **RF-I2-17:** permitir retirar físicamente únicamente una celda nueva sin movimientos asociados.
- **RF-I2-18:** conservar mediante inactivación las celdas que ya tengan historial.
- **RF-I2-19:** impedir anular o retirar una celda con una permanencia abierta.
- **RF-I2-20:** excluir las celdas inactivas de la consulta operativa y de la asignación automática.
- **RF-I2-21:** mantener motos en celdas de moto y carros/camionetas en celdas de automóvil.
- **RF-I2-22:** conservar la protección concurrente para que dos solicitudes no reciban la misma celda.

## 7. Requisitos no funcionales

- **RNF-I2-01 — Seguridad de credenciales:** las contraseñas se almacenan únicamente como hash seguro y nunca se registran en logs o respuestas.
- **RNF-I2-02 — Autorización:** Angular puede ocultar acciones, pero FastAPI es la autoridad que concede o rechaza permisos.
- **RNF-I2-03 — Trazabilidad:** las operaciones conservan usuario, fecha, acción y entidad afectada.
- **RNF-I2-04 — Concurrencia:** dos operadores deben trabajar simultáneamente sin compartir celdas ni sobrescribir movimientos.
- **RNF-I2-05 — Integridad histórica:** anular una cuenta, vehículo o celda no elimina movimientos anteriores.
- **RNF-I2-06 — Sesión:** una sesión inválida, vencida o perteneciente a una cuenta anulada se rechaza con `401`.
- **RNF-I2-07 — Permisos:** una cuenta autenticada sin facultad recibe `403` y no modifica el estado.
- **RNF-I2-08 — Usabilidad:** la interfaz identifica el perfil activo y explica claramente los rechazos.
- **RNF-I2-09 — Reproducibilidad:** el sistema continúa ejecutándose mediante Docker Compose desde un clon limpio.
- **RNF-I2-10 — Regresión:** los flujos de entrada, salida, ocupación, reportes y corrección de la Iteración 1 deben seguir funcionando.

## 8. Reglas de negocio

| ID | Regla |
|---|---|
| RN-I2-01 | Cada cuenta usa un nombre de usuario único. |
| RN-I2-02 | Una cuenta anulada no puede autenticarse ni operar. |
| RN-I2-03 | El administrador hereda todas las facultades del operador. |
| RN-I2-04 | El operador no administra cuentas ni celdas. |
| RN-I2-05 | Ambos perfiles pueden registrar un vehículo nuevo. |
| RN-I2-06 | Solo el administrador modifica o retira un vehículo guardado. |
| RN-I2-07 | Cada operación se atribuye a la cuenta autenticada, no a un ID suministrado libremente por el frontend. |
| RN-I2-08 | Cada celda tiene código único y un tipo compatible con los vehículos admitidos. |
| RN-I2-09 | Solo una celda activa y desocupada puede asignarse. |
| RN-I2-10 | Una celda ocupada no puede anularse ni retirarse. |
| RN-I2-11 | La inactivación conserva las relaciones históricas. |
| RN-I2-12 | La gestión de pagos no condiciona la implementación de esta iteración. |

## 9. Historias de usuario

### HU-I2-01. Iniciar sesión

**Como** empleado, **quiero** ingresar con mis credenciales, **para** realizar únicamente las acciones permitidas para mi perfil.

- Credenciales válidas de una cuenta activa permiten ingresar.
- Una contraseña incorrecta o una cuenta anulada no permiten ingresar.
- La interfaz muestra el nombre y perfil de la sesión activa.

### HU-I2-02. Administrar operadores

**Como** administrador, **quiero** crear y anular operadores, **para** controlar quién puede utilizar el sistema.

- Se impiden usuarios duplicados.
- Una cuenta anulada pierde acceso inmediatamente.
- Su historial permanece consultable.

### HU-I2-03. Cubrir un turno operativo

**Como** administrador, **quiero** registrar entradas y salidas con mi propia cuenta, **para** cubrir la ausencia de un operador sin compartir credenciales.

### HU-I2-04. Registrar un vehículo nuevo

**Como** operador, **quiero** registrar una placa inexistente con sus características, **para** continuar el flujo autorizado del parqueadero.

- Administrador y operador pueden crear el registro.
- Solo el administrador puede corregirlo o retirarlo posteriormente.

### HU-I2-05. Auditar movimientos

**Como** administrador, **quiero** saber qué usuario realizó cada operación, **para** identificar responsabilidades y errores.

### HU-I2-06. Administrar celdas

**Como** administrador, **quiero** crear, anular y reactivar celdas, **para** representar la capacidad operativa real.

- Una celda inactiva no se asigna.
- Una celda ocupada no se puede anular.
- El código no se duplica.

### HU-I2-07. Trabajar simultáneamente

**Como** operador, **quiero** registrar movimientos al mismo tiempo que otro operador, **para** atender los dos accesos sin conflictos.

## 10. Modelo conceptual ampliado

| Entidad | Campos principales | Propósito |
|---|---|---|
| `Operator` | `id`, `name` | Empleado que realiza operaciones |
| `UserAccount` | `id`, `operator_id`, `username`, `password_hash`, `role`, `active`, timestamps | Identidad autenticada y permisos |
| `ParkingSpot` | `id`, `code`, `category`, `active`, timestamps | Celda administrable y asignable |
| `Vehicle` | Campos de Iteración 1 más estado si se requiere retiro lógico | Vehículo registrado |
| `ParkingStay` | Datos de Iteración 1 y responsables autenticados | Entrada y salida auditables |
| `CellCorrection` | Datos de corrección y usuario responsable | Auditoría de ubicación |
| `VehicleAudit` | `vehicle_id`, `account_id`, `action`, estados anterior/nuevo, `occurred_at` | Auditoría implementada para altas, modificaciones y retiros de vehículos |

## 11. Contrato REST previsto

| Método | Ruta | Perfil | Propósito |
|---|---|---|---|
| `POST` | `/api/auth/login` | Público | Validar credenciales e iniciar sesión |
| `POST` | `/api/auth/logout` | Autenticado | Finalizar sesión |
| `GET` | `/api/auth/me` | Autenticado | Consultar usuario y perfil actual |
| `GET` | `/api/operadores` | Administrador | Listar cuentas operativas |
| `POST` | `/api/operadores` | Administrador | Crear operador y cuenta |
| `PATCH` | `/api/operadores/{id}/estado` | Administrador | Anular o reactivar acceso |
| `POST` | `/api/vehiculos` | Ambos | Registrar vehículo nuevo |
| `PATCH` | `/api/vehiculos/{id}` | Administrador | Corregir datos del vehículo |
| `DELETE` | `/api/vehiculos/{id}` | Administrador | Retirar o inactivar vehículo |
| `GET` | `/api/celdas` | Ambos | Consultar celdas según el contexto permitido |
| `POST` | `/api/celdas` | Administrador | Crear celda |
| `PATCH` | `/api/celdas/{id}` | Administrador | Cambiar datos o estado permitido |
| `DELETE` | `/api/celdas/{id}` | Administrador | Retirar celda sin historial |

Las rutas de entrada, salida, ocupación, movimientos, reportes y corrección de Iteración 1 permanecen, pero requieren sesión autenticada y obtienen el responsable desde ella. La consulta histórica se expone mediante `GET /api/movimientos/historial`, que devuelve las permanencias cerradas junto con sus responsables, comprobante y correcciones persistidas.

## 12. Respuestas de seguridad

| Estado | Uso |
|---|---|
| `401 Unauthorized` | No existe una sesión válida, la sesión venció o la cuenta está anulada |
| `403 Forbidden` | La cuenta está autenticada, pero su perfil no permite la acción |
| `409 Conflict` | Usuario, placa o código duplicado; celda ocupada; conflicto de estado |
| `422 Unprocessable Entity` | Datos estructuralmente inválidos |

Los rechazos no deben producir cambios parciales.

## 13. Datos iniciales

La semilla debe incluir:

- Una cuenta administradora activa.
- Por lo menos dos operadores activos con cuentas independientes.
- Contraseñas de demostración configurables y almacenadas como hash.
- Las 80 celdas existentes activas, salvo casos explícitos de demostración.
- Los datos de prueba de vehículos, mensualidades y movimientos de Iteración 1.

Las credenciales de demostración se documentan para el entorno académico, pero no se reutilizan como secretos de producción.

## 14. Criterios globales de aceptación

La Iteración 2 se considera funcional cuando:

- Administrador y operador pueden iniciar sesión con cuentas independientes.
- Una cuenta anulada no puede acceder.
- Un operador recibe `403` al administrar usuarios o celdas.
- El administrador puede crear y anular operadores.
- Ambos perfiles pueden registrar vehículos, entradas y salidas.
- Solo el administrador puede corregir o retirar vehículos guardados.
- El administrador puede crear e inactivar celdas.
- Una celda inactiva u ocupada no se asigna indebidamente.
- Cada movimiento identifica al usuario responsable.
- Dos operadores pueden trabajar simultáneamente sin duplicar celdas.
- Los flujos de Iteración 1 continúan funcionando.
- El proyecto inicia desde un clon limpio mediante Docker Compose.

## 15. Entregables académicos asociados

1. Requisitos funcionales y no funcionales para usuarios y celdas.
2. Casos de uso de administrador, operador y gestión de celdas en StarUML.
3. Historias de usuario de la Iteración 2.
4. Mockups de login, operadores, vehículos y celdas.
5. Diagramas de secuencia de las iteraciones 1 y 2.
6. Diagrama de componentes actualizado para ambas iteraciones.
7. Plan de pruebas resumido.
8. Repositorio de GitHub actualizado.
9. Video en YouTube mostrando el funcionamiento.
10. PDF con portada, introducción, entregables y conclusiones, usando la nomenclatura `Apellido_Nombre_EA2`.

## 16. Trazabilidad

| Historia | Requisitos |
|---|---|
| HU-I2-01 | RF-I2-01 a RF-I2-05 |
| HU-I2-02 | RF-I2-07, RF-I2-08 |
| HU-I2-03 | RF-I2-09, RF-I2-12 |
| HU-I2-04 | RF-I2-10 a RF-I2-14 |
| HU-I2-05 | RF-I2-06 |
| HU-I2-06 | RF-I2-15 a RF-I2-21 |
| HU-I2-07 | RF-I2-04, RF-I2-22 |

## 17. Restricciones para la implementación

1. No implementar pagos ni ampliar el CRUD de clientes.
2. No confiar permisos o identidad enviados libremente por Angular.
3. No guardar contraseñas en texto plano.
4. No eliminar historiales para simular una anulación.
5. No retirar las restricciones concurrentes existentes.
6. No fusionar trabajo incompleto en `main`.
7. Actualizar arquitectura, pruebas y documentación cuando cambie el contrato.
