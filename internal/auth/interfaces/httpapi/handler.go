// Package httpapi は認証APIのHTTPハンドラとミドルウェア。
package httpapi

import (
	"context"
	"encoding/json"
	"errors"
	"net/http"
	"strings"

	"github.com/google/uuid"

	"github.com/Sow-0429/ring_tryon/internal/auth/application"
	authdomain "github.com/Sow-0429/ring_tryon/internal/auth/domain"
)

type ctxKey string

const userIDKey ctxKey = "userID"

func RegisterRoutes(mux *http.ServeMux, svc *application.AuthService) {
	h := &handler{svc: svc}
	mux.HandleFunc("POST /api/auth/signup", h.signup)
	mux.HandleFunc("POST /api/auth/login", h.login)
	mux.Handle("GET /api/me", h.Middleware(http.HandlerFunc(h.me)))
}

type handler struct {
	svc *application.AuthService
}

type credsReq struct {
	UserName string `json:"user_name"`
	Password string `json:"password"`
}

func (h *handler) signup(w http.ResponseWriter, r *http.Request) {
	req, ok := decode(w, r)
	if !ok {
		return
	}
	res, err := h.svc.SignUp(r.Context(), req.UserName, req.Password)
	if errors.Is(err, authdomain.ErrUserExists) {
		writeError(w, http.StatusConflict, "user already exists")
		return
	}
	if err != nil {
		writeError(w, http.StatusInternalServerError, "signup failed")
		return
	}
	writeJSON(w, http.StatusCreated, map[string]string{
		"token": res.Token, "user_id": res.UserID.String(), "user_name": res.UserName,
	})
}

func (h *handler) login(w http.ResponseWriter, r *http.Request) {
	req, ok := decode(w, r)
	if !ok {
		return
	}
	res, err := h.svc.Login(r.Context(), req.UserName, req.Password)
	if errors.Is(err, authdomain.ErrInvalidCredentials) {
		writeError(w, http.StatusUnauthorized, "invalid user name or password")
		return
	}
	if err != nil {
		writeError(w, http.StatusInternalServerError, "login failed")
		return
	}
	writeJSON(w, http.StatusOK, map[string]string{
		"token": res.Token, "user_id": res.UserID.String(), "user_name": res.UserName,
	})
}

func (h *handler) me(w http.ResponseWriter, r *http.Request) {
	id := UserIDFrom(r.Context())
	writeJSON(w, http.StatusOK, map[string]string{"user_id": id.String()})
}

// Middleware は Authorization: Bearer <token> を検証し userID をコンテキストに入れる。
func (h *handler) Middleware(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		token := bearer(r)
		if token == "" {
			writeError(w, http.StatusUnauthorized, "missing bearer token")
			return
		}
		id, err := h.svc.Authenticate(token)
		if err != nil {
			writeError(w, http.StatusUnauthorized, "invalid token")
			return
		}
		ctx := context.WithValue(r.Context(), userIDKey, id)
		next.ServeHTTP(w, r.WithContext(ctx))
	})
}

// UserIDFrom はコンテキストから認証済み userID を取り出す(無ければ uuid.Nil)。
func UserIDFrom(ctx context.Context) uuid.UUID {
	if v, ok := ctx.Value(userIDKey).(uuid.UUID); ok {
		return v
	}
	return uuid.Nil
}

func bearer(r *http.Request) string {
	h := r.Header.Get("Authorization")
	if after, ok := strings.CutPrefix(h, "Bearer "); ok {
		return strings.TrimSpace(after)
	}
	return ""
}

func decode(w http.ResponseWriter, r *http.Request) (credsReq, bool) {
	var req credsReq
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		writeError(w, http.StatusBadRequest, "invalid JSON body")
		return req, false
	}
	if req.UserName == "" || req.Password == "" {
		writeError(w, http.StatusBadRequest, "user_name and password are required")
		return req, false
	}
	return req, true
}

func writeJSON(w http.ResponseWriter, status int, body any) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(status)
	_ = json.NewEncoder(w).Encode(body)
}

func writeError(w http.ResponseWriter, status int, msg string) {
	writeJSON(w, status, map[string]string{"error": msg})
}
