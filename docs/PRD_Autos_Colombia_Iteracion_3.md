# PRD — Autos Colombia, Iteración 3

**Producto:** Sistema de información del parqueadero Autos Colombia
**Iteración:** 3 — Gestión de pagos de mensualidades
**Estado:** Requisitos confirmados para implementación
**Fuentes:** Actividad Evaluativa 3, PRD de Iteración 1, PRD de Iteración 2 y sesión sincrónica con el profesor sobre gestión de pagos
**Stack vigente:** Angular 22, TypeScript, Angular Material, FastAPI, Python 3.12, SQLAlchemy, PostgreSQL 16 y Docker Compose

## 1. Resumen ejecutivo

La tercera iteración incorpora la gestión de pagos de mensualidades sobre el sistema autenticado construido en las iteraciones 1 y 2. Su objetivo es permitir que el operador registre el pago mensual de un vehículo, actualice la vigencia de la mensualidad respetando una fecha de corte estable y mantenga el estado de cada cliente consistente con los pagos realizados.

Esta entrega cierra el ciclo funcional académico: con una mensualidad vigente el vehículo puede ingresar y salir usando los flujos de la Iteración 1, mientras que el administrador y el operador autenticados en la Iteración 2 son quienes registran los pagos y consultan su historial. No se implementa pasarela externa ni retención física del vehículo.

## 2. Decisiones confirmadas por el profesor

Las reglas de esta sección provienen literalmente de la sesión sincrónica con el profesor y son la base no negociable del diseño de pagos.

| Tema | Decisión |
|---|---|
| Responsable del registro | El pago lo registra el **operador** autenticado, no el cliente ni el administrador exclusivamente. El administrador conserva sus facultades operativas de la Iteración 2. |
| Datos mínimos del pago | Fecha del pago, valor del pago, cliente, vehículo asociado y vigencia resultante de la mensualidad. |
| Medios aceptados | Efectivo, transferencia bancaria o código QR. El sistema solo registra que el pago fue recibido; no integra pasarela externa. |
| Fecha de pago vs. fecha de corte | Son dos fechas **distintas**. La fecha de pago registra cuándo se recibió el dinero. La fecha de corte (vigencia de la mensualidad) define hasta cuándo el vehículo tiene derecho a ingresar. |
| Actualización de la vigencia | Al registrar un pago, la vigencia de la mensualidad se extiende **30 días desde la fecha de corte anterior**, no desde la fecha del pago. |
| Pago anticipado | El cliente puede pagar antes de que se venza su mensualidad. Eso **no amplía ni corre la fecha de corte**: siempre se extiende respecto al corte vigente. |
| Pago en mora | Si paga después del vencimiento, la nueva vigencia **también parte desde la fecha de corte anterior**, no desde el día del pago. Ejemplo del profesor: corte el día 1, paga el día 5, la vigencia nueva va hasta el día 1 del mes siguiente. |
| Pago el día del vencimiento | Se trata igual que los demás escenarios: la vigencia se extiende 30 días desde la fecha de corte anterior. |
| Primer pago | Cuando un cliente ingresa por primera vez o reactiva el servicio después de una baja, el primer pago establece la fecha de corte a partir del día del pago. |
| Dar de baja al cliente | Cuando el cliente se retira, se marca como **inactivo en la plataforma** y se conserva en la base de datos para auditoría. No se elimina. |
| Validación al dar de baja | Antes de inactivar al cliente se debe verificar que ninguno de sus vehículos tenga una permanencia abierta dentro del parqueadero. |
| Reingreso tras baja | Un cliente reingresa como registro existente en estado inactivo y debe pagar una nueva mensualidad para reactivarse. No existe suspensión temporal del contrato. |
| Retención de vehículos | Fuera de alcance. El sistema no implementa retención física por mora, aunque la normatividad colombiana lo permita. |
| Suspensión temporal | No contemplada. Solo existen los estados activo e inactivo. |
| Notificaciones | **Voluntarias**. Si el equipo lo implementa, puede notificar por correo o WhatsApp antes del vencimiento. No es obligatorio para aprobar la entrega. |
| Pruebas del profesor | El profesor ejecuta aproximadamente 120 pruebas unitarias y 30 de integración, con énfasis en que la fecha de corte **no se corra** cuando el pago llega tarde. |

## 3. Objetivos

### 3.1 Objetivo general

Registrar los pagos mensuales de los vehículos del parqueadero, actualizar la vigencia de la mensualidad respetando la fecha de corte estable y mantener el estado del cliente consistente con la operación de entrada, salida y gestión de celdas construida en iteraciones anteriores.

### 3.2 Objetivos específicos

1. Permitir al operador registrar el pago mensual de un vehículo con fecha, valor y medio.
2. Calcular la nueva fecha de corte extendiendo 30 días desde la fecha de corte anterior, sin importar cuándo se realice el pago.
3. Mantener la fecha del pago como información independiente de la vigencia.
4. Consultar la vigencia actual, los pagos históricos y el estado de cada cliente y cada vehículo.
5. Permitir dar de baja a un cliente conservando su historial en la base de datos.
6. Impedir dar de baja a un cliente mientras alguno de sus vehículos esté dentro del parqueadero.
7. Impedir el ingreso de un vehículo cuya mensualidad esté vencida, reutilizando la validación de la Iteración 1.
8. Dejar el sistema listo para la demostración académica completa de las tres iteraciones.

## 4. Actores y permisos

| Acción | Administrador | Operador |
|---|:---:|:---:|
| Consultar cliente y vehículos asociados | Sí | Sí |
| Consultar vigencia actual de una mensualidad | Sí | Sí |
| Consultar historial de pagos | Sí | Sí |
| Registrar un pago | Sí | Sí |
| Anular un pago registrado por error | Sí | No |
| Dar de baja (inactivar) un cliente | Sí | Sí |
| Reactivar un cliente inactivo | Sí | Sí |
| Consultar clientes inactivos en reportes de auditoría | Sí | No |

El administrador conserva, por herencia de la Iteración 2, la posibilidad de ejecutar cualquier operación del operador.

## 5. Alcance

### 5.1 Incluido en la Iteración 3

- Registro de pagos mensuales con fecha, valor, medio y responsable autenticado.
- Cálculo automático de la nueva fecha de corte extendiendo 30 días desde la fecha de corte vigente.
- Primer pago de un cliente nuevo o reactivado, cuya fecha de corte parte del día del pago.
- Consulta de la mensualidad vigente de un vehículo, con su fecha de corte e indicador de vencimiento.
- Consulta del historial de pagos por vehículo y por cliente.
- Estado del cliente: activo o inactivo, con fecha e usuario responsable del cambio.
- Baja del cliente con validación de que no tenga vehículos dentro del parqueadero.
- Reactivación del cliente mediante un nuevo pago.
- Integración con la gestión de entradas: solo ingresa un vehículo cuya mensualidad siga vigente.
- Auditoría del usuario autenticado responsable de cada pago, baja o reactivación.
- Reporte operativo de pagos del día y del mes para el administrador.

### 5.2 Fuera de alcance

- Pasarela de pagos en línea o integración con bancos o PSE.
- Facturación electrónica, DIAN, retención en la fuente o cálculo de impuestos.
- Retención física del vehículo por mora.
- Suspensión temporal del contrato.
- Cobros por día o por horas; el parqueadero solo trabaja por mensualidad.
- Descuentos, promociones, pagos parciales o abonos.
- Recordatorios automáticos de pago por correo o WhatsApp (queda como mejora voluntaria).
- Devoluciones o reembolsos de mensualidades ya registradas.
- Aplicación móvil.

## 6. Requisitos funcionales

### Registro de pagos

- **RF-I3-01:** permitir al operador autenticado registrar un pago indicando vehículo, fecha del pago, valor y medio.
- **RF-I3-02:** registrar como responsable del pago la cuenta autenticada; el frontend no puede sustituir esa identidad.
- **RF-I3-03:** rechazar un pago cuyo vehículo no esté registrado, cuyo cliente esté inactivo sin ser reactivado explícitamente o cuyos datos estructurales sean inválidos.
- **RF-I3-04:** calcular la nueva fecha de corte de la mensualidad extendiéndola 30 días a partir de la fecha de corte vigente.
- **RF-I3-05:** para el primer pago de un cliente nuevo o reactivado, fijar la fecha de corte a 30 días después de la fecha del pago.
- **RF-I3-06:** no mover la fecha de corte hacia adelante cuando el pago se realiza antes del vencimiento.
- **RF-I3-07:** no mover la fecha de corte hacia adelante cuando el pago se realiza después del vencimiento; la vigencia se calcula siempre desde la fecha de corte anterior.
- **RF-I3-08:** guardar la fecha del pago como dato independiente de la fecha de corte.
- **RF-I3-09:** permitir al administrador anular un pago registrado por error, revirtiendo la fecha de corte a su valor anterior y conservando el registro con estado anulado.

### Vigencia y consulta

- **RF-I3-10:** exponer la mensualidad vigente por vehículo con su fecha de corte, estado y fecha del último pago.
- **RF-I3-11:** indicar explícitamente si una mensualidad está vigente o vencida tomando como referencia la fecha actual.
- **RF-I3-12:** listar el historial de pagos de un vehículo o de un cliente, con usuario responsable, fecha de pago, valor, medio y estado del pago.
- **RF-I3-13:** restringir el ingreso del vehículo cuando su mensualidad esté vencida, reutilizando la validación existente de la Iteración 1 pero contra el nuevo modelo de pagos.

### Gestión del cliente

- **RF-I3-14:** permitir inactivar un cliente desde la plataforma, cambiando su estado a inactivo y registrando usuario, fecha y motivo.
- **RF-I3-15:** impedir inactivar un cliente que tenga al menos un vehículo con permanencia abierta.
- **RF-I3-16:** ocultar los clientes inactivos de las consultas operativas normales y mostrarlos solo en reportes de auditoría.
- **RF-I3-17:** permitir reactivar un cliente inactivo cuando se registre un nuevo pago para alguno de sus vehículos; el pago establece una nueva fecha de corte a partir del día del pago.

### Reportes operativos

- **RF-I3-18:** generar un reporte de pagos del día con total recaudado, cantidad de pagos y responsables.
- **RF-I3-19:** generar un reporte mensual acumulado para el administrador, discriminado por medio de pago.
- **RF-I3-20:** exponer un listado administrativo de mensualidades próximas a vencer en los próximos siete días.

## 7. Requisitos no funcionales

- **RNF-I3-01 — Consistencia de fechas:** el cálculo de la fecha de corte debe funcionar en la zona horaria oficial del parqueadero (`America/Bogota`) y no verse afectado por la hora del servidor o del navegador.
- **RNF-I3-02 — Integridad transaccional:** el registro de un pago, la actualización de la fecha de corte y la reactivación del cliente deben ejecutarse en una sola transacción. Ante error, no debe quedar un pago sin vigencia actualizada ni una vigencia modificada sin pago.
- **RNF-I3-03 — Idempotencia controlada:** si el frontend reintenta un pago por un problema de red, el backend debe reconocer el mismo intento dentro de una ventana corta y evitar duplicar el registro.
- **RNF-I3-04 — Trazabilidad:** cada pago, anulación, baja y reactivación debe conservar usuario responsable, fecha y motivo cuando aplique.
- **RNF-I3-05 — Seguridad:** el valor del pago, el medio y el responsable nunca se exponen en respuestas de rutas públicas; todas las rutas de pagos exigen sesión autenticada.
- **RNF-I3-06 — Auditoría:** la anulación de un pago nunca lo elimina físicamente; se marca como anulado y queda consultable desde el reporte de auditoría.
- **RNF-I3-07 — Compatibilidad con iteraciones previas:** las reglas de entrada, salida, ocupación, usuarios y celdas siguen funcionando sin regresión.
- **RNF-I3-08 — Rendimiento operativo:** la consulta de vigencia por placa debe responder en menos de 500 ms bajo carga normal del parqueadero.
- **RNF-I3-09 — Reproducibilidad:** la iteración se ejecuta mediante Docker Compose desde un clon limpio, sin pasos manuales adicionales respecto a la Iteración 2.
- **RNF-I3-10 — Zona horaria y formato:** las fechas se almacenan en PostgreSQL con `timestamptz` y se serializan en ISO 8601 con zona horaria explícita en la API.

## 8. Reglas de negocio

| ID | Regla |
|---|---|
| RN-I3-01 | La mensualidad es siempre de 30 días calendario. No se cobra por horas ni por días sueltos. |
| RN-I3-02 | La fecha del pago no desplaza la fecha de corte. |
| RN-I3-03 | La nueva fecha de corte se calcula como fecha de corte anterior + 30 días. |
| RN-I3-04 | El primer pago de un cliente nuevo o reactivado fija la fecha de corte 30 días después del día del pago. |
| RN-I3-05 | Mientras la fecha actual sea menor o igual a la fecha de corte, la mensualidad está vigente. |
| RN-I3-06 | Un vehículo con mensualidad vencida no puede ingresar al parqueadero. |
| RN-I3-07 | El responsable del pago es la cuenta autenticada que lo registra, no un identificador suministrado por el frontend. |
| RN-I3-08 | El cliente inactivo se conserva en la base de datos y no se muestra en consultas operativas. |
| RN-I3-09 | No se puede inactivar un cliente con un vehículo dentro del parqueadero. |
| RN-I3-10 | Reactivar un cliente requiere un pago nuevo que establezca una nueva fecha de corte. |
| RN-I3-11 | La anulación de un pago requiere perfil administrador y revierte la fecha de corte asociada. |
| RN-I3-12 | El sistema no retiene vehículos por mora ni suspende contratos. |
| RN-I3-13 | El valor del pago se registra tal como se recibió; el sistema no calcula descuentos ni impuestos. |
| RN-I3-14 | Un pago anulado no cuenta en los reportes de recaudo, pero sigue siendo consultable para auditoría. |

## 9. Historias de usuario

### HU-I3-01. Registrar un pago mensual

**Como** operador autenticado, **quiero** registrar el pago mensual de un vehículo con su fecha, valor y medio, **para** habilitar su ingreso durante la siguiente vigencia.

- Un vehículo registrado y con cliente activo permite registrar el pago.
- Al confirmar, la nueva fecha de corte se extiende 30 días desde la fecha de corte vigente.
- El pago queda asociado a la cuenta autenticada que lo registró.

### HU-I3-02. Pagar antes del vencimiento sin perder días

**Como** cliente que paga por adelantado, **quiero** que la vigencia nueva se cuente desde mi fecha de corte, **para** no perder los días restantes de la mensualidad vigente.

- Dado un corte vigente a futuro, al registrar un pago anticipado, la nueva fecha de corte es exactamente la anterior más 30 días.
- La fecha del pago se conserva aparte como evidencia de cuándo se recibió el dinero.
- La vigencia nueva no se calcula sobre la fecha del pago.

### HU-I3-03. Pagar en mora sin correr la fecha de corte

**Como** cliente que paga después del vencimiento, **quiero** que la fecha de corte continúe con el ciclo original, **para** no cambiar el día habitual de pago.

- Dado un corte vencido, al registrar el pago, la nueva fecha de corte es la fecha de corte anterior más 30 días, no la fecha del pago más 30 días.
- El operador puede ver que el pago fue en mora pero la vigencia respeta el ciclo original.
- Si el pago en mora cubre más de un ciclo, el sistema registra un pago por cada ciclo adeudado (decisión del administrador).

### HU-I3-04. Primer pago de un cliente

**Como** operador, **quiero** registrar el primer pago de un cliente nuevo o reactivado, **para** dejar su mensualidad vigente a partir de ese día.

- El vehículo o cliente no tiene fecha de corte previa.
- Al registrar el pago, la fecha de corte queda a 30 días a partir de la fecha del pago.
- El cliente queda activo si estaba inactivo.

### HU-I3-05. Consultar vigencia de una placa

**Como** operador, **quiero** consultar la vigencia actual de un vehículo por su placa, **para** saber si puede ingresar o si debe pagar antes.

- La consulta devuelve fecha de corte, estado vigente o vencido y fecha del último pago.
- Si el vehículo no existe, se informa claramente.
- La consulta no modifica el estado del sistema.

### HU-I3-06. Consultar historial de pagos

**Como** administrador u operador, **quiero** consultar los pagos realizados por un vehículo o un cliente, **para** aclarar dudas y auditar la operación.

- El historial muestra fecha de pago, valor, medio, responsable y estado del pago.
- Los pagos anulados aparecen marcados como tal.
- El historial se puede filtrar por fecha.

### HU-I3-07. Dar de baja a un cliente

**Como** operador, **quiero** dar de baja a un cliente que se retira del parqueadero, **para** reflejarlo en la plataforma sin perder su historial.

- Si el cliente tiene algún vehículo dentro del parqueadero, el sistema impide la baja y lo explica.
- Al confirmar la baja, el cliente deja de aparecer en consultas operativas pero sigue existiendo en la base de datos.
- La baja registra usuario responsable, fecha y motivo opcional.

### HU-I3-08. Reactivar un cliente con un nuevo pago

**Como** operador, **quiero** reactivar un cliente inactivo cuando vuelve a pagar, **para** habilitar nuevamente sus vehículos.

- El operador localiza al cliente inactivo mediante documento o placa previa.
- Al registrar un pago para alguno de sus vehículos, el cliente queda activo y con fecha de corte 30 días después del pago.
- La reactivación queda auditada.

### HU-I3-09. Anular un pago mal registrado

**Como** administrador, **quiero** anular un pago registrado por error, **para** corregir la vigencia sin dejar fuera de cuadre al cliente.

- Solo el administrador puede anular un pago.
- La anulación revierte la fecha de corte al valor que tenía antes del pago.
- El pago anulado conserva su registro para auditoría y no se cuenta en el recaudo.

### HU-I3-10. Consultar recaudo del día

**Como** administrador, **quiero** ver el total recaudado del día, con detalle por medio de pago y responsable, **para** cuadrar el cierre operativo.

- El reporte muestra total, cantidad de pagos y responsables.
- Los pagos anulados no se incluyen en el total.
- El reporte puede consultarse para cualquier fecha pasada.

### HU-I3-11. Notificar vencimiento cercano (voluntario)

**Como** administrador, **quiero** enviar un aviso al cliente cuando su mensualidad esté por vencer, **para** reducir la mora y evidenciar el aviso.

- La notificación se envía por correo o WhatsApp si el cliente tiene el dato registrado.
- El sistema conserva el envío como evidencia.
- No es obligatorio para aprobar la iteración; solo se activa si el equipo decide implementarlo.

## 10. Modelo conceptual ampliado

| Entidad | Campos principales | Propósito |
|---|---|---|
| `Payment` | `id`, `vehicle_id`, `client_id`, `amount`, `payment_method`, `paid_at`, `coverage_start`, `coverage_end`, `previous_cutoff`, `recorded_by`, `status`, `annulled_at`, `annulled_by`, `annulment_reason`, `created_at` | Representa un pago mensual, el ciclo de vigencia que cubre y su responsable autenticado. |
| `Membership` (actualizada) | Campos previos más `current_cutoff_date`, `last_payment_id`, `activated_at` | Expone la fecha de corte vigente y vincula el último pago aplicado. |
| `Client` (actualizada) | Campos previos más `status` (`ACTIVE` / `INACTIVE`), `inactivated_at`, `inactivated_by`, `inactivation_reason`, `reactivated_at`, `reactivated_by` | Soporta baja y reactivación conservando auditoría. |
| `PaymentAudit` | `id`, `payment_id`, `action`, `account_id`, `occurred_at`, `previous_state`, `new_state` | Trazabilidad de creación, anulación o corrección de un pago. |
| `ClientStatusAudit` | `id`, `client_id`, `action`, `account_id`, `occurred_at`, `reason` | Trazabilidad de bajas y reactivaciones del cliente. |

### Relaciones nuevas

- Un cliente tiene muchos pagos (a través de sus vehículos).
- Un vehículo tiene muchos pagos a lo largo del tiempo.
- Un pago vigente apunta al corte anterior para permitir anulaciones reversibles.
- Una mensualidad conserva la referencia al último pago aplicado.

## 11. Contrato REST previsto

| Método | Ruta | Perfil | Propósito |
|---|---|---|---|
| `POST` | `/api/pagos` | Ambos | Registrar un pago y recalcular la fecha de corte |
| `GET` | `/api/pagos` | Ambos | Listar pagos por vehículo, cliente, rango de fechas o responsable |
| `GET` | `/api/pagos/{id}` | Ambos | Consultar detalle de un pago |
| `PATCH` | `/api/pagos/{id}/anular` | Administrador | Anular un pago y revertir la fecha de corte |
| `GET` | `/api/mensualidades/vehiculo/{placa}` | Ambos | Consultar vigencia actual por placa |
| `GET` | `/api/mensualidades/cliente/{id}` | Ambos | Consultar vigencias de todos los vehículos de un cliente |
| `GET` | `/api/mensualidades/por-vencer` | Administrador | Listar mensualidades que vencen en los próximos N días |
| `PATCH` | `/api/clientes/{id}/baja` | Ambos | Inactivar al cliente |
| `PATCH` | `/api/clientes/{id}/reactivar` | Ambos | Reactivar al cliente mediante un pago nuevo |
| `GET` | `/api/reportes/recaudo` | Administrador | Recaudo del día o del mes, con totales por medio |

### 11.1 Respuestas de error específicas

| Código | Significado en Iteración 3 |
|---|---|
| `401 Unauthorized` | Sesión inválida o expirada. |
| `403 Forbidden` | Cuenta autenticada sin perfil autorizado para la acción (por ejemplo, anular un pago siendo operador). |
| `404 Not Found` | Vehículo, cliente o pago no existen. |
| `409 Conflict` | Cliente con vehículo dentro intenta inactivarse, o pago duplicado detectado en la ventana de idempotencia. |
| `422 Unprocessable Entity` | Datos estructuralmente inválidos (valor negativo, medio desconocido, fecha inválida). |

## 12. Datos iniciales adicionales

La semilla de Iteración 3 debe incluir, además de la base de iteraciones previas:

- Al menos un cliente con mensualidad vigente y pagos previos registrados para probar historial.
- Al menos un cliente con mensualidad vencida para probar rechazo de ingreso y pago en mora.
- Al menos un cliente inactivo para probar reactivación.
- Al menos un pago anulado para probar reportes de auditoría.
- Tabla de medios de pago soportados (`EFECTIVO`, `TRANSFERENCIA`, `QR`).

## 13. Criterios globales de aceptación

La Iteración 3 se considera funcional cuando:

- El operador puede registrar un pago indicando vehículo, fecha, valor y medio.
- La nueva fecha de corte siempre se calcula como fecha de corte anterior + 30 días, sin importar si el pago fue anticipado, el día justo o en mora.
- El primer pago de un cliente nuevo o reactivado parte desde la fecha del pago.
- La fecha del pago se conserva aparte y nunca desplaza la fecha de corte.
- Un vehículo con mensualidad vencida es rechazado en el flujo de entrada de la Iteración 1.
- Un cliente puede ser inactivado solo si no tiene vehículos dentro del parqueadero.
- Un cliente inactivo no aparece en consultas operativas pero sigue existiendo para auditoría.
- Un pago anulado revierte correctamente la fecha de corte y no entra al recaudo.
- Los reportes de recaudo del día y del mes coinciden con la suma de pagos no anulados.
- Las iteraciones 1 y 2 siguen funcionando sin regresión.
- El sistema se levanta con Docker Compose desde un clon limpio.

## 14. Entregables académicos asociados

| ID | Entregable requerido | Responsable principal |
|---|---|---|
| D3-01 | Requisitos funcionales y no funcionales de pagos | Camilo |
| D3-02 | Plan de pruebas resumido de pagos | Camilo |
| D3-03 | Diagrama de casos de uso de pagos en StarUML | Paul |
| D3-04 | Diagrama de secuencia acumulativo de las iteraciones 1, 2 y 3 en StarUML | Paul |
| D3-05 | Diagrama de componentes acumulativo de las tres iteraciones en StarUML | Paul |
| D3-06 | Historias de usuario de pagos | Mafe |
| D3-07 | Mockups en Figma de pagos | Mafe |
| D3-08 | URL del repositorio en GitHub | Grupal |
| D3-09 | Video en YouTube de las tres iteraciones | Grupal |
| D3-10 | PDF final con portada, introducción, entregables y conclusiones | Grupal, Mafe compila |

El documento final usa la nomenclatura `Apellido_Nombre_EA3`.

## 15. Restricciones para la implementación

1. No implementar pasarela de pagos, DIAN, retenciones ni cálculos tributarios.
2. No eliminar clientes, pagos ni mensualidades; solo marcar estados.
3. No calcular la nueva fecha de corte usando la fecha del pago como base.
4. No introducir suspensiones temporales de contrato.
5. No bloquear o retener físicamente un vehículo por mora.
6. Mantener `main` estable; el trabajo de pagos se integra por ramas cortas con su propia rama integradora.
7. Documentar y versionar únicamente los cambios necesarios; no reescribir módulos de iteraciones 1 y 2 sin justificación.

## 16. Trazabilidad

| Historia | Requisitos |
|---|---|
| HU-I3-01 | RF-I3-01, RF-I3-02, RF-I3-04, RF-I3-08 |
| HU-I3-02 | RF-I3-04, RF-I3-06 |
| HU-I3-03 | RF-I3-04, RF-I3-07 |
| HU-I3-04 | RF-I3-05, RF-I3-17 |
| HU-I3-05 | RF-I3-10, RF-I3-11 |
| HU-I3-06 | RF-I3-12 |
| HU-I3-07 | RF-I3-14, RF-I3-15, RF-I3-16 |
| HU-I3-08 | RF-I3-17, RF-I3-05 |
| HU-I3-09 | RF-I3-09 |
| HU-I3-10 | RF-I3-18, RF-I3-19 |
| HU-I3-11 | Mejora voluntaria asociada a RF-I3-20 |

## 17. Preguntas abiertas no bloqueantes

1. ¿Se permite al operador registrar más de un pago el mismo día para el mismo vehículo (por ejemplo, para cubrir dos ciclos en mora)?
2. ¿El valor de la mensualidad es fijo por tipo de vehículo o lo digita el operador en cada pago?
3. ¿El reporte mensual debe exportarse a CSV o basta con mostrarse en pantalla?
4. ¿El administrador puede editar la fecha de corte directamente para corregir casos extraordinarios, o siempre debe pasar por la anulación de un pago?
5. ¿La notificación voluntaria por WhatsApp usará un proveedor externo o solo se dejará como ejemplo documentado en la evidencia?

Hasta que el cliente confirme, la implementación usa la opción más simple que respete las reglas vigentes y no amplíe el alcance.
