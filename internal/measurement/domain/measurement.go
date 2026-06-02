// Package domain は計測結果(較正ループ用の生データ)のドメインモデル。
package domain

import (
	"context"
	"errors"

	"github.com/google/uuid"
)

var (
	// ErrNotFound は対象の計測レコードが存在しないことを表す。
	ErrNotFound = errors.New("measurement record not found")
	// ErrInvalidFinger は不正な指名。
	ErrInvalidFinger = errors.New("invalid finger name")
	// ErrInvalidRingSize は範囲外の号数。
	ErrInvalidRingSize = errors.New("invalid ring size")
)

// FingerNames は計測対象の指(号数計測の対象)。
var FingerNames = []string{"index", "middle", "ring", "pinky"}

// IsValidFinger は finger が計測対象の指名かを返す。
func IsValidFinger(finger string) bool {
	for _, name := range FingerNames {
		if name == finger {
			return true
		}
	}
	return false
}

// FingerMeasurement は 1 指分の計測。回帰特徴量(指長/付け根幅/関節幅/採用幅)と推定周囲長。
// 号数は持たない(ADR-0001: Python/計測側は周囲長まで)。
type FingerMeasurement struct {
	FingerName      string
	LengthMM        float64
	BaseWidthMM     float64
	PipWidthMM      float64
	WidthMM         float64
	CircumferenceMM float64
}

// Measurement は 1 回の計測結果(撮影メタ + 指別計測 + 任意の集約信頼度)。
type Measurement struct {
	CalibrationMethod string
	PixelsPerMM       float64
	Handedness        string
	HandConfidence    float64
	FrameCount        int
	// Confidence はマルチフレーム集約の総合信頼度。単発計測では nil。
	Confidence *float64
	Fingers    map[string]FingerMeasurement
}

// Repository は計測結果の永続化ポート。実装は infrastructure 層。
type Repository interface {
	// Save は計測結果をユーザーに紐づけて保存し、採番した record ID を返す。
	// 較正ラベル(actual_ring_size_jp)は計測時点では未設定(NULL)。
	Save(ctx context.Context, userID uuid.UUID, m Measurement) (uuid.UUID, error)

	// SetActualRingSize は計測レコードに正解号数(較正ラベル)と対象指を付与する。
	// 対象レコードが無ければ ErrNotFound。
	SetActualRingSize(
		ctx context.Context, recordID uuid.UUID, finger string, jpSize int,
	) error

	// ListLabeled は正解ラベル付きの計測(対象指の推定周囲長 + 正解号数)を返す。
	ListLabeled(ctx context.Context) ([]LabeledMeasurement, error)

	// ListLabeledFeatures は正解ラベル付きの計測から、対象指の回帰特徴量と正解号数を返す。
	ListLabeledFeatures(ctx context.Context) ([]LabeledFeatures, error)
}
