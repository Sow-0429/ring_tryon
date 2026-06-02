package domain

import (
	"crypto/hmac"
	"crypto/sha256"
	"encoding/base64"
	"encoding/json"
	"strings"
	"time"

	"github.com/google/uuid"
)

// TokenService は HMAC-SHA256 署名の最小 JWT を発行・検証する(外部依存なし)。
type TokenService struct {
	secret []byte
}

func NewTokenService(secret string) *TokenService {
	return &TokenService{secret: []byte(secret)}
}

type jwtHeader struct {
	Alg string `json:"alg"`
	Typ string `json:"typ"`
}

type jwtClaims struct {
	Sub string `json:"sub"`
	Exp int64  `json:"exp"`
}

func b64(b []byte) string {
	return base64.RawURLEncoding.EncodeToString(b)
}

// Issue は userID を sub に持つトークンを ttl の有効期限で発行する。
func (s *TokenService) Issue(userID uuid.UUID, ttl time.Duration) (string, error) {
	h, _ := json.Marshal(jwtHeader{Alg: "HS256", Typ: "JWT"})
	c, _ := json.Marshal(jwtClaims{Sub: userID.String(), Exp: time.Now().Add(ttl).Unix()})
	signing := b64(h) + "." + b64(c)
	return signing + "." + b64(s.sign(signing)), nil
}

// Verify は署名と有効期限を検証し、userID を返す。
func (s *TokenService) Verify(token string) (uuid.UUID, error) {
	parts := strings.Split(token, ".")
	if len(parts) != 3 {
		return uuid.Nil, ErrInvalidToken
	}
	expected := b64(s.sign(parts[0] + "." + parts[1]))
	if !hmac.Equal([]byte(expected), []byte(parts[2])) {
		return uuid.Nil, ErrInvalidToken
	}
	raw, err := base64.RawURLEncoding.DecodeString(parts[1])
	if err != nil {
		return uuid.Nil, ErrInvalidToken
	}
	var c jwtClaims
	if err := json.Unmarshal(raw, &c); err != nil {
		return uuid.Nil, ErrInvalidToken
	}
	if time.Now().Unix() >= c.Exp {
		return uuid.Nil, ErrInvalidToken
	}
	id, err := uuid.Parse(c.Sub)
	if err != nil {
		return uuid.Nil, ErrInvalidToken
	}
	return id, nil
}

func (s *TokenService) sign(msg string) []byte {
	m := hmac.New(sha256.New, s.secret)
	m.Write([]byte(msg))
	return m.Sum(nil)
}
