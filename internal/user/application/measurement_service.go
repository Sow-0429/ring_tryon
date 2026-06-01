package application

import (
	"context"

	"github.com/google/uuid"

	userdomain "github.com/Sow-0429/ring_tryon/internal/user/domain"
)

// Calibration は計測のスケール基準の指定。ちょうど 1 つを指定する。
type Calibration struct {
	MiddleFingerLengthMM *float64
	UseCoin              bool
	UseCard              bool
}

// HandMeasurer は画像から各指の周囲長を得る計測ポート。
// 実装(infrastructure/aiclient)は Python ai_service を呼ぶ。号数化はしない(ADR-0001)。
type HandMeasurer interface {
	Measure(
		ctx context.Context,
		image []byte,
		filename string,
		cal Calibration,
	) (userdomain.FingerCircumferences, error)
}

// MeasurementService は画像計測→号数化→永続化を束ねる。
type MeasurementService struct {
	measurer HandMeasurer
	repo     userdomain.Repository
}

func NewMeasurementService(
	measurer HandMeasurer, repo userdomain.Repository,
) *MeasurementService {
	return &MeasurementService{measurer: measurer, repo: repo}
}

// MeasureHandFromImage は画像から各指を計測し、号数化して当該ユーザーの手に保存する。
func (s *MeasurementService) MeasureHandFromImage(
	ctx context.Context,
	userID uuid.UUID,
	image []byte,
	filename string,
	cal Calibration,
) (userdomain.User, error) {
	u, err := s.repo.FindByID(ctx, userID)
	if err != nil {
		return userdomain.User{}, err
	}

	circumferences, err := s.measurer.Measure(ctx, image, filename, cal)
	if err != nil {
		return userdomain.User{}, err
	}

	if err := u.AssignHandFromCircumferences(circumferences); err != nil {
		return userdomain.User{}, err
	}
	if err := s.repo.SaveHand(ctx, u.UserID, u.Hand); err != nil {
		return userdomain.User{}, err
	}
	return u, nil
}
