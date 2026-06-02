ALTER TABLE users
    DROP CONSTRAINT IF EXISTS users_user_name_unique,
    DROP COLUMN IF EXISTS password_hash;
