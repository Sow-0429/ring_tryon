package application

import (
	"context"
	"errors"
	"testing"

	"github.com/google/uuid"

	tryondomain "github.com/Sow-0429/ring_tryon/internal/tryon/domain"
)

type fakeRepo struct{ saved []tryondomain.TryOn }

func (r *fakeRepo) Save(_ context.Context, t tryondomain.TryOn) error {
	r.saved = append(r.saved, t)
	return nil
}

type fakeGen struct {
	out []byte
	err error
}

func (g fakeGen) Generate(
	_ context.Context, _ []byte, _ string,
	_ tryondomain.RingPlacement, _ tryondomain.RingAppearance, _ string,
) ([]byte, error) {
	return g.out, g.err
}

func TestService_RecordTryOn(t *testing.T) {
	t.Run("有効な指は保存される", func(t *testing.T) {
		repo := &fakeRepo{}
		svc := NewService(repo, fakeGen{})
		if err := svc.RecordTryOn(context.Background(), uuid.New(), "gold-champagne", "ring"); err != nil {
			t.Fatalf("unexpected error: %v", err)
		}
		if len(repo.saved) != 1 || repo.saved[0].RingID != "gold-champagne" {
			t.Errorf("unexpected saved: %+v", repo.saved)
		}
	})

	t.Run("不正な指はErrInvalidFingerで保存しない", func(t *testing.T) {
		repo := &fakeRepo{}
		svc := NewService(repo, fakeGen{})
		err := svc.RecordTryOn(context.Background(), uuid.New(), "r1", "thumb")
		if !errors.Is(err, tryondomain.ErrInvalidFinger) {
			t.Errorf("err = %v, want ErrInvalidFinger", err)
		}
		if len(repo.saved) != 0 {
			t.Error("should not save on invalid finger")
		}
	})
}

func TestService_GenerateImage(t *testing.T) {
	svc := NewService(&fakeRepo{}, fakeGen{out: []byte("PNG")})
	got, err := svc.GenerateImage(
		context.Background(), []byte("img"), "h.jpg",
		tryondomain.RingPlacement{CenterX: 0.5, CenterY: 0.5, WidthRatio: 0.3},
		tryondomain.RingAppearance{Metal: "#b9975b"},
		"composite",
	)
	if err != nil || string(got) != "PNG" {
		t.Errorf("got %q err %v", string(got), err)
	}
}
