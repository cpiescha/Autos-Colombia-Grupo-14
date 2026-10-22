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
        ('XYZ99A', 'MOTO'::vehicle_type, 'Yamaha', 'FZ', 'Negro', 'Luis Gómez'),
        ('DEF456', 'CAMIONETA'::vehicle_type, 'Toyota', 'Hilux', 'Gris', 'Marta Díaz'),
        ('VEN001', 'CARRO'::vehicle_type, 'Renault', 'Logan', 'Rojo', 'Ana Pérez'),
        ('INS001', 'CARRO'::vehicle_type, 'Kia', 'Rio', 'Azul', 'Luis Gómez')
) AS seed(license_plate, type, brand, model, color, client_name)
JOIN clients c ON c.name = seed.client_name
ON CONFLICT (license_plate) DO NOTHING;

INSERT INTO memberships (vehicle_id, starts_at, expires_at)
SELECT v.id, seed.starts_at, seed.expires_at
FROM (
    VALUES
        ('ABC123', TIMESTAMPTZ '2026-10-01 00:00:00-05', TIMESTAMPTZ '2026-11-21 23:59:59-05'),
        ('XYZ99A', TIMESTAMPTZ '2026-10-01 00:00:00-05', TIMESTAMPTZ '2026-11-21 23:59:59-05'),
        ('DEF456', TIMESTAMPTZ '2026-10-01 00:00:00-05', TIMESTAMPTZ '2026-11-21 23:59:59-05'),
        ('VEN001', TIMESTAMPTZ '2026-08-01 00:00:00-05', TIMESTAMPTZ '2026-09-30 23:59:59-05'),
        ('INS001', TIMESTAMPTZ '2026-10-01 00:00:00-05', TIMESTAMPTZ '2026-11-21 23:59:59-05')
) AS seed(license_plate, starts_at, expires_at)
JOIN vehicles v ON v.license_plate = seed.license_plate
WHERE NOT EXISTS (
    SELECT 1
    FROM memberships m
    WHERE m.vehicle_id = v.id
      AND m.starts_at = seed.starts_at
      AND m.expires_at = seed.expires_at
);

INSERT INTO parking_stays (
    vehicle_id,
    parking_spot_id,
    entry_operator_id,
    entered_at
)
SELECT v.id, s.id, o.id, TIMESTAMPTZ '2026-10-21 08:15:00-05'
FROM vehicles v
JOIN parking_spots s ON s.code = 'A-01'
JOIN operators o ON o.name = 'Operario Diurno 1'
WHERE v.license_plate = 'INS001'
  AND NOT EXISTS (
      SELECT 1 FROM parking_stays ps
      WHERE ps.vehicle_id = v.id AND ps.exited_at IS NULL
  );

INSERT INTO receipts (code, parking_stay_id)
SELECT 'AC-INS001-OPEN', ps.id
FROM parking_stays ps
JOIN vehicles v ON v.id = ps.vehicle_id
WHERE v.license_plate = 'INS001'
  AND ps.exited_at IS NULL
ON CONFLICT (code) DO NOTHING;
