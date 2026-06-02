package domain

import (
	ringsize "github.com/Sow-0429/ring_tryon/internal/ring_size/domain"
)

// LabeledMeasurement は較正の 1 件: 計測で推定した周囲長と、ユーザー申告の正解号数。
type LabeledMeasurement struct {
	PredictedCircumferenceMM float64
	ActualRingSizeJP         int
}

// LabeledFeatures は正解ラベル付きの計測から取り出した回帰特徴量と正解号数。
type LabeledFeatures struct {
	FingerName       string
	BaseWidthMM      float64
	PipWidthMM       float64
	LengthMM         float64
	ActualRingSizeJP int
}

// TrainingSample は Python 回帰へ渡す学習行(特徴量 + 正解周囲長ラベル)。
// 号数→周囲長変換は ring_size(真実の源)で済ませてから渡す(ADR-0001/0007)。
type TrainingSample struct {
	FingerName            string  `json:"finger_name"`
	BaseWidthMM           float64 `json:"base_width_mm"`
	PipWidthMM            float64 `json:"pip_width_mm"`
	LengthMM              float64 `json:"length_mm"`
	ActualCircumferenceMM float64 `json:"actual_circumference_mm"`
}

// CalibrationReport は蓄積した正解ラベルに対する現行推定の精度。
// 受け入れ基準は ±1号@80% (WithinOneSizeRatio >= 0.8)。
type CalibrationReport struct {
	Total              int     `json:"total"`
	WithinOneSize      int     `json:"within_one_size"`
	WithinOneSizeRatio float64 `json:"within_one_size_ratio"`
	MeanAbsSizeError   float64 `json:"mean_abs_size_error"`
}

// Evaluate は予測号数(推定周囲長→JP号数)と正解号数を号数空間で比較し精度を出す。
// 号数化は ring_size が唯一の真実の源(ADR-0001)。不正な周囲長のサンプルは除外する。
func Evaluate(samples []LabeledMeasurement) CalibrationReport {
	total := 0
	hits := 0
	sumAbs := 0

	for _, s := range samples {
		rs, err := ringsize.NewRingSize(s.PredictedCircumferenceMM)
		if err != nil {
			continue
		}
		total++
		diff := abs(rs.JPSize() - s.ActualRingSizeJP)
		if diff <= 1 {
			hits++
		}
		sumAbs += diff
	}

	if total == 0 {
		return CalibrationReport{}
	}
	return CalibrationReport{
		Total:              total,
		WithinOneSize:      hits,
		WithinOneSizeRatio: float64(hits) / float64(total),
		MeanAbsSizeError:   float64(sumAbs) / float64(total),
	}
}

func abs(x int) int {
	if x < 0 {
		return -x
	}
	return x
}
