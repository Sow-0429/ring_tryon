// Package postgres は計測結果の PostgreSQL 永続化実装。
package postgres

import (
	"context"
	"fmt"

	"github.com/google/uuid"
	"github.com/jackc/pgx/v5/pgxpool"

	measurementdomain "github.com/Sow-0429/ring_tryon/internal/measurement/domain"
)

// RecordRepository は measurementdomain.Repository の PostgreSQL 実装。
type RecordRepository struct {
	pool *pgxpool.Pool
}

func NewRecordRepository(pool *pgxpool.Pool) *RecordRepository {
	return &RecordRepository{pool: pool}
}

// Save は measurement_records と finger_measurements を 1 トランザクションで挿入する。
func (r *RecordRepository) Save(
	ctx context.Context, userID uuid.UUID, m measurementdomain.Measurement,
) (uuid.UUID, error) {
	recordID := uuid.New()

	tx, err := r.pool.Begin(ctx)
	if err != nil {
		return uuid.Nil, fmt.Errorf("begin tx: %w", err)
	}
	defer tx.Rollback(ctx) // commit 後は no-op

	_, err = tx.Exec(
		ctx,
		`INSERT INTO measurement_records
		   (id, user_id, calibration_method, pixels_per_mm, handedness,
		    hand_confidence, frame_count, confidence)
		 VALUES ($1, $2, $3, $4, $5, $6, $7, $8)`,
		recordID, userID, m.CalibrationMethod, m.PixelsPerMM, m.Handedness,
		m.HandConfidence, m.FrameCount, m.Confidence,
	)
	if err != nil {
		return uuid.Nil, fmt.Errorf("insert measurement_record: %w", err)
	}

	for name, f := range m.Fingers {
		_, err = tx.Exec(
			ctx,
			`INSERT INTO finger_measurements
			   (measurement_record_id, finger_name, length_mm,
			    base_width_mm, pip_width_mm, width_mm, circumference_mm)
			 VALUES ($1, $2, $3, $4, $5, $6, $7)`,
			recordID, name, f.LengthMM, f.BaseWidthMM,
			f.PipWidthMM, f.WidthMM, f.CircumferenceMM,
		)
		if err != nil {
			return uuid.Nil, fmt.Errorf("insert finger_measurement %q: %w", name, err)
		}
	}

	if err := tx.Commit(ctx); err != nil {
		return uuid.Nil, fmt.Errorf("commit: %w", err)
	}
	return recordID, nil
}

// SetActualRingSize は正解号数と対象指を計測レコードに付与する。
func (r *RecordRepository) SetActualRingSize(
	ctx context.Context, recordID uuid.UUID, finger string, jpSize int,
) error {
	tag, err := r.pool.Exec(
		ctx,
		`UPDATE measurement_records
		 SET actual_ring_size_jp = $2, actual_ring_finger = $3
		 WHERE id = $1`,
		recordID, jpSize, finger,
	)
	if err != nil {
		return fmt.Errorf("set actual ring size: %w", err)
	}
	if tag.RowsAffected() == 0 {
		return measurementdomain.ErrNotFound
	}
	return nil
}

// ListLabeled は正解ラベル付きの計測(対象指の推定周囲長 + 正解号数)を返す。
func (r *RecordRepository) ListLabeled(
	ctx context.Context,
) ([]measurementdomain.LabeledMeasurement, error) {
	rows, err := r.pool.Query(
		ctx,
		`SELECT f.circumference_mm, r.actual_ring_size_jp
		 FROM measurement_records r
		 JOIN finger_measurements f
		   ON f.measurement_record_id = r.id
		  AND f.finger_name = r.actual_ring_finger
		 WHERE r.actual_ring_size_jp IS NOT NULL
		   AND r.actual_ring_finger IS NOT NULL`,
	)
	if err != nil {
		return nil, fmt.Errorf("list labeled: %w", err)
	}
	defer rows.Close()

	var samples []measurementdomain.LabeledMeasurement
	for rows.Next() {
		var s measurementdomain.LabeledMeasurement
		if err := rows.Scan(&s.PredictedCircumferenceMM, &s.ActualRingSizeJP); err != nil {
			return nil, fmt.Errorf("scan labeled: %w", err)
		}
		samples = append(samples, s)
	}
	return samples, rows.Err()
}

// ListLabeledFeatures は正解ラベル付きの計測から対象指の回帰特徴量と正解号数を返す。
func (r *RecordRepository) ListLabeledFeatures(
	ctx context.Context,
) ([]measurementdomain.LabeledFeatures, error) {
	rows, err := r.pool.Query(
		ctx,
		`SELECT r.actual_ring_finger, f.base_width_mm, f.pip_width_mm,
		        f.length_mm, r.actual_ring_size_jp
		 FROM measurement_records r
		 JOIN finger_measurements f
		   ON f.measurement_record_id = r.id
		  AND f.finger_name = r.actual_ring_finger
		 WHERE r.actual_ring_size_jp IS NOT NULL
		   AND r.actual_ring_finger IS NOT NULL`,
	)
	if err != nil {
		return nil, fmt.Errorf("list labeled features: %w", err)
	}
	defer rows.Close()

	var out []measurementdomain.LabeledFeatures
	for rows.Next() {
		var f measurementdomain.LabeledFeatures
		if err := rows.Scan(
			&f.FingerName, &f.BaseWidthMM, &f.PipWidthMM,
			&f.LengthMM, &f.ActualRingSizeJP,
		); err != nil {
			return nil, fmt.Errorf("scan labeled features: %w", err)
		}
		out = append(out, f)
	}
	return out, rows.Err()
}
