// Package postgres は認証情報の PostgreSQL 永続化。
package postgres

import (
	"context"
	"errors"
	"fmt"

	"github.com/google/uuid"
	"github.com/jackc/pgx/v5"
	"github.com/jackc/pgx/v5/pgconn"
	"github.com/jackc/pgx/v5/pgxpool"

	authapp "github.com/Sow-0429/ring_tryon/internal/auth/application"
	authdomain "github.com/Sow-0429/ring_tryon/internal/auth/domain"
)

const uniqueViolation = "23505"

type CredentialRepository struct {
	pool *pgxpool.Pool
}

func NewCredentialRepository(pool *pgxpool.Pool) *CredentialRepository {
	return &CredentialRepository{pool: pool}
}

func (r *CredentialRepository) Create(
	ctx context.Context, userName, passwordHash string,
) (uuid.UUID, error) {
	id := uuid.New()
	_, err := r.pool.Exec(
		ctx,
		`INSERT INTO users (id, user_name, password_hash) VALUES ($1, $2, $3)`,
		id, userName, passwordHash,
	)
	if err != nil {
		var pgErr *pgconn.PgError
		if errors.As(err, &pgErr) && pgErr.Code == uniqueViolation {
			return uuid.Nil, authdomain.ErrUserExists
		}
		return uuid.Nil, fmt.Errorf("create credential: %w", err)
	}
	return id, nil
}

func (r *CredentialRepository) FindByName(
	ctx context.Context, userName string,
) (authapp.Credentials, error) {
	var (
		id   uuid.UUID
		hash *string
	)
	err := r.pool.QueryRow(
		ctx,
		`SELECT id, password_hash FROM users WHERE user_name = $1`,
		userName,
	).Scan(&id, &hash)
	if errors.Is(err, pgx.ErrNoRows) {
		return authapp.Credentials{}, authdomain.ErrInvalidCredentials
	}
	if err != nil {
		return authapp.Credentials{}, fmt.Errorf("find credential: %w", err)
	}
	if hash == nil {
		// パスワード未設定(旧データ)はログイン不可。
		return authapp.Credentials{}, authdomain.ErrInvalidCredentials
	}
	return authapp.Credentials{UserID: id, PasswordHash: *hash}, nil
}
