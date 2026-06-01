// Package postgres は PostgreSQL 接続(pgxpool)を提供する。
package postgres

import (
	"context"
	"strings"

	"github.com/jackc/pgx/v5/pgxpool"
)

// NewPool は DSN から接続プールを生成する。
// migrate ツールと同じ DATABASE_URL を使えるよう、pgx5:// スキームは
// pgxpool が解釈できる postgres:// に正規化する。
func NewPool(ctx context.Context, dsn string) (*pgxpool.Pool, error) {
	pool, err := pgxpool.New(ctx, normalizeDSN(dsn))
	if err != nil {
		return nil, err
	}
	if err := pool.Ping(ctx); err != nil {
		pool.Close()
		return nil, err
	}
	return pool, nil
}

func normalizeDSN(dsn string) string {
	if strings.HasPrefix(dsn, "pgx5://") {
		return "postgres://" + strings.TrimPrefix(dsn, "pgx5://")
	}
	return dsn
}
