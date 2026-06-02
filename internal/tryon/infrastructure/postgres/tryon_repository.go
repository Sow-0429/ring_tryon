// Package postgres は試着履歴の PostgreSQL 永続化実装。
package postgres

import (
	"context"
	"fmt"

	"github.com/jackc/pgx/v5/pgxpool"

	tryondomain "github.com/Sow-0429/ring_tryon/internal/tryon/domain"
)

type TryOnRepository struct {
	pool *pgxpool.Pool
}

func NewTryOnRepository(pool *pgxpool.Pool) *TryOnRepository {
	return &TryOnRepository{pool: pool}
}

func (r *TryOnRepository) Save(ctx context.Context, t tryondomain.TryOn) error {
	_, err := r.pool.Exec(
		ctx,
		`INSERT INTO tryons (id, user_id, ring_id, finger_name)
		 VALUES ($1, $2, $3, $4)`,
		t.ID, t.UserID, t.RingID, t.FingerName,
	)
	if err != nil {
		return fmt.Errorf("save tryon: %w", err)
	}
	return nil
}
