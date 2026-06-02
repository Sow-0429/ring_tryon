package application

import (
	"context"
	"errors"
	"testing"

	"github.com/google/uuid"

	authdomain "github.com/Sow-0429/ring_tryon/internal/auth/domain"
)

type fakeRepo struct {
	byName map[string]Credentials
}

func newFakeRepo() *fakeRepo { return &fakeRepo{byName: map[string]Credentials{}} }

func (r *fakeRepo) Create(_ context.Context, name, hash string) (uuid.UUID, error) {
	if _, ok := r.byName[name]; ok {
		return uuid.Nil, authdomain.ErrUserExists
	}
	id := uuid.New()
	r.byName[name] = Credentials{UserID: id, PasswordHash: hash}
	return id, nil
}

func (r *fakeRepo) FindByName(_ context.Context, name string) (Credentials, error) {
	c, ok := r.byName[name]
	if !ok {
		return Credentials{}, authdomain.ErrInvalidCredentials
	}
	return c, nil
}

func newSvc() *AuthService {
	return NewAuthService(newFakeRepo(), authdomain.NewTokenService("test-secret"))
}

func TestAuthService_SignupLogin(t *testing.T) {
	svc := newSvc()
	ctx := context.Background()

	res, err := svc.SignUp(ctx, "alice", "pw123456")
	if err != nil {
		t.Fatalf("signup: %v", err)
	}
	if res.Token == "" || res.UserName != "alice" {
		t.Errorf("unexpected signup result: %+v", res)
	}
	// 発行トークンが検証できる。
	if id, err := svc.Authenticate(res.Token); err != nil || id != res.UserID {
		t.Errorf("authenticate failed: id=%v err=%v", id, err)
	}

	// 同名は ErrUserExists。
	if _, err := svc.SignUp(ctx, "alice", "x"); !errors.Is(err, authdomain.ErrUserExists) {
		t.Errorf("want ErrUserExists, got %v", err)
	}

	// ログイン成功 / パスワード誤りで失敗。
	if _, err := svc.Login(ctx, "alice", "pw123456"); err != nil {
		t.Errorf("login: %v", err)
	}
	if _, err := svc.Login(ctx, "alice", "wrong"); !errors.Is(err, authdomain.ErrInvalidCredentials) {
		t.Errorf("want ErrInvalidCredentials, got %v", err)
	}
	if _, err := svc.Login(ctx, "nobody", "x"); !errors.Is(err, authdomain.ErrInvalidCredentials) {
		t.Errorf("want ErrInvalidCredentials for unknown user, got %v", err)
	}
}
