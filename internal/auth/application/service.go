// Package application は認証ユースケース(サインアップ/ログイン/トークン検証)。
package application

import (
	"context"
	"time"

	"github.com/google/uuid"

	authdomain "github.com/Sow-0429/ring_tryon/internal/auth/domain"
)

const tokenTTL = 24 * time.Hour

// Credentials は認証用のユーザー資格情報。
type Credentials struct {
	UserID       uuid.UUID
	PasswordHash string
}

// CredentialRepository は認証情報の永続化ポート。
type CredentialRepository interface {
	// Create は新規ユーザーを作成し ID を返す。同名は ErrUserExists。
	Create(ctx context.Context, userName, passwordHash string) (uuid.UUID, error)
	// FindByName は名前で資格情報を引く。無ければ ErrInvalidCredentials。
	FindByName(ctx context.Context, userName string) (Credentials, error)
}

// AuthResult はサインアップ/ログインの結果。
type AuthResult struct {
	UserID   uuid.UUID
	UserName string
	Token    string
}

type AuthService struct {
	repo   CredentialRepository
	tokens *authdomain.TokenService
}

func NewAuthService(repo CredentialRepository, tokens *authdomain.TokenService) *AuthService {
	return &AuthService{repo: repo, tokens: tokens}
}

func (s *AuthService) SignUp(
	ctx context.Context, userName, password string,
) (AuthResult, error) {
	hash, err := authdomain.HashPassword(password)
	if err != nil {
		return AuthResult{}, err
	}
	id, err := s.repo.Create(ctx, userName, hash)
	if err != nil {
		return AuthResult{}, err
	}
	return s.issue(id, userName)
}

func (s *AuthService) Login(
	ctx context.Context, userName, password string,
) (AuthResult, error) {
	cred, err := s.repo.FindByName(ctx, userName)
	if err != nil {
		return AuthResult{}, err
	}
	if !authdomain.VerifyPassword(cred.PasswordHash, password) {
		return AuthResult{}, authdomain.ErrInvalidCredentials
	}
	return s.issue(cred.UserID, userName)
}

// Authenticate はトークンを検証し userID を返す。
func (s *AuthService) Authenticate(token string) (uuid.UUID, error) {
	return s.tokens.Verify(token)
}

func (s *AuthService) issue(id uuid.UUID, userName string) (AuthResult, error) {
	token, err := s.tokens.Issue(id, tokenTTL)
	if err != nil {
		return AuthResult{}, err
	}
	return AuthResult{UserID: id, UserName: userName, Token: token}, nil
}
