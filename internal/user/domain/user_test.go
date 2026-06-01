package domain

import (
	"testing"

	"github.com/google/uuid"
)

func TestNewUser(t *testing.T) {
	t.Run("UUIDのUserIDと名前を持つユーザーを生成する", func(t *testing.T) {
		// Act
		u := NewUser("alice")

		// Assert
		if u.UserID == uuid.Nil {
			t.Error("UserID should be a generated UUID, got Nil")
		}
		if u.UserName != "alice" {
			t.Errorf("UserName = %q, want %q", u.UserName, "alice")
		}
		// 計測前の手は全指未設定(0)
		if u.Hand != (Hand{}) {
			t.Errorf("Hand should be zero before measurement, got %+v", u.Hand)
		}
	})
}

func TestUser_AssignHandFromCircumferences(t *testing.T) {
	t.Run("各指の周囲長から号数を当てはめる", func(t *testing.T) {
		// Arrange
		u := NewUser("bob")
		c := FingerCircumferences{
			Index:  50.5, // 10号
			Middle: 53.5, // 13号
			Ring:   52.5, // 12号
			Pinky:  45.0, // 5号
		}

		// Act
		if err := u.AssignHandFromCircumferences(c); err != nil {
			t.Fatalf("unexpected error: %v", err)
		}

		// Assert
		want := Hand{Index: 10, Middle: 13, Ring: 12, Pinky: 5}
		if u.Hand != want {
			t.Errorf("Hand = %+v, want %+v", u.Hand, want)
		}
	})

	t.Run("不正な周囲長はエラーで、手は変更しない", func(t *testing.T) {
		// Arrange
		u := NewUser("carol")
		c := FingerCircumferences{Index: 50.5, Middle: 0, Ring: 52.5, Pinky: 45.0}

		// Act
		err := u.AssignHandFromCircumferences(c)

		// Assert
		if err == nil {
			t.Fatal("expected error for non-positive circumference")
		}
		if u.Hand != (Hand{}) {
			t.Errorf("Hand should be unchanged on error, got %+v", u.Hand)
		}
	})
}
