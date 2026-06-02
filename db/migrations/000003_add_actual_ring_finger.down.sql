ALTER TABLE measurement_records
    DROP CONSTRAINT IF EXISTS measurement_records_actual_ring_finger_valid,
    DROP COLUMN IF EXISTS actual_ring_finger;
