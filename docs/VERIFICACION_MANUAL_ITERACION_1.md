# Recorrido manual — Iteración 1

Este recorrido valida la entrega integrada sin sustituir las pruebas unitarias, de integración y concurrencia que el equipo realizará después.

## Preparación

```bash
cp .env.example .env
docker compose up --build -d
docker compose exec -T db psql -U autos_colombia -d autos_colombia < backend/scripts/seed.sql
```

Abrir <http://localhost:4200> y confirmar que <http://localhost:8080/api/health> responde correctamente.

## Recorrido guiado

| Paso | Datos | Resultado esperado | Estado |
|---|---|---|---|
| Consulta autorizada | `ABC123`, `CAR101`, `MOT101` o `MOT202` | Se muestran los datos y se habilita continuar | Pendiente de ejecución manual |
| Consulta vencida | `VEN001` | Se rechaza sin alterar la ocupación | Pendiente de ejecución manual |
| Entrada de carro | `CAR101` | FastAPI asigna una celda `A-*` y entrega comprobante | Pendiente de ejecución manual |
| Entrada de moto | `MOT101` | FastAPI asigna una celda `M-*` y entrega comprobante | Pendiente de ejecución manual |
| Salida de carro | `AC-INS001-OPEN` | Se previsualizan placa/celda y la confirmación libera la celda | Pendiente de ejecución manual |
| Salida de moto | `AC-MOT303-OPEN` | Se previsualizan placa/celda y la confirmación libera la celda | Pendiente de ejecución manual |
| Ocupación y reporte | Menú **Ocupación** y **Reportes** | Los totales provienen de FastAPI y el reporte incluye vehículos registrados | Pendiente de ejecución manual |
| Corrección | **Vehículos presentes → Corregir celda** | Se cambia a una celda compatible y queda trazabilidad | Pendiente de ejecución manual |

## Evidencia pendiente

- Capturas del recorrido manual de T14: pendientes de ejecución por el equipo.
- Pruebas unitarias e integración: diferidas por decisión del equipo.
- T13, dos ingresos simultáneos y última celda en PostgreSQL: diferida junto con las pruebas de integración; no se declara verificada.

Cuando se ejecute el recorrido, reemplazar cada estado por fecha, responsable y resultado observado, y adjuntar las capturas en `docs/evidencias/`.
