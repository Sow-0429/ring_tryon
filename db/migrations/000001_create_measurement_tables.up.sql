-- 指号数計測の永続化スキーマ (golang-migrate 形式)。
-- ユーザーIDは UUID。計測結果(Python ai_service が算出した周囲長と回帰特徴量)を
-- 較正ループ用に蓄積する。号数化(JP表)は Go ドメインが担うため号数列は持たない
-- (actual_ring_size_jp はユーザー入力の正解ラベルのみ保持) — ADR-0001。

CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TABLE users (
    id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE measurement_records (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id             UUID NOT NULL REFERENCES users (id) ON DELETE CASCADE,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
    calibration_method  TEXT NOT NULL,
    pixels_per_mm       DOUBLE PRECISION NOT NULL,
    handedness          TEXT NOT NULL,
    hand_confidence     DOUBLE PRECISION NOT NULL,
    frame_count         INTEGER NOT NULL DEFAULT 1,
    confidence          DOUBLE PRECISION,
    -- 較正ループの正解ラベル(ユーザーが申告した実号数)。号数→周囲長変換は Go。
    actual_ring_size_jp INTEGER,
    user_age            INTEGER,
    user_gender         TEXT,
    CONSTRAINT measurement_records_pixels_per_mm_positive
        CHECK (pixels_per_mm > 0),
    CONSTRAINT measurement_records_frame_count_positive
        CHECK (frame_count >= 1),
    CONSTRAINT measurement_records_actual_ring_size_range
        CHECK (actual_ring_size_jp IS NULL OR actual_ring_size_jp BETWEEN 1 AND 25)
);

CREATE INDEX idx_measurement_records_user_id
    ON measurement_records (user_id);

-- 較正ラベル付き(教師データ)の抽出を高速化する部分インデックス。
CREATE INDEX idx_measurement_records_labeled
    ON measurement_records (created_at)
    WHERE actual_ring_size_jp IS NOT NULL;

CREATE TABLE finger_measurements (
    id                    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    measurement_record_id UUID NOT NULL
        REFERENCES measurement_records (id) ON DELETE CASCADE,
    finger_name           TEXT NOT NULL,
    -- 回帰特徴量: 指長・付け根幅・PIP関節幅・採用幅。
    length_mm             DOUBLE PRECISION NOT NULL,
    base_width_mm         DOUBLE PRECISION NOT NULL,
    pip_width_mm          DOUBLE PRECISION NOT NULL,
    width_mm              DOUBLE PRECISION NOT NULL,
    -- 推定周囲長(mm)。号数化はしない(ADR-0001)。
    circumference_mm      DOUBLE PRECISION NOT NULL,
    CONSTRAINT finger_measurements_finger_name_valid
        CHECK (finger_name IN ('index', 'middle', 'ring', 'pinky')),
    CONSTRAINT finger_measurements_unique_finger_per_record
        UNIQUE (measurement_record_id, finger_name)
);

CREATE INDEX idx_finger_measurements_record_id
    ON finger_measurements (measurement_record_id);
