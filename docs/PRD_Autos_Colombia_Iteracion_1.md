# PRD — Autos Colombia, Iteración 1

**Producto:** Sistema de información del parqueadero Autos Colombia
**Iteración:** 1 — Gestión de entrada y salida de vehículos
**Estado:** Base de implementación
**Fuentes:** guía de la Evidencia de Aprendizaje 1 y transcripción de la entrevista de requisitos con el docente en el rol de cliente
**Stack acordado:** Angular 22 + TypeScript, FastAPI + Python, SQLAlchemy, PostgreSQL 16 y Docker Compose

## 1. Resumen ejecutivo

Autos Colombia es un parqueadero cubierto que presta servicio exclusivamente mediante mensualidades. La primera iteración debe permitir que los operarios registren entradas y salidas, validen que cada vehículo esté autorizado, asignen una celda compatible disponible, entreguen un comprobante y liberen la celda al finalizar la permanencia.

El sistema debe controlar 80 celdas: 10 para motos y 70 para carros o camionetas. Dos operarios pueden registrar ingresos simultáneamente durante el día, por lo que la aplicación debe impedir el sobrecupo, una segunda entrada del mismo vehículo y la asignación de una misma celda a dos vehículos.

Esta iteración no implementa la administración completa de usuarios ni la gestión de pagos. Sin embargo, necesita consultar datos previamente registrados del vehículo, su cliente y el estado de su mensualidad para decidir si el ingreso está autorizado.

## 2. Objetivos

### 2.1 Objetivo general

Diseñar e implementar una aplicación web que gestione de forma segura y consistente la entrada y salida de vehículos del parqueadero Autos Colombia.

### 2.2 Objetivos específicos

1. Validar por placa que el vehículo esté registrado y tenga una mensualidad vigente.
2. Mostrar marca, modelo, color y tipo para facilitar la verificación visual del vehículo.
3. Asignar automáticamente una celda libre compatible con el tipo de vehículo.
4. Evitar el sobrecupo, las entradas duplicadas y las asignaciones dobles de celdas.
5. Emitir un comprobante de ingreso que permita autorizar la salida.
6. Registrar la salida, cerrar la permanencia y liberar la celda.
7. Consultar la ocupación y disponibilidad actual del parqueadero.
8. Producir la documentación solicitada en la actividad académica y mantener trazabilidad entre requisitos, historias, modelos, interfaz y código.

## 3. Contexto del negocio

| Tema | Regla confirmada por el cliente |
|---|---|
| Modalidad | El parqueadero trabaja únicamente por mensualidades; no ofrece estacionamiento por horas o días. |
| Operación | Está disponible 24 horas al día, 7 días a la semana. |
| Capacidad | Existen 80 celdas: 10 para motos y 70 para carros o camionetas. |
| Vehículos admitidos | Motos, carros y camionetas. No se admiten camiones. |
| Asignación | Las celdas no son fijas por cliente. En cada ingreso se asigna una celda compatible disponible. |
| Titularidad | Cada vehículo está asociado a una persona. Un cliente puede tener varios vehículos, pero paga una mensualidad por cada uno. |
| Identificación | La placa identifica el registro; marca, modelo y color permiten comprobar visualmente que corresponda al vehículo autorizado. |
| Accesos | Hay dos accesos y dos operarios diurnos que pueden registrar vehículos al mismo tiempo; en la noche opera una persona. |
| Salida | Se autoriza con el recibo, tarjeta o comprobante entregado al ingresar, no por reconocimiento visual del operario. |
| Infraestructura | Todo el parqueadero es cubierto. Las 70 celdas de automóvil sirven tanto para carros como para camionetas. |

## 4. Alcance

### 4.1 Incluido en la Iteración 1

- Consulta de un vehículo por placa.
- Verificación de registro y mensualidad vigente.
- Presentación de marca, modelo, color y tipo de vehículo.
- Registro de entrada.
- Asignación automática de una celda compatible disponible.
- Prevención de sobrecupo, duplicidad de entradas y doble asignación de celdas.
- Generación de un comprobante de ingreso.
- Registro de salida mediante comprobante.
- Cierre de la permanencia y liberación de la celda.
- Consulta de celdas ocupadas y disponibles por tipo.
- Consulta de vehículos actualmente dentro del parqueadero.
- Reporte de vehículos registrados y estado general de ocupación.
- Corrección operativa cuando un vehículo ocupa una celda diferente a la asignada.

### 4.2 Fuera del alcance de la Iteración 1

- Registro, edición y eliminación completa de clientes.
- Gestión completa de usuarios, autenticación, permisos y roles.
- Cobro de mensualidades.
- Pasarela de pagos.
- Definición e implementación de tarifas.
- Servicios adicionales, como lavado.
- Responsabilidad o inventario de objetos dentro de los vehículos.
- Integración con RUNT u otra API externa.
- Gestión completa de novedades o daños.
- Reconocimiento automático de placas.
- Aplicación móvil.

### 4.3 Contexto para futuras iteraciones

- La gestión de usuarios deberá contemplar nombre, apellido, documento, teléfonos, correo, vehículos asociados y actualización del vehículo.
- La gestión de pagos manejará mensualidades por vehículo. Durante la clase se mencionaron como referencia COP 250.000 para carro y COP 100.000 para moto, pero esas tarifas no forman parte de esta iteración.
- La vigencia comienza en la fecha de pago y no existe periodo de gracia: al vencer, el cliente paga o no ingresa. El cálculo definitivo pertenece a la iteración de pagos.
- La gestión de novedades permitirá registrar incidentes o daños relacionados con un vehículo.

## 5. Usuarios del producto

### 5.1 Operario

Registra entradas y salidas, consulta vehículos, verifica sus características, entrega o valida comprobantes, consulta celdas y corrige asignaciones operativas.

### 5.2 Responsable del parqueadero

Consulta reportes de vehículos registrados, vehículos presentes, ocupación y disponibilidad. La administración completa de usuarios y roles se difiere a otra iteración.

### 5.3 Cliente del parqueadero

Es la persona asociada a uno o varios vehículos. No utiliza directamente la aplicación en esta iteración; recibe el comprobante y lo presenta para retirar el vehículo.

## 6. Supuestos operativos

1. Los clientes, vehículos y estados de mensualidad necesarios para las pruebas estarán precargados.
2. Cada vehículo tiene una placa única y un tipo entre `MOTO`, `CARRO` y `CAMIONETA`.
3. Las celdas estarán precargadas: 10 de tipo moto y 70 de tipo automóvil.
4. El backend es la única autoridad para confirmar una asignación de celda.
5. El frontend nunca considera definitiva una celda hasta recibir la confirmación de FastAPI.
6. El comprobante tendrá un identificador único. Su formato físico o digital puede definirse durante el diseño de interfaz.
7. La aplicación registra fecha y hora de cada entrada y salida para mantener trazabilidad.
8. El estado de vigencia de la mensualidad se consulta, pero su pago y administración no se implementan en esta iteración.

## 7. Reglas de negocio

| ID | Regla |
|---|---|
| RN-01 | Solo puede ingresar un vehículo registrado y asociado a un cliente. |
| RN-02 | El vehículo debe tener una mensualidad vigente al momento del ingreso. |
| RN-03 | La mensualidad corresponde al vehículo, no a una celda. |
| RN-04 | Un cliente puede tener varios vehículos, cada uno con su propia mensualidad. |
| RN-05 | Un vehículo no puede tener más de una permanencia abierta. |
| RN-06 | Una celda no puede estar asociada a más de una permanencia abierta. |
| RN-07 | Una moto solo puede ocupar una de las 10 celdas para motos. |
| RN-08 | Un carro o camioneta solo puede ocupar una de las 70 celdas para automóviles. |
| RN-09 | Los camiones no están permitidos. |
| RN-10 | La capacidad total nunca puede superar 80 vehículos. |
| RN-11 | La celda se asigna en cada ingreso; no queda reservada permanentemente para un cliente. |
| RN-12 | La celda queda ocupada al confirmar la entrada y se libera al confirmar la salida. |
| RN-13 | La salida requiere un comprobante válido asociado a una permanencia abierta. |
| RN-14 | Si un vehículo ocupa una celda distinta, el operario debe corregir las asignaciones afectadas sin crear duplicidades. |
| RN-15 | Marca, modelo y color deben mostrarse al consultar la placa para apoyar la verificación de seguridad. |

## 8. Flujo principal del producto

### 8.1 Entrada

1. El operario ingresa la placa.
2. El sistema localiza el vehículo.
3. El sistema muestra placa, tipo, marca, modelo y color.
4. El sistema valida que el vehículo esté registrado, tenga mensualidad vigente y no tenga otra entrada abierta.
5. El sistema busca una celda compatible disponible.
6. PostgreSQL protege la asignación dentro de una transacción para que otra operación concurrente no tome la misma celda.
7. El sistema registra el movimiento de entrada y confirma la celda.
8. El sistema genera un comprobante único.
9. El operario informa la celda al conductor y entrega el comprobante.

### 8.2 Salida

1. El cliente presenta el comprobante.
2. El operario ingresa o consulta su identificador.
3. El sistema localiza la permanencia abierta y presenta el vehículo y la celda.
4. El operario confirma la salida.
5. El sistema registra fecha y hora de salida.
6. El sistema cierra la permanencia y libera la celda en una misma operación.
7. El sistema informa que la salida fue registrada correctamente.

### 8.3 Corrección de ubicación

1. El operario detecta que un vehículo no está en la celda asignada.
2. Consulta el movimiento abierto del vehículo y el estado de la celda real.
3. Selecciona una celda compatible y disponible o corrige las asignaciones involucradas.
4. El sistema valida que la corrección no duplique vehículos ni celdas.
5. El sistema guarda el nuevo estado y conserva trazabilidad de la corrección.

## 9. Requisitos funcionales

### RF-01. Consultar vehículo por placa

- **Descripción:** El sistema debe permitir al operario buscar un vehículo mediante su placa.
- **Entradas:** Placa.
- **Salidas:** Datos del vehículo o mensaje de vehículo no registrado.
- **Resultado esperado:** Se identifica el registro que será validado para el ingreso.
- **Criterios de aceptación:**
  - La placa se normaliza para evitar diferencias por mayúsculas o espacios.
  - Si existe, se muestran placa, tipo, marca, modelo, color y estado de mensualidad.
  - Si no existe, se informa que el vehículo no está registrado y no se permite continuar.

### RF-02. Validar autorización de ingreso

- **Descripción:** El sistema debe verificar que el vehículo esté registrado, tenga una mensualidad vigente y no posea otra permanencia abierta.
- **Entradas:** Vehículo identificado y fecha/hora actual.
- **Salidas:** Autorización o motivo del rechazo.
- **Resultado esperado:** Solo avanzan vehículos habilitados.
- **Criterios de aceptación:**
  - Un vehículo con mensualidad vencida es rechazado.
  - Un vehículo con entrada abierta es rechazado.
  - Un camión es rechazado.
  - Cada rechazo presenta una causa comprensible y no modifica ocupaciones ni contadores.

### RF-03. Mostrar características para verificación

- **Descripción:** Antes de confirmar el ingreso, el sistema debe mostrar marca, modelo, color y tipo del vehículo asociado a la placa.
- **Entradas:** Placa válida.
- **Salidas:** Ficha resumida del vehículo.
- **Resultado esperado:** El operario puede comparar el vehículo presente con el registrado.
- **Criterios de aceptación:**
  - Los datos se muestran antes de la confirmación.
  - Si las características no coinciden, el operario puede cancelar sin alterar el estado del parqueadero.

### RF-04. Registrar entrada

- **Descripción:** El sistema debe crear una permanencia abierta cuando el operario confirme el ingreso autorizado.
- **Entradas:** Vehículo, operario y fecha/hora.
- **Salidas:** Movimiento de entrada confirmado.
- **Resultado esperado:** El vehículo queda registrado dentro del parqueadero.
- **Criterios de aceptación:**
  - El movimiento registra vehículo, celda, operario y fecha/hora de entrada.
  - La operación solo finaliza si también se confirma una celda.
  - Ante un error, no queda un movimiento incompleto ni una celda ocupada parcialmente.

### RF-05. Asignar automáticamente una celda compatible

- **Descripción:** El sistema debe seleccionar una celda disponible según el tipo de vehículo.
- **Entradas:** Tipo de vehículo y celdas disponibles.
- **Salidas:** Celda asignada o mensaje de capacidad agotada.
- **Resultado esperado:** Cada ingreso recibe una única celda compatible.
- **Criterios de aceptación:**
  - Una moto recibe una de las 10 celdas para motos.
  - Un carro o camioneta recibe una de las 70 celdas para automóviles.
  - Una celda ocupada nunca se ofrece.
  - Si no existe una celda compatible libre, el ingreso se rechaza sin cambios de estado.

### RF-06. Impedir sobrecupo y duplicidades

- **Descripción:** El sistema debe proteger las restricciones de capacidad y unicidad incluso cuando dos operarios registran al mismo tiempo.
- **Entradas:** Solicitudes concurrentes de ingreso.
- **Salidas:** Asignaciones diferentes o rechazo controlado.
- **Resultado esperado:** Nunca hay dos movimientos abiertos para el mismo vehículo ni para la misma celda.
- **Criterios de aceptación:**
  - Dos ingresos simultáneos no reciben la misma celda.
  - La ocupación nunca supera 10 motos, 70 automóviles ni 80 vehículos totales.
  - Si solo queda una celda y llegan dos solicitudes válidas, una se confirma y la otra se rechaza.

### RF-07. Generar comprobante de ingreso

- **Descripción:** El sistema debe generar un identificador único para cada entrada confirmada.
- **Entradas:** Movimiento de entrada confirmado.
- **Salidas:** Comprobante asociado al vehículo, celda y entrada.
- **Resultado esperado:** El cliente recibe el soporte necesario para solicitar la salida.
- **Criterios de aceptación:**
  - Cada comprobante es único.
  - El comprobante referencia una permanencia abierta.
  - Un intento fallido de ingreso no genera comprobante.

### RF-08. Registrar salida mediante comprobante

- **Descripción:** El sistema debe localizar y cerrar una permanencia abierta utilizando el comprobante presentado por el cliente.
- **Entradas:** Identificador del comprobante y confirmación del operario.
- **Salidas:** Salida confirmada o mensaje de rechazo.
- **Resultado esperado:** Solo se retira un vehículo respaldado por un comprobante válido.
- **Criterios de aceptación:**
  - Un comprobante válido muestra vehículo y celda antes de confirmar.
  - Un comprobante inexistente, ya utilizado o sin permanencia abierta es rechazado.
  - El rechazo no libera celdas ni modifica movimientos.

### RF-09. Cerrar permanencia y liberar celda

- **Descripción:** Al confirmar la salida, el sistema debe registrar la fecha/hora y liberar la celda en una sola operación.
- **Entradas:** Permanencia abierta confirmada para salida.
- **Salidas:** Movimiento cerrado y celda disponible.
- **Resultado esperado:** La celda queda disponible inmediatamente para otro ingreso.
- **Criterios de aceptación:**
  - El movimiento conserva entrada y salida.
  - La celda deja de aparecer como ocupada.
  - No puede registrarse dos veces la salida del mismo movimiento.
  - Si la operación falla, ni el movimiento ni la celda quedan en un estado parcial.

### RF-10. Consultar ocupación y disponibilidad

- **Descripción:** El sistema debe mostrar el estado actual de las celdas.
- **Entradas:** Consulta del operario o responsable.
- **Salidas:** Totales y listado de celdas disponibles u ocupadas.
- **Resultado esperado:** El personal conoce la capacidad en tiempo real.
- **Criterios de aceptación:**
  - Se muestran disponibles y ocupadas para motos.
  - Se muestran disponibles y ocupadas para carros/camionetas.
  - Los totales coinciden con las permanencias abiertas.

### RF-11. Consultar reportes operativos

- **Descripción:** El sistema debe presentar un reporte de vehículos registrados, vehículos presentes y disponibilidad de celdas.
- **Entradas:** Solicitud de reporte.
- **Salidas:** Información consolidada y actual.
- **Resultado esperado:** El responsable puede controlar la operación del parqueadero.
- **Criterios de aceptación:**
  - Distingue vehículos registrados de vehículos actualmente presentes.
  - Incluye capacidad total, ocupación y disponibilidad por tipo.
  - La información se obtiene de los datos actuales y no de contadores manuales independientes.

### RF-12. Corregir una asignación de celda

- **Descripción:** El operario debe poder corregir la celda de un movimiento abierto cuando el vehículo se encuentre en una ubicación distinta.
- **Entradas:** Movimiento abierto, celda actual observada y confirmación del operario.
- **Salidas:** Asignación corregida o explicación del rechazo.
- **Resultado esperado:** El mapa lógico vuelve a coincidir con la ocupación real.
- **Criterios de aceptación:**
  - La nueva celda debe ser compatible con el vehículo.
  - No se puede ocupar una celda que ya pertenezca a otro movimiento abierto sin resolver previamente la inconsistencia.
  - La corrección no crea movimientos adicionales.
  - Se registra quién hizo la corrección y cuándo.

## 10. Requisitos no funcionales

### RNF-01. Integridad y concurrencia

La selección y ocupación de una celda debe ejecutarse mediante una transacción en el backend y la base de datos. PostgreSQL debe reforzar la unicidad de una permanencia abierta por vehículo y por celda.

### RNF-02. Disponibilidad operativa

La aplicación debe poder utilizarse durante la operación 24/7 del parqueadero. No se define un porcentaje contractual de disponibilidad para esta actividad, pero reiniciar un contenedor no debe eliminar los datos persistidos.

### RNF-03. Consistencia transaccional

Registrar una entrada, asignar una celda y generar su comprobante debe comportarse como una sola operación lógica. Cerrar una permanencia y liberar la celda también debe ser atómico.

### RNF-04. Usabilidad

Las pantallas deben utilizar lenguaje claro, mostrar los datos críticos antes de confirmar y presentar mensajes concretos ante vehículo no registrado, mensualidad vencida, entrada duplicada, falta de cupo o comprobante inválido.

### RNF-05. Seguridad operativa

La salida debe requerir un comprobante válido. Los datos del vehículo deben mostrarse para apoyar la verificación visual. Las credenciales de base de datos no deben quedar escritas directamente en el código fuente.

### RNF-06. Trazabilidad

Cada movimiento debe conservar vehículo, celda, fecha/hora de entrada, fecha/hora de salida y operario responsable. Las correcciones de celda deben registrar autor y momento.

### RNF-07. Mantenibilidad

Frontend, backend y base de datos deben estar separados. El código debe usar nombres claros y módulos sencillos por responsabilidad, evitando microservicios y patrones que no aporten al alcance.

### RNF-08. Reproducibilidad

El entorno debe ejecutarse mediante Docker Compose con servicios para Angular, FastAPI y PostgreSQL. Una persona con Docker y Git debe poder iniciar el proyecto siguiendo el README, sin instalar Angular ni PostgreSQL localmente.

### RNF-09. Persistencia

PostgreSQL debe usar un volumen persistente. Recrear los contenedores de aplicación no debe borrar vehículos, celdas ni movimientos.

### RNF-10. Compatibilidad

El frontend se implementará con Angular 22 y TypeScript. El backend se implementará con Python 3.12, FastAPI y SQLAlchemy. La base de datos será PostgreSQL 16.

## 11. Historias de usuario

### HU-01. Consultar y validar un vehículo

**Como** operario, **quiero** buscar un vehículo por su placa y ver sus características y vigencia, **para** decidir si está autorizado para ingresar.

**Criterios de aceptación:**

- Dado un vehículo registrado y vigente, cuando ingreso su placa, entonces veo tipo, marca, modelo y color y puedo continuar.
- Dada una placa inexistente, cuando intento consultarla, entonces se informa que no está registrada y no se modifica el parqueadero.
- Dado un vehículo con mensualidad vencida, cuando intento autorizarlo, entonces se rechaza el ingreso con una causa clara.

### HU-02. Registrar una entrada con celda automática

**Como** operario, **quiero** confirmar la entrada de un vehículo autorizado y recibir una celda compatible, **para** indicarle al conductor dónde estacionar.

**Criterios de aceptación:**

- Dado un vehículo autorizado y una celda compatible libre, cuando confirmo la entrada, entonces se crea una permanencia abierta y se asigna esa celda.
- Dada una moto, cuando se registra su entrada, entonces solo puede recibir una celda de moto.
- Dado un carro o camioneta, cuando se registra su entrada, entonces solo puede recibir una celda de automóvil.

### HU-03. Rechazar una entrada inválida

**Como** operario, **quiero** conocer por qué una entrada no puede realizarse, **para** informar al cliente sin alterar la ocupación.

**Criterios de aceptación:**

- Se rechazan placa no registrada, mensualidad vencida, camión, vehículo ya presente y falta de cupo compatible.
- El rechazo muestra una causa comprensible.
- El rechazo no crea movimientos, comprobantes ni ocupaciones.

### HU-04. Recibir un comprobante de ingreso

**Como** operario, **quiero** generar un comprobante único al registrar la entrada, **para** entregarlo al cliente y utilizarlo en la salida.

**Criterios de aceptación:**

- El comprobante se genera solo después de confirmar la entrada.
- Su identificador es único.
- Está vinculado con el vehículo, la celda y la permanencia abierta.

### HU-05. Registrar la salida y liberar la celda

**Como** operario, **quiero** localizar la permanencia mediante el comprobante y confirmar la salida, **para** cerrar el movimiento y devolver la celda a disponibilidad.

**Criterios de aceptación:**

- Un comprobante válido muestra el vehículo y la celda.
- Al confirmar, se registra la salida y la celda queda disponible.
- Un comprobante inválido o ya utilizado no cambia el estado.

### HU-06. Consultar disponibilidad

**Como** operario, **quiero** consultar celdas disponibles y ocupadas por tipo, **para** conocer la capacidad actual del parqueadero.

**Criterios de aceptación:**

- La vista separa motos de carros/camionetas.
- Los totales coinciden con las permanencias abiertas.
- Una entrada o salida confirmada actualiza la información.

### HU-07. Registrar ingresos simultáneos sin conflictos

**Como** responsable del parqueadero, **quiero** que dos operarios puedan registrar entradas simultáneamente, **para** atender ambos accesos sin duplicar celdas.

**Criterios de aceptación:**

- Dos solicitudes simultáneas nunca reciben la misma celda.
- Si queda una sola celda, solo una solicitud se confirma.
- El resultado conserva los límites de capacidad.

### HU-08. Consultar vehículos y ocupación

**Como** responsable del parqueadero, **quiero** consultar vehículos registrados, vehículos presentes y celdas disponibles, **para** controlar la operación actual.

**Criterios de aceptación:**

- El reporte diferencia registro total y presencia actual.
- Presenta capacidad, ocupación y disponibilidad por tipo.
- Los datos reflejan el estado de PostgreSQL.

### HU-09. Corregir una celda equivocada

**Como** operario, **quiero** corregir la celda asociada a un vehículo mal ubicado, **para** que el sistema represente la ocupación real.

**Criterios de aceptación:**

- La nueva celda debe ser compatible y estar disponible.
- La corrección no duplica vehículos ni celdas.
- Se conserva quién corrigió la asignación y cuándo.

### HU-10. Verificar visualmente el vehículo

**Como** operario, **quiero** ver marca, modelo y color asociados a la placa, **para** detectar si el vehículo presente no coincide con el autorizado.

**Criterios de aceptación:**

- Los datos aparecen antes de confirmar el ingreso.
- El operario puede cancelar si observa una inconsistencia.
- Cancelar no cambia ninguna celda ni movimiento.

## 12. Modelo conceptual mínimo

| Entidad | Propósito | Datos mínimos |
|---|---|---|
| Cliente | Persona asociada a uno o varios vehículos. | Identificador y nombre de referencia. La gestión completa se difiere. |
| Vehículo | Unidad que paga mensualidad e ingresa al parqueadero. | Placa, tipo, marca, modelo, color y cliente. |
| Mensualidad | Fuente del estado de autorización. | Vehículo, inicio, vencimiento y estado. El pago se difiere. |
| Celda | Espacio físico disponible u ocupado. | Código, tipo y estado derivado de la permanencia abierta. |
| Movimiento | Permanencia de un vehículo. | Vehículo, celda, entrada, salida y operario. |
| Comprobante | Soporte para autorizar la salida. | Identificador único, movimiento y estado de uso. |
| Operario | Persona que registra operaciones. | Identificador y nombre de referencia. Roles completos se difieren. |

### Relaciones principales

- Un cliente tiene uno o varios vehículos.
- Un vehículo puede tener mensualidades a lo largo del tiempo.
- Un vehículo puede tener muchos movimientos históricos, pero solo uno abierto.
- Una celda puede tener muchos movimientos históricos, pero solo uno abierto.
- Un movimiento corresponde a un vehículo y una celda.
- Un movimiento genera un comprobante.
- Un operario registra movimientos y correcciones.

## 13. Arquitectura propuesta

### 13.1 Componentes

```text
Navegador
   │
   ▼
Angular 22 + TypeScript
   │ REST/JSON
   ▼
FastAPI + SQLAlchemy
   │ SQL/transacciones
   ▼
PostgreSQL 16
```

### 13.2 Docker Compose

El entorno tendrá tres servicios:

- `frontend`: aplicación Angular disponible para el navegador.
- `backend`: API FastAPI responsable de reglas y transacciones.
- `db`: PostgreSQL con volumen persistente.

El backend se conecta a `db:5432` dentro de la red de Docker. El puerto de PostgreSQL no necesita publicarse al host. Si se requiere acceso local, deberá usarse un puerto alternativo, por ejemplo `5433`, porque el equipo actual ya tiene PostgreSQL local usando `5432`.

### 13.3 Estructura mínima

```text
autos-colombia/
├── frontend/
├── backend/
│   └── app/
│       ├── main.py
│       ├── database.py
│       ├── models.py
│       ├── schemas.py
│       ├── services.py
│       └── routes.py
├── docs/
├── docker-compose.yml
├── .env.example
├── .gitignore
└── README.md
```

## 14. Contrato inicial de API

| Método | Ruta | Propósito |
|---|---|---|
| `GET` | `/api/vehiculos/{placa}` | Consultar vehículo y estado necesario para el ingreso. |
| `POST` | `/api/entradas` | Validar, asignar celda, registrar entrada y generar comprobante. |
| `POST` | `/api/salidas` | Validar comprobante, cerrar movimiento y liberar celda. |
| `GET` | `/api/celdas` | Consultar celdas y estados. |
| `GET` | `/api/movimientos/activos` | Consultar vehículos presentes. |
| `GET` | `/api/reportes/ocupacion` | Consultar resumen de capacidad, ocupación y disponibilidad. |
| `PATCH` | `/api/movimientos/{id}/celda` | Corregir la celda de una permanencia abierta. |

Los nombres finales pueden ajustarse durante la implementación, pero no deben alterar las reglas del producto.

## 15. Restricciones de implementación para el agente

1. Implementar solo el alcance de la Iteración 1.
2. No agregar cobros, pasarela, servicios adicionales ni autenticación compleja sin una nueva decisión.
3. No asignar celdas exclusivamente en Angular.
4. Ejecutar la validación y asignación dentro de una transacción en FastAPI/PostgreSQL.
5. Reforzar en PostgreSQL que no exista más de un movimiento abierto por vehículo o por celda.
6. Derivar ocupación y disponibilidad de las permanencias abiertas; evitar contadores manuales que puedan desincronizarse.
7. Mantener frontend, backend y base de datos como servicios separados de Docker Compose.
8. Usar mensajes claros y conservar el estado cuando una operación sea rechazada.
9. Mantener el código sencillo y explicable para una evaluación académica.
10. Documentar cómo levantar, detener y probar el sistema.

## 16. Matriz de trazabilidad

| Historia | Requisitos relacionados |
|---|---|
| HU-01 | RF-01, RF-02, RF-03 |
| HU-02 | RF-04, RF-05, RF-06 |
| HU-03 | RF-02, RF-05, RF-06 |
| HU-04 | RF-07 |
| HU-05 | RF-08, RF-09 |
| HU-06 | RF-10 |
| HU-07 | RF-06, RNF-01, RNF-03 |
| HU-08 | RF-11 |
| HU-09 | RF-12, RNF-06 |
| HU-10 | RF-03 |

## 17. Criterios globales de aceptación

La Iteración 1 se considera funcional cuando:

- Un vehículo registrado, vigente y ausente puede ingresar y recibe una celda compatible.
- Un vehículo no registrado, vencido, duplicado, no permitido o sin cupo es rechazado sin efectos secundarios.
- Dos ingresos concurrentes no comparten celda.
- La ocupación nunca supera los límites definidos.
- Un comprobante válido permite registrar la salida.
- Una salida libera inmediatamente la celda.
- La disponibilidad coincide con los movimientos abiertos.
- Los reportes distinguen vehículos registrados y actualmente presentes.
- La solución puede iniciarse mediante Docker Compose siguiendo el README.

## 18. Entregables académicos asociados

La entrega final debe contener:

1. Requisitos funcionales y no funcionales para la gestión de entrada y salida.
2. Historias de usuario asociadas.
3. Arquitectura del sistema realizada en StarUML.
4. Mockups de las historias asociadas realizados en Figma.
5. Modelo entidad-relación, modelo relacional y modelo físico.
6. Diagramas de casos de uso realizados en StarUML.
7. Diagrama de clases realizado en StarUML.
8. Diagrama de paquetes realizado en StarUML.
9. Código fuente ejecutable y alojado en GitHub.

El documento final de la actividad debe incluir portada, introducción, desarrollo de los entregables y conclusiones. La guía solicita PDF, aunque su ejemplo de nomenclatura usa `.docx`; se recomienda confirmar el formato final con el docente. La nomenclatura indicada es `Apellido_Nombre_EA1`.

## 19. Preguntas abiertas no bloqueantes

Estas decisiones no fueron cerradas por el cliente y deben confirmarse antes de pulir la interfaz final:

1. ¿El comprobante será impreso, digital o ambos?
2. ¿Qué formato exacto tendrá su identificador?
3. ¿La salida permitirá una validación excepcional cuando el cliente pierda el comprobante?
4. ¿El reporte se visualizará únicamente en pantalla o deberá exportarse?
5. ¿Cuál será el formato permitido para placas de motos y automóviles?
6. ¿Qué datos mínimos de cliente y operario se precargarán para esta iteración?
7. ¿La corrección de una celda ocupada por error requerirá resolver dos movimientos en una sola pantalla?

Hasta recibir respuesta, la implementación debe utilizar la opción más sencilla que respete las reglas confirmadas y no ampliar el alcance.
