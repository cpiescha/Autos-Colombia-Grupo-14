# T26 verificado en PostgreSQL

T26 quedó automatizado con tres pruebas opt-in que levantan un proyecto Docker Compose aislado, ejecutan concurrencia real contra PostgreSQL 16 y verifican el desmontaje de contenedores y volumen al finalizar.

## Ejecutar

Desde `backend/`:

```bash
RUN_T26_DOCKER=1 .venv/Scripts/python.exe -m pytest -q tests/test_t26_runtime.py
```

En PowerShell:

```powershell
$env:RUN_T26_DOCKER = "1"
.venv\Scripts\python.exe -m pytest -q tests/test_t26_runtime.py
```

Sin `RUN_T26_DOCKER=1`, estas pruebas se omiten y la suite rápida no exige Docker.

## Resultado observado

| Escenario | Resultado |
|---|---|
| Dos operadores simultáneos | Dos transacciones PostgreSQL solapadas producen respuestas `201`, celdas y comprobantes diferentes, con asociación exacta entre placa, respuesta y operador |
| Última celda compatible | El rechazo termina mientras la transacción ganadora conserva el bloqueo: una `201`, una `409 NO_COMPATIBLE_SPACE`, un único movimiento y comprobante |
| Permisos y auditoría | Operador administrativo recibe `403` y el fingerprint completo de la base permanece igual; alta de vehículo conserva la cuenta responsable |
| Sesión anulada | Un token ya emitido recibe `401 INVALID_SESSION` después de anular la cuenta; el fingerprint completo permanece igual durante el rechazo |
| Regresión Iteración 1 | Entrada, corrección, reporte, vista previa, salida y consulta histórica validan responsables, comprobante y correcciones persistidas |

Última ejecución registrada antes de ampliar la consulta histórica: **3 pruebas aprobadas en 38.24 segundos**. La versión actual de T26 agrega la verificación de `GET /api/movimientos/historial`; debe reejecutarse con Docker antes de adjuntar la evidencia final.

## Integridad comprobada

- No hay dos permanencias abiertas para una misma celda.
- El rechazo concurrente no crea permanencia ni comprobante parcial.
- Entrada, corrección y salida conservan sus respectivos operarios.
- El comprobante queda usado y la permanencia cerrada después de la salida.
- La permanencia cerrada y su corrección se recuperan desde la API histórica después de completar el flujo.
- Cada ejecución usa un nombre de proyecto Compose y puertos disponibles únicos, por lo que no elimina el entorno de otra ejecución T26.
- Las credenciales PostgreSQL del escenario se fijan explícitamente y no dependen del entorno del desarrollador.
- El `finally` intenta el desmontaje aun cuando falla el arranque, y cualquier fallo de cleanup se informa.
