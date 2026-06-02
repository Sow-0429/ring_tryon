package application

import (
	"context"
	"errors"
	"testing"

	"github.com/google/uuid"

	billingapp "github.com/Sow-0429/ring_tryon/internal/billing/application"
	measurementdomain "github.com/Sow-0429/ring_tryon/internal/measurement/domain"
	userdomain "github.com/Sow-0429/ring_tryon/internal/user/domain"
)

// in-memory repository
type fakeRepo struct {
	users map[uuid.UUID]userdomain.User
	hands map[uuid.UUID]userdomain.Hand
}

func newFakeRepo() *fakeRepo {
	return &fakeRepo{
		users: map[uuid.UUID]userdomain.User{},
		hands: map[uuid.UUID]userdomain.Hand{},
	}
}

func (r *fakeRepo) Create(_ context.Context, u userdomain.User) error {
	r.users[u.UserID] = u
	return nil
}

func (r *fakeRepo) FindByID(
	_ context.Context, id uuid.UUID,
) (userdomain.User, error) {
	u, ok := r.users[id]
	if !ok {
		return userdomain.User{}, userdomain.ErrNotFound
	}
	u.Hand = r.hands[id]
	return u, nil
}

func (r *fakeRepo) SaveHand(
	_ context.Context, userID uuid.UUID, h userdomain.Hand,
) error {
	r.hands[userID] = h
	return nil
}

// fake measurer
type fakeMeasurer struct {
	result measurementdomain.Measurement
	err    error
}

func (m fakeMeasurer) Measure(
	_ context.Context, _ []byte, _ string, _ Calibration, _ string,
) (measurementdomain.Measurement, error) {
	return m.result, m.err
}

// fake record repository
type fakeRecordRepo struct {
	saved []measurementdomain.Measurement
}

func (r *fakeRecordRepo) Save(
	_ context.Context, _ uuid.UUID, m measurementdomain.Measurement,
) (uuid.UUID, error) {
	r.saved = append(r.saved, m)
	return uuid.New(), nil
}

func (r *fakeRecordRepo) SetActualRingSize(
	_ context.Context, _ uuid.UUID, _ string, _ int,
) error {
	return nil
}

func (r *fakeRecordRepo) ListLabeled(
	_ context.Context,
) ([]measurementdomain.LabeledMeasurement, error) {
	return nil, nil
}

func (r *fakeRecordRepo) ListLabeledFeatures(
	_ context.Context,
) ([]measurementdomain.LabeledFeatures, error) {
	return nil, nil
}

func measurementOf(index, middle, ring, pinky float64) measurementdomain.Measurement {
	return measurementdomain.Measurement{
		CalibrationMethod: "card_id1",
		PixelsPerMM:       10.0,
		Handedness:        "Right",
		HandConfidence:    0.95,
		FrameCount:        1,
		Fingers: map[string]measurementdomain.FingerMeasurement{
			"index":  {FingerName: "index", CircumferenceMM: index},
			"middle": {FingerName: "middle", CircumferenceMM: middle},
			"ring":   {FingerName: "ring", CircumferenceMM: ring},
			"pinky":  {FingerName: "pinky", CircumferenceMM: pinky},
		},
	}
}

func TestMeasurementService_MeasureHandFromImage(t *testing.T) {
	t.Run("計測→生計測の永続化→号数化→保存され、手がユーザーに紐づく", func(t *testing.T) {
		// Arrange
		repo := newFakeRepo()
		records := &fakeRecordRepo{}
		u := userdomain.NewUser("alice")
		_ = repo.Create(context.Background(), u)
		measurer := fakeMeasurer{result: measurementOf(50.5, 53.5, 52.5, 45.0)}
		svc := NewMeasurementService(measurer, repo, records, billingapp.NewStaticEntitlementPolicy())

		// Act
		got, err := svc.MeasureHandFromImage(
			context.Background(), u.UserID, []byte("img"), "hand.jpg", Calibration{UseCard: true},
		)

		// Assert
		if err != nil {
			t.Fatalf("unexpected error: %v", err)
		}
		want := userdomain.Hand{Index: 10, Middle: 13, Ring: 12, Pinky: 5}
		if got.User.Hand != want {
			t.Errorf("Hand = %+v, want %+v", got.User.Hand, want)
		}
		if repo.hands[u.UserID] != want {
			t.Errorf("saved hand = %+v, want %+v", repo.hands[u.UserID], want)
		}
		if got.RecordID == (uuid.UUID{}) {
			t.Error("expected non-nil record id")
		}
		if len(records.saved) != 1 {
			t.Errorf("expected 1 persisted measurement, got %d", len(records.saved))
		}
	})

	t.Run("存在しないユーザーはErrNotFound", func(t *testing.T) {
		repo := newFakeRepo()
		svc := NewMeasurementService(fakeMeasurer{}, repo, &fakeRecordRepo{}, billingapp.NewStaticEntitlementPolicy())

		_, err := svc.MeasureHandFromImage(
			context.Background(), uuid.New(), []byte("img"), "x.jpg", Calibration{},
		)
		if !errors.Is(err, userdomain.ErrNotFound) {
			t.Errorf("err = %v, want ErrNotFound", err)
		}
	})

	t.Run("計測エラーは伝播し、手も生計測も保存しない", func(t *testing.T) {
		repo := newFakeRepo()
		records := &fakeRecordRepo{}
		u := userdomain.NewUser("bob")
		_ = repo.Create(context.Background(), u)
		measurer := fakeMeasurer{err: errors.New("ai service down")}
		svc := NewMeasurementService(measurer, repo, records, billingapp.NewStaticEntitlementPolicy())

		_, err := svc.MeasureHandFromImage(
			context.Background(), u.UserID, []byte("img"), "x.jpg", Calibration{UseCoin: true},
		)
		if err == nil {
			t.Fatal("expected error")
		}
		if _, saved := repo.hands[u.UserID]; saved {
			t.Error("hand should not be saved on measure error")
		}
		if len(records.saved) != 0 {
			t.Error("measurement should not be persisted on measure error")
		}
	})
}
