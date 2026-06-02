// Package domain は認証(パスワード検証とトークン発行)のドメイン。
package domain

import (
	"errors"

	"golang.org/x/crypto/bcrypt"
)

var (
	// ErrInvalidCredentials は名前/パスワード不一致。
	ErrInvalidCredentials = errors.New("invalid credentials")
	// ErrUserExists は同名ユーザーが既に存在する。
	ErrUserExists = errors.New("user already exists")
	// ErrInvalidToken はトークンが不正/期限切れ。
	ErrInvalidToken = errors.New("invalid token")
)

// HashPassword は bcrypt でパスワードをハッシュ化する。
func HashPassword(password string) (string, error) {
	h, err := bcrypt.GenerateFromPassword([]byte(password), bcrypt.DefaultCost)
	if err != nil {
		return "", err
	}
	return string(h), nil
}

// VerifyPassword はハッシュとパスワードが一致するか検証する。
func VerifyPassword(hash, password string) bool {
	return bcrypt.CompareHashAndPassword([]byte(hash), []byte(password)) == nil
}
