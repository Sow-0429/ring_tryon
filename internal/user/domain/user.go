// Package domain はユーザーと、その手(各指の号数)のドメインモデルを表す。
package domain

import (
	"errors"
	"fmt"

	"github.com/google/uuid"

	ringsize "github.com/Sow-0429/ring_tryon/internal/ring_size/domain"
)

// ErrInvalidCircumference は号数化できない不正な周囲長を表す。
var ErrInvalidCircumference = errors.New("invalid finger circumference")

// Hand は片手の各指の号数(JPサイズ 1-25)を保持する。
// 計測前は各フィールド 0 (未設定)。
type Hand struct {
	Index  int
	Middle int
	Ring   int
	Pinky  int
}

// FingerCircumferences は計測で得た各指の周囲長(mm)。
// Python ai_service が算出し、号数化(JP表)は ring_size ドメインが担う(ADR-0001)。
type FingerCircumferences struct {
	Index  float64
	Middle float64
	Ring   float64
	Pinky  float64
}

// User は UserID(UUID)・UserName・Hand(各指の号数)を持つ。
type User struct {
	UserID   uuid.UUID
	UserName string
	Hand     Hand
}

// NewUser は UUID を採番して新規ユーザーを生成する。
func NewUser(userName string) User {
	return User{
		UserID:   uuid.New(),
		UserName: userName,
	}
}

// AssignHandFromCircumferences は各指の周囲長を号数化して Hand の各フィールドに当てはめる。
// いずれかの周囲長が不正なら Hand を変更せずエラーを返す。
func (u *User) AssignHandFromCircumferences(c FingerCircumferences) error {
	hand, err := newHand(c)
	if err != nil {
		return err
	}
	u.Hand = hand
	return nil
}

func newHand(c FingerCircumferences) (Hand, error) {
	index, err := jpSize(c.Index)
	if err != nil {
		return Hand{}, err
	}
	middle, err := jpSize(c.Middle)
	if err != nil {
		return Hand{}, err
	}
	ring, err := jpSize(c.Ring)
	if err != nil {
		return Hand{}, err
	}
	pinky, err := jpSize(c.Pinky)
	if err != nil {
		return Hand{}, err
	}
	return Hand{Index: index, Middle: middle, Ring: ring, Pinky: pinky}, nil
}

func jpSize(circumferenceMM float64) (int, error) {
	rs, err := ringsize.NewRingSize(circumferenceMM)
	if err != nil {
		return 0, fmt.Errorf("%w: %v", ErrInvalidCircumference, err)
	}
	return rs.JPSize(), nil
}
