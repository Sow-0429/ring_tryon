package application

import (
	"context"
	"testing"

	"github.com/google/uuid"

	measurementdomain "github.com/Sow-0429/ring_tryon/internal/measurement/domain"
)

// CalibrationService が使う Repository の最小フェイク。
type fakeRepo struct {
	labeledFeatures []measurementdomain.LabeledFeatures
	setCalls        int
}

func (r *fakeRepo) Save(
	_ context.Context, _ uuid.UUID, _ measurementdomain.Measurement,
) (uuid.UUID, error) {
	return uuid.New(), nil
}

func (r *fakeRepo) SetActualRingSize(
	_ context.Context, _ uuid.UUID, _ string, _ int,
) error {
	r.setCalls++
	return nil
}

func (r *fakeRepo) ListLabeled(
	_ context.Context,
) ([]measurementdomain.LabeledMeasurement, error) {
	return nil, nil
}

func (r *fakeRepo) ListLabeledFeatures(
	_ context.Context,
) ([]measurementdomain.LabeledFeatures, error) {
	return r.labeledFeatures, nil
}

func TestCalibrationService_TrainingDataset(t *testing.T) {
	t.Run("号数を周囲長ラベルに変換して学習行を返す", func(t *testing.T) {
		repo := &fakeRepo{labeledFeatures: []measurementdomain.LabeledFeatures{
			{FingerName: "ring", BaseWidthMM: 16, PipWidthMM: 17, LengthMM: 70, ActualRingSizeJP: 12},
		}}
		svc := NewCalibrationService(repo)

		samples, err := svc.TrainingDataset(context.Background())
		if err != nil {
			t.Fatalf("unexpected error: %v", err)
		}
		if len(samples) != 1 {
			t.Fatalf("len = %d, want 1", len(samples))
		}
		s := samples[0]
		// 12号 = 52.5mm (ring_size 表)
		if s.ActualCircumferenceMM != 52.5 {
			t.Errorf("ActualCircumferenceMM = %f, want 52.5", s.ActualCircumferenceMM)
		}
		if s.FingerName != "ring" || s.BaseWidthMM != 16 {
			t.Errorf("unexpected sample: %+v", s)
		}
	})
}

func TestCalibrationService_SetActualRingSize_Validation(t *testing.T) {
	repo := &fakeRepo{}
	svc := NewCalibrationService(repo)

	if err := svc.SetActualRingSize(context.Background(), uuid.New(), "thumb", 12); err == nil {
		t.Error("expected error for invalid finger")
	}
	if err := svc.SetActualRingSize(context.Background(), uuid.New(), "ring", 99); err == nil {
		t.Error("expected error for invalid ring size")
	}
	if repo.setCalls != 0 {
		t.Errorf("repo.SetActualRingSize should not be called on validation failure, got %d", repo.setCalls)
	}
}
