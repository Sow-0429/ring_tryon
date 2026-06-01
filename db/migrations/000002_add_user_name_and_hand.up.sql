-- ユーザーに名前と「手(各指の号数)」を持たせる。
-- Go ドメインの User{UserID, UserName, Hand{Index/Middle/Ring/Pinky}} に対応。
-- 号数は計測後に当てはめるため計測前は NULL。hands は user に 1:1 で紐づく。

ALTER TABLE users ADD COLUMN user_name TEXT NOT NULL DEFAULT '';

CREATE TABLE hands (
    user_id        UUID PRIMARY KEY REFERENCES users (id) ON DELETE CASCADE,
    index_jp_size  INTEGER,
    middle_jp_size INTEGER,
    ring_jp_size   INTEGER,
    pinky_jp_size  INTEGER,
    updated_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT hands_index_size_range
        CHECK (index_jp_size IS NULL OR index_jp_size BETWEEN 1 AND 25),
    CONSTRAINT hands_middle_size_range
        CHECK (middle_jp_size IS NULL OR middle_jp_size BETWEEN 1 AND 25),
    CONSTRAINT hands_ring_size_range
        CHECK (ring_jp_size IS NULL OR ring_jp_size BETWEEN 1 AND 25),
    CONSTRAINT hands_pinky_size_range
        CHECK (pinky_jp_size IS NULL OR pinky_jp_size BETWEEN 1 AND 25)
);
