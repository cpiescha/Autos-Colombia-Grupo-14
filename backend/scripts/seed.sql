-- Datos iniciales Iteración 1 — Autos Colombia (T04)
-- Idempotente: se puede ejecutar varias veces sin duplicar.
-- Ejecutar contra autos_colombia, después de schema.sql.

INSERT INTO parking_spots (code, category)
SELECT format('M-%s', lpad(g::text, 2, '0')), 'MOTO'::spot_category
FROM generate_series(1, 10) AS g
ON CONFLICT (code) DO NOTHING;

INSERT INTO parking_spots (code, category)
SELECT format('A-%s', lpad(g::text, 2, '0')), 'AUTOMOVIL'::spot_category
FROM generate_series(1, 70) AS g
ON CONFLICT (code) DO NOTHING;

INSERT INTO operators (name)
SELECT name
FROM (VALUES ('Operario Diurno 1'), ('Operario Diurno 2')) AS seed(name)
WHERE NOT EXISTS (
    SELECT 1 FROM operators o WHERE o.name = seed.name
);

INSERT INTO clients (name)
SELECT name
FROM (
    VALUES
        ('Ana Pérez'),
        ('Luis Gómez'),
        ('Marta Díaz')
) AS seed(name)
WHERE NOT EXISTS (
    SELECT 1 FROM clients c WHERE c.name = seed.name
);

INSERT INTO vehicles (license_plate, type, brand, model, color, client_id)
SELECT seed.license_plate, seed.type, seed.brand, seed.model, seed.color, c.id
FROM (
    VALUES
        ('ABC123', 'CARRO'::vehicle_type, 'Chevrolet', 'Onix', 'Blanco', 'Ana Pérez'),
        ('CAR101', 'CARRO'::vehicle_type, 'Mazda', '3', 'Rojo', 'Luis Gómez'),
        ('CAR202', 'CARRO'::vehicle_type, 'Renault', 'Sandero', 'Gris', 'Marta Díaz'),
        ('CAR303', 'CARRO'::vehicle_type, 'Nissan', 'Versa', 'Negro', 'Ana Pérez'),
        ('XYZ99A', 'MOTO'::vehicle_type, 'Yamaha', 'FZ', 'Negro', 'Luis Gómez'),
        ('MOT101', 'MOTO'::vehicle_type, 'Honda', 'CB 125F', 'Rojo', 'Marta Díaz'),
        ('MOT202', 'MOTO'::vehicle_type, 'Suzuki', 'GN 125', 'Azul', 'Ana Pérez'),
        ('MOT303', 'MOTO'::vehicle_type, 'Bajaj', 'Pulsar', 'Negro', 'Luis Gómez'),
        ('DEF456', 'CAMIONETA'::vehicle_type, 'Toyota', 'Hilux', 'Gris', 'Marta Díaz'),
        ('VEN001', 'CARRO'::vehicle_type, 'Renault', 'Logan', 'Rojo', 'Ana Pérez'),
        ('INS001', 'CARRO'::vehicle_type, 'Kia', 'Rio', 'Azul', 'Luis Gómez')
) AS seed(license_plate, type, brand, model, color, client_name)
JOIN clients c ON c.name = seed.client_name
ON CONFLICT (license_plate) DO NOTHING;

-- Vigencias relativas para que los datos de demostración sigan siendo utilizables.
-- Una nueva vigencia solo se agrega cuando el vehículo no tiene otra vigente.
INSERT INTO memberships (vehicle_id, starts_at, expires_at)
SELECT v.id, CURRENT_TIMESTAMP - INTERVAL '30 days', CURRENT_TIMESTAMP + INTERVAL '365 days'
FROM vehicles v
WHERE v.license_plate IN (
    'ABC123', 'CAR101', 'CAR202', 'CAR303',
    'XYZ99A', 'MOT101', 'MOT202', 'MOT303',
    'DEF456', 'INS001'
)
AND NOT EXISTS (
    SELECT 1
    FROM memberships m
    WHERE m.vehicle_id = v.id
      AND m.starts_at <= CURRENT_TIMESTAMP
      AND m.expires_at >= CURRENT_TIMESTAMP
);

-- Caso negativo conservado para probar el rechazo por mensualidad vencida.
INSERT INTO memberships (vehicle_id, starts_at, expires_at)
SELECT v.id, CURRENT_TIMESTAMP - INTERVAL '90 days', CURRENT_TIMESTAMP - INTERVAL '1 day'
FROM vehicles v
WHERE v.license_plate = 'VEN001'
  AND NOT EXISTS (SELECT 1 FROM memberships m WHERE m.vehicle_id = v.id);

INSERT INTO parking_stays (
    vehicle_id,
    parking_spot_id,
    entry_operator_id,
    entered_at
)
SELECT v.id, s.id, o.id, CURRENT_TIMESTAMP - INTERVAL '2 hours'
FROM vehicles v
JOIN parking_spots s ON s.code = 'A-01'
JOIN operators o ON o.name = 'Operario Diurno 1'
WHERE v.license_plate = 'INS001'
  AND NOT EXISTS (
      SELECT 1 FROM parking_stays ps
      WHERE ps.vehicle_id = v.id
  )
  AND NOT EXISTS (
      SELECT 1 FROM parking_stays ps
      WHERE ps.parking_spot_id = s.id AND ps.exited_at IS NULL
  );

INSERT INTO receipts (code, parking_stay_id)
SELECT 'AC-INS001-OPEN', ps.id
FROM parking_stays ps
JOIN vehicles v ON v.id = ps.vehicle_id
WHERE v.license_plate = 'INS001'
  AND ps.exited_at IS NULL
  AND NOT EXISTS (
      SELECT 1 FROM receipts existing
      WHERE existing.parking_stay_id = ps.id
  )
ON CONFLICT (code) DO NOTHING;

-- Segunda permanencia abierta para probar salida de moto con comprobante.
INSERT INTO parking_stays (
    vehicle_id,
    parking_spot_id,
    entry_operator_id,
    entered_at
)
SELECT v.id, s.id, o.id, CURRENT_TIMESTAMP - INTERVAL '45 minutes'
FROM vehicles v
JOIN parking_spots s ON s.code = 'M-01'
JOIN operators o ON o.name = 'Operario Diurno 1'
WHERE v.license_plate = 'MOT303'
  AND NOT EXISTS (
      SELECT 1 FROM parking_stays ps
      WHERE ps.vehicle_id = v.id
  )
  AND NOT EXISTS (
      SELECT 1 FROM parking_stays ps
      WHERE ps.parking_spot_id = s.id AND ps.exited_at IS NULL
  );

INSERT INTO receipts (code, parking_stay_id)
SELECT 'AC-MOT303-OPEN', ps.id
FROM parking_stays ps
JOIN vehicles v ON v.id = ps.vehicle_id
WHERE v.license_plate = 'MOT303'
  AND ps.exited_at IS NULL
  AND NOT EXISTS (
      SELECT 1 FROM receipts existing
      WHERE existing.parking_stay_id = ps.id
  )
ON CONFLICT (code) DO NOTHING;
