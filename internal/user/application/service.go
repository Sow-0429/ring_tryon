// Package application はユーザーに関するユースケースを提供する。
package application

import (
	"context"

	"github.com/google/uuid"

	userdomain "github.com/Sow-0429/ring_tryon/internal/user/domain"
)

// UserService はユーザー作成・取得・手の号数計測の適用を担う。
type UserService struct {
	repo userdomain.Repository
}

func NewUserService(repo userdomain.Repository) *UserService {
	return &UserService{repo: repo}
}

func (s *UserService) CreateUser(
	ctx context.Context, userName string,
) (userdomain.User, error) {
	u := userdomain.NewUser(userName)
	if err := s.repo.Create(ctx, u); err != nil {
		return userdomain.User{}, err
	}
	return u, nil
}

func (s *UserService) GetUser(
	ctx context.Context, id uuid.UUID,
) (userdomain.User, error) {
	return s.repo.FindByID(ctx, id)
}

// MeasureHand は各指の周囲長を号数化して手に当てはめ、永続化する。
func (s *UserService) MeasureHand(
	ctx context.Context, id uuid.UUID, c userdomain.FingerCircumferences,
) (userdomain.User, error) {
	u, err := s.repo.FindByID(ctx, id)
	if err != nil {
		return userdomain.User{}, err
	}
	if err := u.AssignHandFromCircumferences(c); err != nil {
		return userdomain.User{}, err
	}
	if err := s.repo.SaveHand(ctx, u.UserID, u.Hand); err != nil {
		return userdomain.User{}, err
	}
	return u, nil
}
