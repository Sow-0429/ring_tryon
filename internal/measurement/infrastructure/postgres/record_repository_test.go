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
	measurementdomain "github.com/Sow-0429/ring_tryon/internal/measurement/domain"
)

// 統合テスト。TEST_DATABASE_URL(pgx5://...) が未設定ならスキップ。
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
	m2, _ := migrate.NewWithSourceInstance("iofs", src, dsn)
	if err := m2.Up(); err != nil && !errors.Is(err, migrate.ErrNoChange) {
		t.Fatalf("migrate up: %v", err)
	}

	pool, err := pgxpool.New(
		context.Background(), strings.Replace(dsn, "pgx5://", "postgres://", 1),
	)
	if err != nil {
		t.Fatalf("pool: %v", err)
	}
	t.Cleanup(pool.Close)
	return pool
}

func TestRecordRepository_Save(t *testing.T) {
	pool := setup(t)
	ctx := context.Background()

	// FK のためユーザーを 1 件用意。
	userID := uuid.New()
	if _, err := pool.Exec(
		ctx, `INSERT INTO users (id, user_name) VALUES ($1, $2)`, userID, "dave",
	); err != nil {
		t.Fatalf("seed user: %v", err)
	}

	conf := 0.83
	m := measurementdomain.Measurement{
		CalibrationMethod: "card_id1",
		PixelsPerMM:       10.0,
		Handedness:        "Right",
		HandConfidence:    0.95,
		FrameCount:        5,
		Confidence:        &conf,
		Fingers: map[string]measurementdomain.FingerMeasurement{
			"index":  {LengthMM: 70, BaseWidthMM: 16, PipWidthMM: 16, WidthMM: 16, CircumferenceMM: 50.5},
			"middle": {LengthMM: 80, BaseWidthMM: 17, PipWidthMM: 17, WidthMM: 17, CircumferenceMM: 53.5},
			"ring":   {LengthMM: 75, BaseWidthMM: 16, PipWidthMM: 17, WidthMM: 17, CircumferenceMM: 52.5},
			"pinky":  {LengthMM: 60, BaseWidthMM: 14, PipWidthMM: 14, WidthMM: 14, CircumferenceMM: 45.0},
		},
	}

	recordID, err := NewRecordRepository(pool).Save(ctx, userID, m)
	if err != nil {
		t.Fatalf("save: %v", err)
	}
	if recordID == uuid.Nil {
		t.Fatal("expected non-nil record id")
	}

	// レコードが user に紐づき、4 指分が保存されている。
	var (
		gotUser    uuid.UUID
		frameCount int
		gotConf    *float64
		actual     *int
	)
	if err := pool.QueryRow(ctx,
		`SELECT user_id, frame_count, confidence, actual_ring_size_jp
		 FROM measurement_records WHERE id = $1`, recordID,
	).Scan(&gotUser, &frameCount, &gotConf, &actual); err != nil {
		t.Fatalf("query record: %v", err)
	}
	if gotUser != userID {
		t.Errorf("user_id = %v, want %v", gotUser, userID)
	}
	if frameCount != 5 {
		t.Errorf("frame_count = %d, want 5", frameCount)
	}
	if gotConf == nil || *gotConf != 0.83 {
		t.Errorf("confidence = %v, want 0.83", gotConf)
	}
	if actual != nil {
		t.Errorf("actual_ring_size_jp should be NULL at measure time, got %v", *actual)
	}

	var fingerCount int
	if err := pool.QueryRow(ctx,
		`SELECT count(*) FROM finger_measurements WHERE measurement_record_id = $1`,
		recordID,
	).Scan(&fingerCount); err != nil {
		t.Fatalf("count fingers: %v", err)
	}
	if fingerCount != 4 {
		t.Errorf("finger rows = %d, want 4", fingerCount)
	}
}
