// Package postgres はユーザー集約の PostgreSQL 永続化実装。
package postgres

import (
	"context"
	"errors"
	"fmt"

	"github.com/google/uuid"
	"github.com/jackc/pgx/v5"
	"github.com/jackc/pgx/v5/pgxpool"

	userdomain "github.com/Sow-0429/ring_tryon/internal/user/domain"
)

// UserRepository は userdomain.Repository の PostgreSQL 実装。
type UserRepository struct {
	pool *pgxpool.Pool
}

func NewUserRepository(pool *pgxpool.Pool) *UserRepository {
	return &UserRepository{pool: pool}
}

func (r *UserRepository) Create(ctx context.Context, u userdomain.User) error {
	_, err := r.pool.Exec(
		ctx,
		`INSERT INTO users (id, user_name) VALUES ($1, $2)`,
		u.UserID, u.UserName,
	)
	if err != nil {
		return fmt.Errorf("create user: %w", err)
	}
	return nil
}

func (r *UserRepository) FindByID(
	ctx context.Context, id uuid.UUID,
) (userdomain.User, error) {
	row := r.pool.QueryRow(
		ctx,
		`SELECT u.id, u.user_name,
		        h.index_jp_size, h.middle_jp_size, h.ring_jp_size, h.pinky_jp_size
		 FROM users u
		 LEFT JOIN hands h ON h.user_id = u.id
		 WHERE u.id = $1`,
		id,
	)

	var (
		uid                       uuid.UUID
		name                      string
		index, middle, ring, pinky *int32
	)
	err := row.Scan(&uid, &name, &index, &middle, &ring, &pinky)
	if errors.Is(err, pgx.ErrNoRows) {
		return userdomain.User{}, userdomain.ErrNotFound
	}
	if err != nil {
		return userdomain.User{}, fmt.Errorf("find user: %w", err)
	}

	return userdomain.User{
		UserID:   uid,
		UserName: name,
		Hand: userdomain.Hand{
			Index:  deref(index),
			Middle: deref(middle),
			Ring:   deref(ring),
			Pinky:  deref(pinky),
		},
	}, nil
}

func (r *UserRepository) SaveHand(
	ctx context.Context, userID uuid.UUID, h userdomain.Hand,
) error {
	_, err := r.pool.Exec(
		ctx,
		`INSERT INTO hands
		   (user_id, index_jp_size, middle_jp_size, ring_jp_size, pinky_jp_size)
		 VALUES ($1, $2, $3, $4, $5)
		 ON CONFLICT (user_id) DO UPDATE SET
		   index_jp_size  = EXCLUDED.index_jp_size,
		   middle_jp_size = EXCLUDED.middle_jp_size,
		   ring_jp_size   = EXCLUDED.ring_jp_size,
		   pinky_jp_size  = EXCLUDED.pinky_jp_size,
		   updated_at     = now()`,
		userID, nullIfZero(h.Index), nullIfZero(h.Middle),
		nullIfZero(h.Ring), nullIfZero(h.Pinky),
	)
	if err != nil {
		return fmt.Errorf("save hand: %w", err)
	}
	return nil
}

// nullIfZero は未設定(0)の号数を SQL NULL に写像する(CHECK 1-25 を満たすため)。
func nullIfZero(v int) any {
	if v == 0 {
		return nil
	}
	return v
}

func deref(p *int32) int {
	if p == nil {
		return 0
	}
	return int(*p)
}
