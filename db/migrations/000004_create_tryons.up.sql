-- 試着履歴: どのユーザーがどの指にどのリングを試着したか。
CREATE TABLE tryons (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id     UUID NOT NULL REFERENCES users (id) ON DELETE CASCADE,
    ring_id     TEXT NOT NULL,
    finger_name TEXT NOT NULL,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT tryons_finger_name_valid
        CHECK (finger_name IN ('index', 'middle', 'ring', 'pinky'))
);

CREATE INDEX idx_tryons_user_id ON tryons (user_id, created_at DESC);
