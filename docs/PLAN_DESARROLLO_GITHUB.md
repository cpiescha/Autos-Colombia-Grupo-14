# Plan de desarrollo en GitHub — Autos Colombia, Iteraciones 1 y 2

> Plan de colaboración para continuar la aplicación de parqueadero sin conflictos de integración. La base funcional construida corresponde al [PRD de Iteración 1](PRD_Autos_Colombia_Iteracion_1.md); el alcance confirmado de autenticación, perfiles y celdas está en el [PRD de Iteración 2](PRD_Autos_Colombia_Iteracion_2.md). Ambas iteraciones comparten la [arquitectura técnica](ARQUITECTURA_TECNICA_AUTOS_COLOMBIA.md).

## 1. Decisiones de trabajo

- **Rama protegida de entrega:** `main`. Debe estar siempre ejecutable y no recibe pushes directos.
- **Rama integradora de la Iteración 2:** `camilo-backend`. Se sincroniza desde `main` antes de comenzar y recibe los PR de las tareas T16–T29.
- **Ramas por tarea:** cada trabajo se desarrolla en una rama corta creada desde la versión más reciente de `camilo-backend`, con nombres como `docs/i2-t16-contract` o `feat/i2-t19-authentication`.
- **Un PR por tarea:** cada pull request contiene únicamente una tarea del backlog y apunta a `camilo-backend`; ningún PR hijo de la Iteración 2 apunta directamente a `main`.
- **PR integrador:** `camilo-backend` mantiene un PR draft hacia `main`. Solo pasa a revisión y se fusiona después de completar y verificar T29.
- **Sin rebase ni fuerza:** las actualizaciones se realizan mediante avance rápido o `merge`; no se permite `rebase`, `push --force` ni trabajo directo sobre `main` o `camilo-backend`.
- **Integración por oleadas:** primero contrato, luego persistencia y pantallas base, después seguridad, integración, pruebas y evidencia.
- **Autoridad de datos:** FastAPI y PostgreSQL deciden validaciones, asignaciones y transacciones; Angular solo presenta el resultado confirmado.

### Stack acordado

| Capa | Tecnología |
|---|---|
| Frontend | Angular 22, TypeScript y Angular Material |
| Backend | Python 3.12, FastAPI y SQLAlchemy |
| Datos | PostgreSQL 16 |
| Entorno | Docker Compose |

## 2. Estado actual del repositorio

El repositorio ya está publicado en GitHub y la Iteración 1 se encuentra integrada en `main`. La Iteración 2 parte de esa versión; no se reinicializa el repositorio ni se vuelve a crear la estructura técnica.

Antes de comenzar T16 se debe comprobar:

```bash
git fetch origin
git switch main
git merge --ff-only origin/main
git status
```

`main` debe permanecer sin cambios locales y ejecutable. La rama `camilo-backend` se sincroniza desde esa referencia siguiendo el apartado 3.2.

No subir `.env`, credenciales, volúmenes de PostgreSQL, `node_modules/`, `.venv/` ni archivos de construcción. Los valores configurables se documentan mediante `.env.example` sin información sensible.

En GitHub, proteger `main`: requerir PR, al menos una revisión del equipo cuando haya disponibilidad, conversaciones resueltas y validaciones aprobadas. Si el plan de GitHub no permite reglas automáticas, el equipo aplica las mismas condiciones manualmente. `camilo-backend` también se trata como rama protegida por acuerdo del equipo: recibe únicamente PR revisados y no commits directos.

## 3. Ramas de trabajo y pull requests

### 3.1 Estructura de integración de la Iteración 2

La Iteración 2 utiliza una rama integradora y ramas cortas por tarea:

```text
main
 └── camilo-backend                 ← rama integradora y PR tracker
      ├── docs/i2-t16-contract
      ├── feat/i2-t17-internal-accounts
      ├── feat/i2-t18-cell-status
      ├── feat/i2-t19-authentication
      └── ...
```

| Rama | Función |
|---|---|
| `main` | Versión estable que ejecutará el profesor; solo recibe el PR final de la iteración |
| `camilo-backend` | Acumula la Iteración 2 y mantiene un PR draft hacia `main` |
| `type/i2-tNN-description` | Rama corta de una tarea; abre un PR hacia `camilo-backend` y se elimina después de integrarse |
| `paul-database`, `mafe-frontend` | Ramas históricas de la Iteración 1; no son bases de integración para la Iteración 2 |

Este esquema es una cadena de integración por dependencias: cada nueva rama nace de `camilo-backend` actualizado y entrega una unidad revisable. No se mantiene una cadena lineal de catorce PR abiertos porque dificultaría corregir, revisar y fusionar trabajo paralelo.

### 3.2 Preparar la rama integradora

Antes de T16, Camilo sincroniza `camilo-backend` con la versión estable:

```bash
git fetch origin
git switch camilo-backend
git merge --ff-only origin/main
git push origin camilo-backend
```

Si el avance rápido no es posible, el equipo debe revisar la divergencia antes de continuar; no se resuelve con `rebase` ni `push --force`.

El PR tracker `camilo-backend` → `main` se abre como **draft** cuando el primer PR hijo, T16, ya haya producido una diferencia visible. Permanece abierto y sin fusionar hasta completar T29.

### 3.3 Crear una rama de tarea

Siempre se parte de la rama integradora actualizada:

```bash
git switch camilo-backend
git fetch origin
git merge --ff-only origin/camilo-backend
git switch -c feat/i2-t19-authentication
```

Convención de nombres:

```text
feat/i2-tNN-description
docs/i2-tNN-description
test/i2-tNN-description
fix/i2-tNN-description
```

### 3.4 Regla de los PR hijos

- Cada PR resuelve un solo issue/T-ID y apunta a `camilo-backend`.
- El título usa el ID de la tarea, por ejemplo: `[T19] Implementar autenticación`.
- El cuerpo indica qué se hizo, cómo se verificó, de qué depende y qué queda fuera.
- Cada PR debe ser revisable en aproximadamente una hora y procurar no superar 400 líneas modificadas de trabajo autoral.
- Las pruebas y la documentación viajan en el mismo PR que el comportamiento que verifican.
- T17/T18 y T23/T24 pueden avanzar en paralelo después de T16 porque trabajan en superficies separadas.
- Un PR dependiente se mantiene como draft hasta que sus requisitos previos estén integrados en `camilo-backend`.
- Los PR hijos se fusionan mediante **Create a merge commit**. No se usa squash, rebase ni force push.
- Los issues T16–T29 son obligatorios para conectar alcance, responsable, dependencias y evidencia.

## 4. Propiedad de archivos y zonas de integración

La propiedad evita ediciones simultáneas, pero no reemplaza la revisión cruzada.

| Responsable | Propietario principal | Puede modificar con coordinación previa |
|---|---|---|
| **Camilo** | `backend/app/` (rutas, esquemas, servicios, pruebas del backend), integración Angular–API y flujos complejos de frontend | `frontend/src/app/core/`, `frontend/src/app/features/` cuando consume API; `docker-compose.yml` |
| **Paul** | `backend/app/models/` o `models.py`, `backend/app/database.py`, migraciones/DDL, restricciones, semillas y pruebas de persistencia | Contratos de esquema/API junto con Camilo; `docker-compose.yml` para el servicio `db` |
| **Mafe** | `frontend/src/app/shared/`, componentes presentacionales Material, estilos, navegación básica, mensajes y pruebas manuales | Vistas de `frontend/src/app/features/` sin lógica de integración compleja, coordinadas con Camilo |
| **Compartido** | `docs/`, `README.md`, `docker-compose.yml`, `.env.example`, contrato API | Un único editor por PR; avisar en el issue y esperar integración de cambios recientes |

### Hotspots que requieren acuerdo antes de editar

1. `docker-compose.yml`, `.env.example` y `README.md`.
2. Modelos SQLAlchemy, migraciones, semillas y restricciones PostgreSQL.
3. DTO/esquemas, nombres de rutas y formatos de error de FastAPI.
4. Servicios Angular que consumen API y las rutas de navegación.
5. Cualquier cambio al contrato de API o a la semántica de una regla RN/RF del PRD.

Para un hotspot, el autor abre primero el issue, escribe la decisión en el PR y solicita revisión de Camilo y Paul para datos/API, o de Camilo y Mafe para frontend/API. No se implementan dos versiones en paralelo.

## 5. Oleadas y dependencias

| Oleada | Resultado integrable | Condición de inicio |
|---|---|---|
| A — Base | Proyecto clonable y levantable con Docker Compose; frontend, backend y base definidos | Repositorio inicializado |
| B — Datos y contrato | Modelo persistente, 80 celdas, datos de prueba y contrato API acordado | A fusionada |
| C — Flujos principales | Consulta, entrada, comprobante, salida y disponibilidad de punta a punta | B fusionada |
| D — Robustez y cierre | Corrección de celda, concurrencia, reportes, documentación y verificación final | C fusionada |

Regla de avance: en la Iteración 1 cada persona toma una tarea cuya dependencia esté en `main`; en la Iteración 2 la dependencia debe estar integrada en `camilo-backend`. Puede preparar investigación o mockups antes, pero un PR dependiente permanece como **draft** hasta que su base esté disponible.

## 6. Backlog ejecutable

### 6.1 Entregables académicos

Esta distribución no debe confundirse con las tareas técnicas del repositorio:

| Punto | Entregable | Responsable |
|---|---|---|
| 1 | Requisitos funcionales y no funcionales | Camilo |
| 2 | Historias de usuario | Camilo |
| 3 | Arquitectura del sistema en StarUML | Camilo |
| 4 | Mockups en Figma | Paul |
| 5 | MER, modelo relacional y modelo físico | Paul |
| 6 | Diagramas de casos de uso en StarUML | Paul |
| 7 | Diagrama de clases en StarUML | Mafe, con clases y relaciones acordadas con Camilo y Paul |
| 8 | Diagrama de paquetes en StarUML | Mafe, con paquetes y dependencias definidos por el equipo |
| 9 | Código fuente ejecutable y repositorio GitHub | Los tres |

### 6.2 Tareas técnicas del repositorio

Los IDs siguientes describen unidades de código y documentación. No corresponden al número del entregable académico.

| ID | Área / responsable | Depende de | Entregable delimitado | Verificación |
|---|---|---|---|---|
| T01 | Base / Camilo | Repositorio inicializado | Estructura `frontend/`, `backend/`, `.gitignore`, `.env.example`, Compose y README mínimo | `docker compose up --build` inicia los tres servicios y los datos persisten tras reiniciar aplicaciones |
| T02 | Persistencia / Paul | T01 | Entidades Cliente, Vehículo, Mensualidad, Celda, Movimiento, Comprobante, Operario y corrección; relaciones y tipos | La base crea el esquema y las relaciones requeridas por el PRD |
| T03 | Presentación básica / Mafe | T01 | Angular Material, layout, navegación básica, tema/estilos y área de mensajes presentacionales | `npm run build` y navegación entre vistas sin errores visuales básicos |
| T04 | Integridad y semillas / Paul | T02 | 10 celdas moto, 70 automóvil, datos de clientes/vehículos/mensualidades/operarios; restricciones de movimientos abiertos | Semilla repetible; 80 celdas y unicidad de vehículo/celda abiertos comprobables |
| T05 | Consulta y autorización / Camilo | T02, T04 | `GET /api/vehiculos/{placa}`, normalización y causas de rechazo | Pruebas de placa existente, inexistente, vencida y tipo no permitido |
| T06 | Entrada y comprobante / Camilo | T04, T05 | Transacción de entrada, asignación compatible, comprobante único y respuesta de API | Una moto usa celda moto; carro/camioneta usa automóvil; fallo no deja estado parcial |
| T07 | UI presentacional de consulta e ingreso / Mafe | T03 | Componentes Material con `@Input` y `@Output`, formularios visuales, ficha de vehículo y mensajes usando datos simulados | Prueba manual documentada de estados de éxito, inexistente y vencido, sin lógica HTTP dentro de los componentes |
| T08 | Integración de ingreso / Camilo | T05, T06, T07 | Servicio Angular y páginas contenedoras que consumen la API y muestran celda/comprobante confirmados | El frontend no asigna por cuenta propia y refleja respuestas y errores de API |
| T09 | Persistencia de salida y corrección / Paul | T02, T04 | Consultas y restricciones para cerrar movimiento, liberar celda y auditar correcciones | Salida/corrección atómica; no se duplican vehículos ni celdas abiertas |
| T10 | API de salida, disponibilidad y reportes / Camilo | T06, T09 | Endpoints de salida, celdas, movimientos activos, ocupación y corrección; reglas de negocio | Comprobante inválido no cambia estado; totales derivan de movimientos abiertos |
| T11 | UI presentacional de salida y ocupación / Mafe | T03 | Componentes Material, tablas, estados vacíos, mensajes y navegación con datos simulados | Componentes visibles y navegables; no contienen llamadas HTTP ni cálculos definitivos de ocupación |
| T12 | Integración del frontend restante / Camilo | T10, T11 | Servicios y páginas contenedoras para salida, ocupación, movimientos activos, reportes y corrección | Cada pantalla refleja el resultado de FastAPI y conserva el estado ante rechazos |
| T13 | Concurrencia / Camilo | T10 | Pruebas de servicios/endpoints para dos ingresos simultáneos y última celda | Dos solicitudes no obtienen la misma celda; una se rechaza cuando queda una |
| T14 | Ajuste visual y evidencia / Mafe | T07, T11, T12 | Estilos finales, mensajes claros, capturas y registro de pruebas manuales guiadas | Revisión contra RNF-04; flujos de entrada y salida comprensibles y utilizables |
| T15 | Entrega integrada / Compartido | T12, T13, T14 | README final, despliegue, pruebas, trazabilidad y material académico restante | Clonado limpio + Docker Compose + recorrido de criterios globales del PRD |

**Orden práctico:** Paul y Mafe pueden iniciar T02 y T03 después de T01. Camilo inicia T05 cuando T04 esté fusionada. Mafe construye T07 y T11 con datos simulados; Camilo agrega la integración HTTP en T08 y T12 sin trasladarle esa complejidad a Mafe. Cada PR debe respetar estas dependencias.

## 7. Flujo sencillo de trabajo

### Antes de comenzar una tarea de la Iteración 2

Cada persona actualiza la referencia remota, cambia a `camilo-backend` y crea una rama corta:

```bash
git fetch origin
git switch camilo-backend
git merge --ff-only origin/camilo-backend
git switch -c feat/i2-tNN-description
```

Si existen cambios locales, primero se revisan con `git status`; no se ocultan ni se mezclan con la tarea nueva.

### Mientras trabaja

```bash
git status
git add <archivos-exactos-de-la-tarea>
git commit -m "feat(T19): implementar autenticación"
git push -u origin feat/i2-t19-authentication
```

No usar `git add .` cuando haya documentos, secretos o artefactos sin seguimiento. Cada commit debe usar una convención reconocible y contener una unidad coherente.

### Cuando termina la tarea

1. Abrir un PR desde la rama de tarea hacia `camilo-backend`.
2. Vincular el issue T-ID correspondiente.
3. Documentar alcance, dependencias, pruebas, resultado y trabajo excluido.
4. Pedir la revisión indicada en el apartado 8.
5. Corregir observaciones en la misma rama y volver a ejecutar `git push`.
6. Fusionar con **Create a merge commit** cuando las validaciones estén aprobadas.
7. Actualizar `camilo-backend` local antes de crear la siguiente rama:

```bash
git switch camilo-backend
git fetch origin
git merge --ff-only origin/camilo-backend
```

8. Eliminar la rama corta únicamente después de confirmar que el PR quedó integrado.

> No usar `rebase`, `push --force` ni trabajar directamente en `main` o `camilo-backend`. Si aparece un conflicto durante la actualización, detenerse y aplicar el protocolo del apartado 9.

## 8. Reglas de PR, revisión y fusión

### Lista de comprobación del autor

- [ ] El PR resuelve un único issue/T-ID y su título respeta la convención.
- [ ] La rama de tarea nació de la versión más reciente de `origin/camilo-backend` y no incluye archivos ajenos, secretos ni artefactos generados.
- [ ] Se respetó la propiedad de directorios y se avisó si se tocó un hotspot.
- [ ] Se actualizaron contrato, README o documentación si el cambio lo exige.
- [ ] Se ejecutaron las validaciones de la tarea y se adjuntó el resultado.
- [ ] Los casos rechazados no dejan movimiento, celda ni comprobante en estado parcial.
- [ ] El PR es pequeño, idealmente alrededor de 400 líneas modificadas por trabajo autoral; los archivos generados del scaffold se justifican por separado. Si excede su objetivo, se divide antes de solicitar revisión.

### Revisión mínima

- **PR de Camilo (API/integración):** Paul revisa persistencia/transacciones; Mafe valida el resultado visible cuando aplique.
- **PR de Paul (datos):** Camilo revisa compatibilidad con reglas y contrato API.
- **PR de Mafe (presentación):** Camilo revisa integración y Mafe conserva el control visual; Paul no necesita revisar salvo que afecte datos.
- **PR compartido/hotspot:** revisan los dos responsables afectados.

Usar **Create a merge commit** para integrar cada PR hijo en `camilo-backend`. El único PR de la Iteración 2 que apunta a `main` es el tracker final desde `camilo-backend`. Solo fusionar cuando las validaciones y la revisión acordada estén completas. Quien abrió el PR resuelve los comentarios antes de fusionar; nadie fusiona el PR de otra persona sin avisarle.

## 9. Protocolo de conflictos

1. **Detenerse:** no resolver por intuición un conflicto en modelo, migración, Compose, contrato API o navegación.
2. **Identificar:** publicar en el issue/PR el archivo, las ramas involucradas y la intención de ambos cambios.
3. **Decidir por propiedad:** Paul decide la forma de persistencia; Camilo la regla y contrato API; Mafe la presentación. En un límite entre capas, Camilo y Paul acuerdan primero el contrato y Mafe adapta la vista.
4. **Resolver una sola persona:** el autor de la rama que integra incorpora la decisión, ejecuta la validación afectada y documenta el resultado en el PR.
5. **Revisar de nuevo:** quien es dueño del área conflictiva aprueba la resolución antes del merge.

Para evitar conflictos previsibles en la Iteración 2: crear cada rama desde `origin/camilo-backend` actualizado; mantener pocos PR simultáneos y solo cuando sus superficies sean independientes; no reformatear archivos ajenos; no mezclar cambios de estilo con lógica; y avisar en el grupo antes de editar un hotspot.

## 10. Definición de terminado de la Iteración 1

T15 solo se cierra cuando el equipo puede, desde un clon limpio y con las instrucciones del README:

1. levantar Angular, FastAPI y PostgreSQL con Docker Compose;
2. consultar un vehículo autorizado y uno rechazado;
3. registrar entrada con celda compatible y comprobante único;
4. verificar que dos ingresos concurrentes no compartan celda;
5. registrar salida y comprobar que libera la celda;
6. consultar disponibilidad, vehículos presentes y reporte; y
7. corregir una ubicación sin crear duplicidades y con trazabilidad.

Cualquier pregunta no resuelta del PRD se registra como issue de decisión; no se amplía el alcance de la Iteración 1 dentro de un PR de implementación.

## 11. Continuación para la Iteración 2 — usuarios y celdas

> Fuente funcional: [PRD de Iteración 2](PRD_Autos_Colombia_Iteracion_2.md). Si el backlog y el PRD difieren, primero se corrige la documentación y luego se implementa; ningún PR redefine requisitos por su cuenta.

### 11.1 Diagnóstico del repositorio actual

La Iteración 1 ya deja una base reutilizable y **no se debe comenzar de cero**:

- Existe la entidad cliente y la relación cliente–vehículo, pero la sesión sincrónica aclaró que la **gestión de usuarios de esta entrega corresponde a las cuentas internas del administrador y los operadores**, no al CRUD completo de clientes.
- Existe la entidad operario para registrar quién ejecuta entradas, salidas y correcciones, pero actualmente no hay inicio de sesión, contraseña, roles ni autorización real; el frontend usa un operario fijo.
- Ya existe un catálogo sembrado de 80 celdas (10 para motos y 70 para automóviles), consulta de ocupación, asignación automática, liberación en la salida y corrección de la celda de una permanencia abierta.
- Falta que el administrador pueda crear, anular o retirar celdas mediante su código y tipo. Las celdas inhabilitadas no deben aparecer como disponibles ni poder asignarse.
- Los documentos, pruebas manuales y mockups existentes describen la Iteración 1; todavía faltan los artefactos académicos específicos de la Iteración 2.

Por lo tanto, la Iteración 2 debe extender el modelo, la API y las pantallas actuales, sin duplicar la lógica de entradas, salidas, ocupación o corrección ya implementada.

### 11.2 Resumen vinculante de la sesión sincrónica del 28-10

El profesor definió y aclaró el alcance de la Actividad Evaluativa 2 de la siguiente manera:

1. La entrega cubre únicamente **gestión de usuarios internos** y **gestión de celdas**. La gestión de pagos corresponde a la Iteración 3 y no debe adelantarse.
2. El sistema tendrá solo dos perfiles: `ADMINISTRADOR` y `OPERADOR`.
3. Cada empleado debe ingresar con usuario y contraseña privados. No deben compartir credenciales.
4. Deben poder trabajar, como mínimo, dos operadores autenticados al mismo tiempo porque existen dos accesos al parqueadero.
5. El administrador crea y anula cuentas de operadores. Una cuenta anulada no puede volver a ingresar.
6. El administrador también puede ejecutar las funciones operativas de entrada y salida cuando deba cubrir un turno.
7. El operador se concentra en registrar vehículos, entradas y salidas. No puede administrar cuentas de empleados ni celdas.
8. Tanto administrador como operador pueden registrar un vehículo nuevo cuando la placa todavía no existe. Después de guardar, solo el administrador puede editar o eliminar el registro del vehículo.
9. Cada movimiento debe conservar qué usuario autenticado lo realizó, para evitar credenciales compartidas y permitir identificar responsabilidades.
10. Las celdas las administra únicamente el administrador. Debe poder crearlas, anularlas o retirarlas indicando código y tipo (`MOTO` o `AUTOMOVIL`).
11. Una celda anulada o inhabilitada no debe estar disponible para los operadores ni participar en una asignación.
12. La asignación de celda puede conservarse automática o mediante selección entre las disponibles. Como el repositorio ya asigna automáticamente y valida compatibilidad, se conservará esa solución para evitar rehacer un flujo correcto.
13. Los iconos que distinguen moto, automóvil y camioneta son un valor visual aceptado, siempre que no amplíen innecesariamente la lógica.
14. El profesor autorizó trabajar en ramas antes de cerrar la calificación anterior, pero pidió no dejar código incompleto en la versión que él ejecutará. `main` debe permanecer estable; el trabajo de la Iteración 2 queda en ramas cortas, en `camilo-backend` y en su PR tracker draft hasta completar la entrega.

El profesor también insistió en no agregar funcionalidades no validadas por el cliente. Por eso este plan elimina el CRUD completo de clientes que se había supuesto inicialmente y se limita a las cuentas internas, vehículos y celdas expresamente mencionados.

### 11.3 Requisitos funcionales y reglas de negocio

La definición normativa está en las secciones 6 a 8 del [PRD de Iteración 2](PRD_Autos_Colombia_Iteracion_2.md), con los identificadores `RF-I2-01` a `RF-I2-22`, `RNF-I2-01` a `RNF-I2-10` y `RN-I2-01` a `RN-I2-12`. Este plan no duplica ni renumera esos requisitos; únicamente los convierte en tareas ejecutables.

Resumen para asignación:

| Grupo | Alcance |
|---|---|
| `RF-I2-01`–`RF-I2-06` | Login, perfiles, cuenta activa, concurrencia, autorización y auditoría |
| `RF-I2-07`–`RF-I2-09` | Administración de operadores y facultades del administrador |
| `RF-I2-10`–`RF-I2-14` | Registro, edición, retiro y operación de vehículos según perfil |
| `RF-I2-15`–`RF-I2-22` | Creación, estado, retiro, compatibilidad y concurrencia de celdas |

Las decisiones técnicas derivadas —hash de contraseñas, inactivación lógica, identidad obtenida desde la sesión y exclusión de pagos— se mantienen en el PRD y en la arquitectura técnica.

### 11.4 Entregables académicos de la Actividad Evaluativa 2

| ID | Entregable requerido | Responsable principal | Revisión |
|---|---|---|---|
| D2-01 | Requisitos funcionales y no funcionales de usuarios internos y celdas | Camilo | Paul y Mafe |
| D2-02 | Diagramas de casos de uso de administrador, operador y celdas en StarUML | Paul | Camilo |
| D2-03 | Historias de usuario con criterios de aceptación | Camilo | Mafe |
| D2-04 | Mockups de login, operadores, vehículos y administración de celdas | Mafe | Camilo |
| D2-05 | Diagramas de secuencia de las iteraciones 1 y 2 en StarUML | Camilo | Paul |
| D2-06 | Diagrama de componentes actualizado para las iteraciones 1 y 2 | Paul | Camilo y Mafe |
| D2-07 | Plan de pruebas resumido de autenticación, permisos y celdas | Mafe | Camilo y Paul |
| D2-08 | PDF final: portada, introducción, entregables, conclusiones, URL de GitHub y URL del video | Mafe compila; los tres aportan evidencia | Los tres |
| D2-09 | Video en YouTube mostrando ambos perfiles y la gestión de celdas | Los tres; Mafe coordina el guion | Los tres |

El documento final debe usar la nomenclatura solicitada por la actividad: `Apellido_Nombre_EA2`.

### 11.5 Reparto del desarrollo en GitHub

| Persona | Responsabilidad principal | Superficies de código |
|---|---|---|
| **Paul** | Modelo persistente de cuentas, roles, credenciales, estados de celdas, auditoría y restricciones | `backend/app/models/`, `backend/app/db/`, `backend/scripts/`, pruebas de persistencia |
| **Camilo** | Autenticación, autorización, reglas por perfil, API de operadores/celdas/vehículos e integración con los flujos existentes | `backend/app/schemas/`, `backend/app/services/`, `backend/app/api/`, pruebas de servicios y API |
| **Mafe** | Login, navegación por perfil, administración visual de operadores y celdas, mensajes, formularios y pruebas del frontend | `frontend/src/app/`, especialmente páginas, guards, servicios, modelos y componentes compartidos |

#### Límites para evitar conflictos

- Paul define tablas, relaciones, índices y restricciones; Camilo consume ese modelo desde servicios y endpoints.
- Camilo define el contrato HTTP y los códigos de error con Paul antes de que Mafe conecte las pantallas.
- Mafe puede desarrollar primero con datos simulados, pero no implementa permisos únicamente en el frontend: la autoridad siempre queda en FastAPI.
- Solo una persona edita por PR los hotspots `docker-compose.yml`, `.env.example`, `README.md`, rutas Angular y registro principal de routers FastAPI.
- Ningún PR debe mezclar autenticación, celdas y documentación completa en un único cambio. Cada tarea debe poder revisarse y probarse por separado.

### 11.6 Backlog técnico de la Iteración 2

| ID | Responsable | Depende de | Entregable delimitado | Verificación mínima |
|---|---|---|---|---|
| T16 | Camilo + Paul | T15 | Alinear PRD, arquitectura, contrato de autenticación, roles, permisos, auditoría, rutas y errores | Matriz perfil–acción y documentos revisados por los tres |
| T17 | Paul | T16 | Modelo de cuentas internas: usuario único, hash, rol, estado y relación con operario | No admite usuario duplicado; nunca persiste contraseña en texto plano |
| T18 | Paul | T16 | Modelo administrable de celdas: código único, tipo, estado activo e historial | Celda referenciada no se borra; celda ocupada no se puede anular |
| T19 | Camilo | T17 | Login, validación de contraseña, sesión/token y obtención del usuario actual | Credenciales válidas ingresan; inválidas o anuladas se rechazan |
| T20 | Camilo | T17, T19 | API administrativa de operadores y guards por rol | Operador recibe `403` al intentar administrar usuarios |
| T21 | Camilo | T18, T19 | API administrativa de celdas y adaptación de asignación/corrección | Solo administrador modifica; celdas anuladas nunca se asignan |
| T22 | Camilo | T19 | Adaptar vehículos, entradas y salidas para permisos y auditoría | Ambos perfiles operan; solo administrador edita/elimina vehículos; queda responsable registrado |
| T23 | Mafe | T16 | Pantalla de login, sesión local, cierre de sesión y navegación por perfil con API simulada | Estados de carga, error y cuenta anulada visibles; build correcto |
| T24 | Mafe | T16 | Pantallas de operadores y celdas con datos simulados | Acciones administrativas visibles solo para administrador; filtros e indicadores comprensibles |
| T25 | Mafe + Camilo | T19–T24 | Integración completa del frontend con autenticación y APIs | Recargar conserva o invalida correctamente la sesión; errores `401/403` se muestran sin romper la aplicación |
| T26 | Camilo + Paul | T20–T22 | Pruebas de permisos, concurrencia, auditoría y regresión de Iteración 1 | Dos operadores trabajan simultáneamente; no comparten celda; flujos anteriores siguen funcionando |
| T27 | Mafe | T25, T26 | Evidencia manual y plan de pruebas resumido | Casos de administrador, operador, acceso denegado, cuenta anulada y celda inhabilitada |
| T28 | Compartido | T16, T25, T27 | Requisitos, historias, mockups, casos de uso, secuencias, componentes y PDF | Trazabilidad RF–HU–mockup–prueba completa |
| T29 | Compartido | T26–T28 | README, ejecución limpia, video y cierre de la entrega | Clon limpio, `docker compose up --build`, recorrido de ambos perfiles y enlaces accesibles |

### 11.7 Oleadas y orden de integración

| Oleada | Trabajo paralelo | Resultado |
|---|---|---|
| E — Contrato | T16 y borradores D2-01/D2-03/D2-04 | Permisos, rutas y pantallas acordados antes de programar |
| F — Base paralela | Paul: T17–T18; Mafe: T23–T24 con mocks | Persistencia y frontend avanzan sin editar los mismos archivos |
| G — Seguridad y reglas | Camilo: T19–T22 en PR separados | Backend autenticado y autorizado, integrado con Iteración 1 |
| H — Integración | Camilo + Mafe: T25; Camilo + Paul: T26 | Aplicación completa y regresión comprobada |
| I — Evidencia | T27–T29 y D2-01–D2-09 | Entrega académica, repositorio y video terminados |

### 11.8 Flujo concreto en GitHub

1. Crear los issues T16–T29 con alcance, responsable, dependencias y verificación mínima.
2. Sincronizar `camilo-backend` con `origin/main` mediante avance rápido y publicarla antes de iniciar T16.
3. Crear `docs/i2-t16-contract` desde `camilo-backend`, actualizar el contrato y abrir el primer PR hijo hacia `camilo-backend`.
4. Después de integrar T16, abrir el PR tracker `camilo-backend` → `main` como **draft/no merge**.
5. Cada tarea posterior usa una rama corta creada desde `origin/camilo-backend` y un PR cuyo destino es `camilo-backend`.
6. Integrar por oleadas:
   - E: T16.
   - F: T17/T18 y T23/T24 en paralelo cuando no compartan archivos.
   - G: T19, seguido de T20–T22 en PR separados.
   - H: T25 y luego T26.
   - I: T27, T28 y T29.
7. Si una tarea depende de otra, su PR permanece como **draft** hasta que la dependencia esté integrada en `camilo-backend`.
8. Cada PR hijo debe mostrar únicamente su trabajo, incluir pruebas y documentación aplicables y procurar no superar 400 líneas de cambios autorales.
9. Paul revisa los cambios de persistencia y transacciones; Camilo revisa reglas y contratos; Mafe valida el comportamiento visible.
10. No fusionar un PR hijo si fallan login, permisos, entrada/salida, asignación concurrente o regresiones de la Iteración 1.
11. Al terminar T29, ejecutar la verificación desde un clon limpio, completar video y enlaces, pasar el tracker a revisión y fusionar `camilo-backend` en `main` mediante **Create a merge commit**.
12. Después del merge final, conservar `main` como versión entregable y cerrar o eliminar las ramas cortas ya integradas.

No se debe iniciar la gestión de pagos en esta entrega. Esa funcionalidad pertenece a la Iteración 3.
