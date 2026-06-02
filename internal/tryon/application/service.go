// Package application は試着のユースケース。
package application

import (
	"context"

	"github.com/google/uuid"

	tryondomain "github.com/Sow-0429/ring_tryon/internal/tryon/domain"
)

type Service struct {
	repo      tryondomain.Repository
	generator tryondomain.ImageGenerator
}

func NewService(
	repo tryondomain.Repository, generator tryondomain.ImageGenerator,
) *Service {
	return &Service{repo: repo, generator: generator}
}

// RecordTryOn は試着履歴を保存する。
func (s *Service) RecordTryOn(
	ctx context.Context, userID uuid.UUID, ringID, finger string,
) error {
	if !tryondomain.IsValidFinger(finger) {
		return tryondomain.ErrInvalidFinger
	}
	return s.repo.Save(ctx, tryondomain.TryOn{
		ID:         uuid.New(),
		UserID:     userID,
		RingID:     ringID,
		FingerName: finger,
	})
}

// GenerateImage は手画像にリングを合成/生成した PNG を返す。
func (s *Service) GenerateImage(
	ctx context.Context,
	image []byte,
	filename string,
	placement tryondomain.RingPlacement,
	appearance tryondomain.RingAppearance,
	mode string,
) ([]byte, error) {
	return s.generator.Generate(ctx, image, filename, placement, appearance, mode)
}
