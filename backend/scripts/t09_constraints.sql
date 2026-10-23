-- T09: restricciones extra para salida y corrección.
-- Ejecutar en autos_colombia si el esquema ya se creó con T02.

ALTER TABLE parking_stays
    ADD CONSTRAINT ck_stay_exit_pair CHECK (
        (exited_at IS NULL AND exit_operator_id IS NULL)
        OR (exited_at IS NOT NULL AND exit_operator_id IS NOT NULL)
    );

ALTER TABLE parking_stays
    ADD CONSTRAINT ck_stay_exit_after_entry CHECK (
        exited_at IS NULL OR exited_at >= entered_at
    );

ALTER TABLE cell_corrections
    ADD CONSTRAINT ck_correction_different_spots CHECK (
        previous_spot_id <> new_spot_id
    );
