package domain

import (
	"math"
	"testing"
)

func TestEvaluate(t *testing.T) {
	t.Run("予測号数と正解号数を±1号で評価する", func(t *testing.T) {
		// 50.5mm→10号, 53.5mm→13号, 52.5mm→12号
		samples := []LabeledMeasurement{
			{PredictedCircumferenceMM: 50.5, ActualRingSizeJP: 10}, // 一致 (diff 0)
			{PredictedCircumferenceMM: 53.5, ActualRingSizeJP: 12}, // 13 vs 12 (diff 1) → 範囲内
			{PredictedCircumferenceMM: 52.5, ActualRingSizeJP: 9},  // 12 vs 9 (diff 3) → 範囲外
		}

		report := Evaluate(samples)

		if report.Total != 3 {
			t.Errorf("Total = %d, want 3", report.Total)
		}
		if report.WithinOneSize != 2 {
			t.Errorf("WithinOneSize = %d, want 2", report.WithinOneSize)
		}
		if math.Abs(report.WithinOneSizeRatio-2.0/3.0) > 1e-9 {
			t.Errorf("WithinOneSizeRatio = %f, want %f", report.WithinOneSizeRatio, 2.0/3.0)
		}
		// 平均絶対号数誤差 = (0+1+3)/3
		if math.Abs(report.MeanAbsSizeError-4.0/3.0) > 1e-9 {
			t.Errorf("MeanAbsSizeError = %f, want %f", report.MeanAbsSizeError, 4.0/3.0)
		}
	})

	t.Run("空なら全ゼロ", func(t *testing.T) {
		report := Evaluate(nil)
		if report != (CalibrationReport{}) {
			t.Errorf("expected zero report, got %+v", report)
		}
	})

	t.Run("不正な周囲長は除外する", func(t *testing.T) {
		samples := []LabeledMeasurement{
			{PredictedCircumferenceMM: 50.5, ActualRingSizeJP: 10},
			{PredictedCircumferenceMM: 0, ActualRingSizeJP: 10}, // 除外
		}
		report := Evaluate(samples)
		if report.Total != 1 {
			t.Errorf("Total = %d, want 1 (invalid excluded)", report.Total)
		}
	})
}
