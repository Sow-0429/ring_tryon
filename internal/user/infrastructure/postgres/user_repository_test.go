package postgres

import (
	"context"
	"errors"
	"os"
	"strings"
	"testing"

	"github.com/golang-migrate/migrate/v4"
	_ "github.com/golang-migrate/migrate/v4/database/pgx/v5"
	"github.com/golang-migrate/migrate/v4/source/iofs"
	"github.com/google/uuid"
	"github.com/jackc/pgx/v5/pgxpool"

	"github.com/Sow-0429/ring_tryon/db"
	userdomain "github.com/Sow-0429/ring_tryon/internal/user/domain"
)

// 統合テスト。TEST_DATABASE_URL(pgx5://...) が未設定ならスキップする。
func setup(t *testing.T) *pgxpool.Pool {
	t.Helper()
	dsn := os.Getenv("TEST_DATABASE_URL")
	if dsn == "" {
		t.Skip("TEST_DATABASE_URL not set; skipping DB integration test")
	}

	src, err := iofs.New(db.MigrationsFS, "migrations")
	if err != nil {
		t.Fatalf("load migrations: %v", err)
	}
	m, err := migrate.NewWithSourceInstance("iofs", src, dsn)
	if err != nil {
		t.Fatalf("init migrate: %v", err)
	}
	if err := m.Drop(); err != nil {
		t.Fatalf("drop: %v", err)
	}
	// Drop 後はソースを開き直す必要がある。
	m2, err := migrate.NewWithSourceInstance("iofs", src, dsn)
	if err != nil {
		t.Fatalf("re-init migrate: %v", err)
	}
	if err := m2.Up(); err != nil && !errors.Is(err, migrate.ErrNoChange) {
		t.Fatalf("migrate up: %v", err)
	}

	pgxDSN := strings.Replace(dsn, "pgx5://", "postgres://", 1)
	pool, err := pgxpool.New(context.Background(), pgxDSN)
	if err != nil {
		t.Fatalf("pool: %v", err)
	}
	t.Cleanup(pool.Close)
	return pool
}

func TestUserRepository_CreateAndFind(t *testing.T) {
	pool := setup(t)
	repo := NewUserRepository(pool)
	ctx := context.Background()

	u := userdomain.NewUser("alice")
	if err := repo.Create(ctx, u); err != nil {
		t.Fatalf("create: %v", err)
	}

	got, err := repo.FindByID(ctx, u.UserID)
	if err != nil {
		t.Fatalf("find: %v", err)
	}
	if got.UserName != "alice" {
		t.Errorf("UserName = %q, want alice", got.UserName)
	}
	// 計測前なので手は全指0(NULL)。
	if got.Hand != (userdomain.Hand{}) {
		t.Errorf("Hand = %+v, want zero", got.Hand)
	}
}

func TestUserRepository_SaveHandUpsert(t *testing.T) {
	pool := setup(t)
	repo := NewUserRepository(pool)
	ctx := context.Background()

	u := userdomain.NewUser("bob")
	if err := repo.Create(ctx, u); err != nil {
		t.Fatalf("create: %v", err)
	}

	hand := userdomain.Hand{Index: 10, Middle: 13, Ring: 12, Pinky: 5}
	if err := repo.SaveHand(ctx, u.UserID, hand); err != nil {
		t.Fatalf("save hand: %v", err)
	}
	// upsert: もう一度別の値で保存しても成功する。
	hand2 := userdomain.Hand{Index: 11, Middle: 14, Ring: 13, Pinky: 6}
	if err := repo.SaveHand(ctx, u.UserID, hand2); err != nil {
		t.Fatalf("save hand again: %v", err)
	}

	got, err := repo.FindByID(ctx, u.UserID)
	if err != nil {
		t.Fatalf("find: %v", err)
	}
	if got.Hand != hand2 {
		t.Errorf("Hand = %+v, want %+v", got.Hand, hand2)
	}
}

func TestUserRepository_FindByID_NotFound(t *testing.T) {
	pool := setup(t)
	repo := NewUserRepository(pool)

	_, err := repo.FindByID(context.Background(), uuid.New())
	if !errors.Is(err, userdomain.ErrNotFound) {
		t.Errorf("err = %v, want ErrNotFound", err)
	}
}
