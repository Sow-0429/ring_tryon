package application

import (
	"context"
	"errors"
	"testing"

	"github.com/google/uuid"

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
	result userdomain.FingerCircumferences
	err    error
}

func (m fakeMeasurer) Measure(
	_ context.Context, _ []byte, _ string, _ Calibration,
) (userdomain.FingerCircumferences, error) {
	return m.result, m.err
}

func TestMeasurementService_MeasureHandFromImage(t *testing.T) {
	t.Run("計測→号数化→保存され、手がユーザーに紐づく", func(t *testing.T) {
		// Arrange
		repo := newFakeRepo()
		u := userdomain.NewUser("alice")
		_ = repo.Create(context.Background(), u)
		measurer := fakeMeasurer{result: userdomain.FingerCircumferences{
			Index: 50.5, Middle: 53.5, Ring: 52.5, Pinky: 45.0,
		}}
		svc := NewMeasurementService(measurer, repo)

		// Act
		got, err := svc.MeasureHandFromImage(
			context.Background(), u.UserID, []byte("img"), "hand.jpg", Calibration{UseCard: true},
		)

		// Assert
		if err != nil {
			t.Fatalf("unexpected error: %v", err)
		}
		want := userdomain.Hand{Index: 10, Middle: 13, Ring: 12, Pinky: 5}
		if got.Hand != want {
			t.Errorf("Hand = %+v, want %+v", got.Hand, want)
		}
		if repo.hands[u.UserID] != want {
			t.Errorf("saved hand = %+v, want %+v", repo.hands[u.UserID], want)
		}
	})

	t.Run("存在しないユーザーはErrNotFound", func(t *testing.T) {
		repo := newFakeRepo()
		svc := NewMeasurementService(fakeMeasurer{}, repo)

		_, err := svc.MeasureHandFromImage(
			context.Background(), uuid.New(), []byte("img"), "x.jpg", Calibration{},
		)
		if !errors.Is(err, userdomain.ErrNotFound) {
			t.Errorf("err = %v, want ErrNotFound", err)
		}
	})

	t.Run("計測エラーは伝播し、手は保存しない", func(t *testing.T) {
		repo := newFakeRepo()
		u := userdomain.NewUser("bob")
		_ = repo.Create(context.Background(), u)
		measurer := fakeMeasurer{err: errors.New("ai service down")}
		svc := NewMeasurementService(measurer, repo)

		_, err := svc.MeasureHandFromImage(
			context.Background(), u.UserID, []byte("img"), "x.jpg", Calibration{UseCoin: true},
		)
		if err == nil {
			t.Fatal("expected error")
		}
		if _, saved := repo.hands[u.UserID]; saved {
			t.Error("hand should not be saved on measure error")
		}
	})
}
