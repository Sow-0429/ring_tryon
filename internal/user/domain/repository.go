package domain

import (
	"context"
	"errors"

	"github.com/google/uuid"
)

// ErrNotFound はユーザーが存在しないことを表す。
var ErrNotFound = errors.New("user not found")

// Repository はユーザー集約の永続化ポート。実装は infrastructure 層に置く。
type Repository interface {
	Create(ctx context.Context, u User) error
	FindByID(ctx context.Context, id uuid.UUID) (User, error)
	// SaveHand はユーザーの手(各指の号数)を保存(upsert)する。
	SaveHand(ctx context.Context, userID uuid.UUID, h Hand) error
}
