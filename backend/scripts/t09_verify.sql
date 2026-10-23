-- T09 — comprobación en pgAdmin sobre autos_colombia.
-- 1) Ejecuta t09_constraints.sql una vez (si aún no lo hiciste).
-- 2) Ejecuta cada bloque por separado (selección + F5).
-- Los bloques 2 y 3 hacen ROLLBACK: no alteran los datos de semilla.

-- ============================================================
-- Bloque 1. Estado inicial (debe existir INS001 abierto en A-01)
-- ============================================================
SELECT v.license_plate,
       s.code AS celda,
       r.code AS comprobante,
       r.used_at,
       ps.exited_at
FROM parking_stays ps
JOIN vehicles v ON v.id = ps.vehicle_id
JOIN parking_spots s ON s.id = ps.parking_spot_id
JOIN receipts r ON r.parking_stay_id = ps.id
WHERE v.license_plate = 'INS001';

SELECT COUNT(*) FILTER (WHERE category = 'MOTO') AS motos,
       COUNT(*) FILTER (WHERE category = 'AUTOMOVIL') AS automoviles,
       COUNT(*) AS total
FROM parking_spots;
-- Esperado: 1 fila INS001 / A-01 / AC-INS001-OPEN / used_at y exited_at nulos.
-- Esperado: 10 motos, 70 automóviles, 80 total.

-- ============================================================
-- Bloque 2. Corrección atómica A-01 -> A-02 (se deshace al final)
-- ============================================================
BEGIN;

UPDATE parking_stays ps
SET parking_spot_id = (SELECT id FROM parking_spots WHERE code = 'A-02')
FROM vehicles v
WHERE v.id = ps.vehicle_id
  AND v.license_plate = 'INS001'
  AND ps.exited_at IS NULL;

INSERT INTO cell_corrections (
    parking_stay_id, previous_spot_id, new_spot_id, operator_id
)
SELECT ps.id,
       (SELECT id FROM parking_spots WHERE code = 'A-01'),
       (SELECT id FROM parking_spots WHERE code = 'A-02'),
       (SELECT id FROM operators WHERE name = 'Operario Diurno 2')
FROM parking_stays ps
JOIN vehicles v ON v.id = ps.vehicle_id
WHERE v.license_plate = 'INS001'
  AND ps.exited_at IS NULL;

SELECT v.license_plate, s.code AS celda, c.previous_spot_id, c.new_spot_id, c.operator_id
FROM parking_stays ps
JOIN vehicles v ON v.id = ps.vehicle_id
JOIN parking_spots s ON s.id = ps.parking_spot_id
JOIN cell_corrections c ON c.parking_stay_id = ps.id
WHERE v.license_plate = 'INS001';
-- Esperado: celda A-02 y una fila de auditoría.

ROLLBACK;

-- ============================================================
-- Bloque 3. Salida atómica (se deshace al final)
-- ============================================================
BEGIN;

UPDATE parking_stays ps
SET exit_operator_id = (SELECT id FROM operators WHERE name = 'Operario Diurno 1'),
    exited_at = NOW()
FROM vehicles v
WHERE v.id = ps.vehicle_id
  AND v.license_plate = 'INS001'
  AND ps.exited_at IS NULL;

UPDATE receipts
SET used_at = NOW()
WHERE code = 'AC-INS001-OPEN';

SELECT v.license_plate, ps.exited_at, r.used_at, s.code AS celda
FROM parking_stays ps
JOIN vehicles v ON v.id = ps.vehicle_id
JOIN parking_spots s ON s.id = ps.parking_spot_id
JOIN receipts r ON r.parking_stay_id = ps.id
WHERE v.license_plate = 'INS001';
-- Esperado: exited_at y used_at con fecha. A-01 ya no tiene permanencia abierta.

SELECT s.code
FROM parking_spots s
JOIN parking_stays ps ON ps.parking_spot_id = s.id AND ps.exited_at IS NULL
WHERE s.code = 'A-01';
-- Esperado: 0 filas (celda libre).

ROLLBACK;

-- ============================================================
-- Bloque 4. Rechazos (ejecutar DE A UNO; deben fallar)
-- ============================================================

-- 4a. Salida incompleta: hora sin operario → ck_stay_exit_pair
-- UPDATE parking_stays SET exited_at = NOW()
-- WHERE exited_at IS NULL AND vehicle_id = (SELECT id FROM vehicles WHERE license_plate = 'INS001');

-- 4b. Corrección a la misma celda → ck_correction_different_spots
-- INSERT INTO cell_corrections (parking_stay_id, previous_spot_id, new_spot_id, operator_id)
-- SELECT ps.id, ps.parking_spot_id, ps.parking_spot_id, ps.entry_operator_id
-- FROM parking_stays ps
-- JOIN vehicles v ON v.id = ps.vehicle_id
-- WHERE v.license_plate = 'INS001' AND ps.exited_at IS NULL;

-- 4c. Dos permanencias abiertas en la misma celda → uq_open_stay_per_spot
-- INSERT INTO parking_stays (vehicle_id, parking_spot_id, entry_operator_id, entered_at)
-- SELECT v.id, s.id, o.id, NOW()
-- FROM vehicles v, parking_spots s, operators o
-- WHERE v.license_plate = 'ABC123' AND s.code = 'A-01' AND o.name = 'Operario Diurno 1';
