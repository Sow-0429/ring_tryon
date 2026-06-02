-- 較正ループ: 正解号数(actual_ring_size_jp)が「どの指」のものかを保持する。
-- これにより [付け根幅, 関節幅, 指長, 指種別] → 実周囲長 の教師データを抽出できる。

ALTER TABLE measurement_records
    ADD COLUMN actual_ring_finger TEXT,
    ADD CONSTRAINT measurement_records_actual_ring_finger_valid
        CHECK (
            actual_ring_finger IS NULL
            OR actual_ring_finger IN ('index', 'middle', 'ring', 'pinky')
        );
