// Package application は計測・較正のユースケースを提供する。
package application

import (
	"context"

	"github.com/google/uuid"

	measurementdomain "github.com/Sow-0429/ring_tryon/internal/measurement/domain"
	ringsize "github.com/Sow-0429/ring_tryon/internal/ring_size/domain"
)

// CalibrationService は正解号数(ラベル)の付与と、蓄積データに対する精度評価を担う。
type CalibrationService struct {
	repo measurementdomain.Repository
}

func NewCalibrationService(repo measurementdomain.Repository) *CalibrationService {
	return &CalibrationService{repo: repo}
}

// SetActualRingSize は計測レコードに正解号数(対象指)を付与する(較正ラベル)。
func (s *CalibrationService) SetActualRingSize(
	ctx context.Context, recordID uuid.UUID, finger string, jpSize int,
) error {
	if !measurementdomain.IsValidFinger(finger) {
		return measurementdomain.ErrInvalidFinger
	}
	// 号数の妥当性は ring_size(真実の源)で検証する。
	if _, err := ringsize.CircumferenceForJPSize(jpSize); err != nil {
		return measurementdomain.ErrInvalidRingSize
	}
	return s.repo.SetActualRingSize(ctx, recordID, finger, jpSize)
}

// Evaluate は蓄積した正解ラベルに対する現行推定の精度(±1号@80%)を返す。
func (s *CalibrationService) Evaluate(
	ctx context.Context,
) (measurementdomain.CalibrationReport, error) {
	samples, err := s.repo.ListLabeled(ctx)
	if err != nil {
		return measurementdomain.CalibrationReport{}, err
	}
	return measurementdomain.Evaluate(samples), nil
}

// TrainingDataset は Python 回帰へ渡す学習行(特徴量 + 正解周囲長)を返す。
// 号数→周囲長変換は ring_size(真実の源)で行う。
func (s *CalibrationService) TrainingDataset(
	ctx context.Context,
) ([]measurementdomain.TrainingSample, error) {
	rows, err := s.repo.ListLabeledFeatures(ctx)
	if err != nil {
		return nil, err
	}

	samples := make([]measurementdomain.TrainingSample, 0, len(rows))
	for _, row := range rows {
		circ, err := ringsize.CircumferenceForJPSize(row.ActualRingSizeJP)
		if err != nil {
			// 範囲外ラベルはスキップ(DBのCHECKで通常起きない)。
			continue
		}
		samples = append(samples, measurementdomain.TrainingSample{
			FingerName:            row.FingerName,
			BaseWidthMM:           row.BaseWidthMM,
			PipWidthMM:            row.PipWidthMM,
			LengthMM:              row.LengthMM,
			ActualCircumferenceMM: circ,
		})
	}
	return samples, nil
}
