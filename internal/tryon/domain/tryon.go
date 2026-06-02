// Package domain は試着(リング試着履歴と画像生成)のドメインモデル。
package domain

import (
	"context"
	"errors"

	"github.com/google/uuid"
)

// ErrInvalidFinger は不正な指名。
var ErrInvalidFinger = errors.New("invalid finger name")

var fingerNames = map[string]struct{}{
	"index": {}, "middle": {}, "ring": {}, "pinky": {},
}

func IsValidFinger(finger string) bool {
	_, ok := fingerNames[finger]
	return ok
}

// TryOn は 1 回の試着履歴(どのリングをどの指に)。
type TryOn struct {
	ID         uuid.UUID
	UserID     uuid.UUID
	RingID     string
	FingerName string
}

// Repository は試着履歴の永続化ポート。
type Repository interface {
	Save(ctx context.Context, t TryOn) error
}

// RingPlacement は生成リクエストのリング配置(正規化座標)。
type RingPlacement struct {
	CenterX    float64
	CenterY    float64
	WidthRatio float64
	AngleDeg   float64
}

// RingAppearance はリングの見た目(色)。
type RingAppearance struct {
	Metal     string
	MetalDark string
	Gem       string
}

// ImageGenerator は手画像にリングを合成/生成する生成ポート(実装は ai_service プロキシ)。
// mode は "composite"(決定的合成) または "photoreal"(拡散)。
type ImageGenerator interface {
	Generate(
		ctx context.Context,
		image []byte,
		filename string,
		placement RingPlacement,
		appearance RingAppearance,
		mode string,
	) ([]byte, error)
}
