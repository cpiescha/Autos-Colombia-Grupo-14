-- T18: celdas administrables sobre una base que ya tiene el esquema de la Iteración 1.
-- Impide borrar una celda con historial y anular una celda ocupada.

ALTER TABLE parking_spots
    ADD COLUMN IF NOT EXISTS active BOOLEAN NOT NULL DEFAULT TRUE;

ALTER TABLE parking_spots
    ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ NOT NULL DEFAULT NOW();

ALTER TABLE parking_spots
    ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW();

CREATE OR REPLACE FUNCTION set_updated_at()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS trg_parking_spots_updated_at ON parking_spots;
CREATE TRIGGER trg_parking_spots_updated_at
    BEFORE UPDATE ON parking_spots
    FOR EACH ROW
    EXECUTE FUNCTION set_updated_at();

CREATE OR REPLACE FUNCTION prevent_delete_spot_with_history()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM parking_stays WHERE parking_spot_id = OLD.id
    ) OR EXISTS (
        SELECT 1
        FROM cell_corrections
        WHERE previous_spot_id = OLD.id OR new_spot_id = OLD.id
    ) THEN
        RAISE EXCEPTION 'SPOT_HAS_HISTORY'
            USING ERRCODE = '23503',
                  HINT = 'Una celda con movimientos se inactiva; no se elimina.';
    END IF;
    RETURN OLD;
END;
$$;

DROP TRIGGER IF EXISTS trg_prevent_delete_spot_with_history ON parking_spots;
CREATE TRIGGER trg_prevent_delete_spot_with_history
    BEFORE DELETE ON parking_spots
    FOR EACH ROW
    EXECUTE FUNCTION prevent_delete_spot_with_history();

CREATE OR REPLACE FUNCTION prevent_deactivate_occupied_spot()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
    IF NEW.active = FALSE AND OLD.active = TRUE AND EXISTS (
        SELECT 1
        FROM parking_stays
        WHERE parking_spot_id = OLD.id
          AND exited_at IS NULL
    ) THEN
        RAISE EXCEPTION 'SPOT_OCCUPIED'
            USING ERRCODE = '23514',
                  HINT = 'No se puede anular una celda con una permanencia abierta.';
    END IF;
    RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS trg_prevent_deactivate_occupied_spot ON parking_spots;
CREATE TRIGGER trg_prevent_deactivate_occupied_spot
    BEFORE UPDATE OF active ON parking_spots
    FOR EACH ROW
    EXECUTE FUNCTION prevent_deactivate_occupied_spot();
