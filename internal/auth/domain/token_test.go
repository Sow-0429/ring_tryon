package domain

import (
	"testing"
	"time"

	"github.com/google/uuid"
)

func TestTokenService_IssueVerify(t *testing.T) {
	svc := NewTokenService("secret-key")
	id := uuid.New()

	token, err := svc.Issue(id, time.Hour)
	if err != nil {
		t.Fatalf("issue: %v", err)
	}
	got, err := svc.Verify(token)
	if err != nil {
		t.Fatalf("verify: %v", err)
	}
	if got != id {
		t.Errorf("got %v, want %v", got, id)
	}
}

func TestTokenService_RejectsTampered(t *testing.T) {
	svc := NewTokenService("secret-key")
	token, _ := svc.Issue(uuid.New(), time.Hour)
	if _, err := svc.Verify(token + "x"); err == nil {
		t.Error("expected error for tampered token")
	}
	// 別シークレットでは検証失敗。
	if _, err := NewTokenService("other").Verify(token); err == nil {
		t.Error("expected error for wrong secret")
	}
}

func TestTokenService_RejectsExpired(t *testing.T) {
	svc := NewTokenService("secret-key")
	token, _ := svc.Issue(uuid.New(), -time.Second)
	if _, err := svc.Verify(token); err == nil {
		t.Error("expected error for expired token")
	}
}

func TestPasswordHashVerify(t *testing.T) {
	hash, err := HashPassword("pw123456")
	if err != nil {
		t.Fatalf("hash: %v", err)
	}
	if !VerifyPassword(hash, "pw123456") {
		t.Error("expected verify to succeed")
	}
	if VerifyPassword(hash, "wrong") {
		t.Error("expected verify to fail for wrong password")
	}
}
