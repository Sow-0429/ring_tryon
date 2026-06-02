package application

import (
	"context"
	"fmt"

	"github.com/google/uuid"

	billingapp "github.com/Sow-0429/ring_tryon/internal/billing/application"
	measurementdomain "github.com/Sow-0429/ring_tryon/internal/measurement/domain"
	userdomain "github.com/Sow-0429/ring_tryon/internal/user/domain"
)

// Calibration は計測のスケール基準の指定。ちょうど 1 つを指定する。
type Calibration struct {
	MiddleFingerLengthMM *float64
	UseCoin              bool
	UseCard              bool
}

// HandMeasurer は画像から計測結果(周囲長+特徴量+メタ)を得る計測ポート。
// 実装(infrastructure/aiclient)は Python ai_service を呼ぶ。号数化はしない(ADR-0001)。
// tier は品質ティア(standard/premium)で、ai_service の推定戦略選択に使う。
type HandMeasurer interface {
	Measure(
		ctx context.Context,
		image []byte,
		filename string,
		cal Calibration,
		tier string,
	) (measurementdomain.Measurement, error)
}

// MeasurementService は画像計測→生計測の永続化→号数化→手の保存を束ねる。
// ティア(課金)判定は EntitlementPolicy(アプリ層)に委譲する。
type MeasurementService struct {
	measurer     HandMeasurer
	users        userdomain.Repository
	records      measurementdomain.Repository
	entitlements billingapp.EntitlementPolicy
}

func NewMeasurementService(
	measurer HandMeasurer,
	users userdomain.Repository,
	records measurementdomain.Repository,
	entitlements billingapp.EntitlementPolicy,
) *MeasurementService {
	return &MeasurementService{
		measurer:     measurer,
		users:        users,
		records:      records,
		entitlements: entitlements,
	}
}

// MeasureResult は計測フローの結果。較正(正解号数の付与)で参照する record_id を含む。
type MeasureResult struct {
	User     userdomain.User
	RecordID uuid.UUID
}

// MeasureHandFromImage は画像から計測し、生計測を蓄積しつつ号数化して手に保存する。
func (s *MeasurementService) MeasureHandFromImage(
	ctx context.Context,
	userID uuid.UUID,
	image []byte,
	filename string,
	cal Calibration,
) (MeasureResult, error) {
	u, err := s.users.FindByID(ctx, userID)
	if err != nil {
		return MeasureResult{}, err
	}

	tier := s.entitlements.TierFor(ctx, userID)
	m, err := s.measurer.Measure(ctx, image, filename, cal, tier.String())
	if err != nil {
		return MeasureResult{}, err
	}

	circumferences, err := handCircumferences(m)
	if err != nil {
		return MeasureResult{}, err
	}
	if err := u.AssignHandFromCircumferences(circumferences); err != nil {
		return MeasureResult{}, err
	}

	// 較正ループ用に生計測を蓄積(actual_ring_size_jp は後段で付与)。
	recordID, err := s.records.Save(ctx, u.UserID, m)
	if err != nil {
		return MeasureResult{}, err
	}
	if err := s.users.SaveHand(ctx, u.UserID, u.Hand); err != nil {
		return MeasureResult{}, err
	}
	return MeasureResult{User: u, RecordID: recordID}, nil
}

func handCircumferences(
	m measurementdomain.Measurement,
) (userdomain.FingerCircumferences, error) {
	get := func(name string) (float64, error) {
		f, ok := m.Fingers[name]
		if !ok {
			return 0, fmt.Errorf("missing finger %q in measurement", name)
		}
		return f.CircumferenceMM, nil
	}
	index, err := get("index")
	if err != nil {
		return userdomain.FingerCircumferences{}, err
	}
	middle, err := get("middle")
	if err != nil {
		return userdomain.FingerCircumferences{}, err
	}
	ring, err := get("ring")
	if err != nil {
		return userdomain.FingerCircumferences{}, err
	}
	pinky, err := get("pinky")
	if err != nil {
		return userdomain.FingerCircumferences{}, err
	}
	return userdomain.FingerCircumferences{
		Index:  index,
		Middle: middle,
		Ring:   ring,
		Pinky:  pinky,
	}, nil
}
