// Package httpapi はユーザーAPIのHTTPハンドラを提供する。
package httpapi

import (
	"encoding/json"
	"errors"
	"io"
	"net/http"
	"strconv"

	"github.com/google/uuid"

	"github.com/Sow-0429/ring_tryon/internal/user/application"
	userdomain "github.com/Sow-0429/ring_tryon/internal/user/domain"
)

const maxImageBytes = 32 << 20 // 32MB

// NewRouter はユーザーAPIのルーティングを構築する(stdlib ServeMux)。
func NewRouter(
	svc *application.UserService, measurement *application.MeasurementService,
) *http.ServeMux {
	h := &handler{svc: svc, measurement: measurement}
	mux := http.NewServeMux()
	mux.HandleFunc("GET /health", h.health)
	mux.HandleFunc("POST /api/users", h.createUser)
	mux.HandleFunc("GET /api/users/{id}", h.getUser)
	mux.HandleFunc("POST /api/users/{id}/hand/measure", h.measureHand)
	mux.HandleFunc("POST /api/users/{id}/measure", h.measureFromImage)
	return mux
}

type handler struct {
	svc         *application.UserService
	measurement *application.MeasurementService
}

type handResponse struct {
	IndexJPSize  int `json:"index_jp_size"`
	MiddleJPSize int `json:"middle_jp_size"`
	RingJPSize   int `json:"ring_jp_size"`
	PinkyJPSize  int `json:"pinky_jp_size"`
}

type userResponse struct {
	UserID   string       `json:"user_id"`
	UserName string       `json:"user_name"`
	Hand     handResponse `json:"hand"`
}

func toUserResponse(u userdomain.User) userResponse {
	return userResponse{
		UserID:   u.UserID.String(),
		UserName: u.UserName,
		Hand: handResponse{
			IndexJPSize:  u.Hand.Index,
			MiddleJPSize: u.Hand.Middle,
			RingJPSize:   u.Hand.Ring,
			PinkyJPSize:  u.Hand.Pinky,
		},
	}
}

func (h *handler) health(w http.ResponseWriter, _ *http.Request) {
	writeJSON(w, http.StatusOK, map[string]string{"status": "ok"})
}

func (h *handler) createUser(w http.ResponseWriter, r *http.Request) {
	var req struct {
		UserName string `json:"user_name"`
	}
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		writeError(w, http.StatusBadRequest, "invalid JSON body")
		return
	}
	if req.UserName == "" {
		writeError(w, http.StatusBadRequest, "user_name is required")
		return
	}

	u, err := h.svc.CreateUser(r.Context(), req.UserName)
	if err != nil {
		writeError(w, http.StatusInternalServerError, "failed to create user")
		return
	}
	writeJSON(w, http.StatusCreated, toUserResponse(u))
}

func (h *handler) getUser(w http.ResponseWriter, r *http.Request) {
	id, err := uuid.Parse(r.PathValue("id"))
	if err != nil {
		writeError(w, http.StatusBadRequest, "invalid user id")
		return
	}

	u, err := h.svc.GetUser(r.Context(), id)
	if errors.Is(err, userdomain.ErrNotFound) {
		writeError(w, http.StatusNotFound, "user not found")
		return
	}
	if err != nil {
		writeError(w, http.StatusInternalServerError, "failed to get user")
		return
	}
	writeJSON(w, http.StatusOK, toUserResponse(u))
}

func (h *handler) measureHand(w http.ResponseWriter, r *http.Request) {
	id, err := uuid.Parse(r.PathValue("id"))
	if err != nil {
		writeError(w, http.StatusBadRequest, "invalid user id")
		return
	}

	var req struct {
		IndexMM  float64 `json:"index_mm"`
		MiddleMM float64 `json:"middle_mm"`
		RingMM   float64 `json:"ring_mm"`
		PinkyMM  float64 `json:"pinky_mm"`
	}
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		writeError(w, http.StatusBadRequest, "invalid JSON body")
		return
	}

	c := userdomain.FingerCircumferences{
		Index:  req.IndexMM,
		Middle: req.MiddleMM,
		Ring:   req.RingMM,
		Pinky:  req.PinkyMM,
	}
	u, err := h.svc.MeasureHand(r.Context(), id, c)
	switch {
	case errors.Is(err, userdomain.ErrNotFound):
		writeError(w, http.StatusNotFound, "user not found")
		return
	case errors.Is(err, userdomain.ErrInvalidCircumference):
		writeError(w, http.StatusUnprocessableEntity, "invalid finger circumference")
		return
	case err != nil:
		writeError(w, http.StatusInternalServerError, "failed to measure hand")
		return
	}
	writeJSON(w, http.StatusOK, toUserResponse(u))
}

// measureFromImage は画像(multipart)を ai_service で計測し、号数化して保存する。
func (h *handler) measureFromImage(w http.ResponseWriter, r *http.Request) {
	id, err := uuid.Parse(r.PathValue("id"))
	if err != nil {
		writeError(w, http.StatusBadRequest, "invalid user id")
		return
	}

	if err := r.ParseMultipartForm(maxImageBytes); err != nil {
		writeError(w, http.StatusBadRequest, "invalid multipart form")
		return
	}
	file, header, err := r.FormFile("image")
	if err != nil {
		writeError(w, http.StatusBadRequest, "image file is required")
		return
	}
	defer file.Close()
	image, err := io.ReadAll(io.LimitReader(file, maxImageBytes))
	if err != nil {
		writeError(w, http.StatusBadRequest, "failed to read image")
		return
	}

	cal, ok := parseCalibration(r)
	if !ok {
		writeError(
			w, http.StatusBadRequest,
			"specify exactly one calibration: middle_finger_length_mm, use_coin, or use_card",
		)
		return
	}

	var depthMM *float64
	if v := r.FormValue("depth_mm"); v != "" {
		if f, perr := strconv.ParseFloat(v, 64); perr == nil && f > 0 {
			depthMM = &f
		}
	}

	result, err := h.measurement.MeasureHandFromImage(
		r.Context(), id, image, header.Filename, cal, depthMM,
	)
	switch {
	case errors.Is(err, userdomain.ErrNotFound):
		writeError(w, http.StatusNotFound, "user not found")
		return
	case errors.Is(err, userdomain.ErrInvalidCircumference):
		writeError(w, http.StatusUnprocessableEntity, "invalid finger circumference")
		return
	case err != nil:
		writeError(w, http.StatusBadGateway, "measurement failed: "+err.Error())
		return
	}

	resp := struct {
		userResponse
		RecordID string `json:"record_id"`
	}{
		userResponse: toUserResponse(result.User),
		RecordID:     result.RecordID.String(),
	}
	writeJSON(w, http.StatusOK, resp)
}

// parseCalibration はフォームから較正指定を 1 つだけ読む。複数/ゼロは ok=false。
func parseCalibration(r *http.Request) (application.Calibration, bool) {
	var cal application.Calibration
	selected := 0

	if v := r.FormValue("middle_finger_length_mm"); v != "" {
		mm, err := strconv.ParseFloat(v, 64)
		if err != nil {
			return cal, false
		}
		cal.MiddleFingerLengthMM = &mm
		selected++
	}
	if r.FormValue("use_coin") == "true" {
		cal.UseCoin = true
		selected++
	}
	if r.FormValue("use_card") == "true" {
		cal.UseCard = true
		selected++
	}

	return cal, selected == 1
}

func writeJSON(w http.ResponseWriter, status int, body any) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(status)
	_ = json.NewEncoder(w).Encode(body)
}

func writeError(w http.ResponseWriter, status int, message string) {
	writeJSON(w, status, map[string]string{"error": message})
}
