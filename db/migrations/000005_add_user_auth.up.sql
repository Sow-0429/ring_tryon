-- 認証: ユーザー名を一意にし、パスワードハッシュ列を追加する。
-- 既存(パスワード無し)ユーザーは password_hash = NULL でログイン不可。
ALTER TABLE users
    ADD COLUMN password_hash TEXT,
    ADD CONSTRAINT users_user_name_unique UNIQUE (user_name);
