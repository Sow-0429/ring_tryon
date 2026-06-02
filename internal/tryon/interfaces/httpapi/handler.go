// Package httpapi は試着APIのHTTPハンドラ。
package httpapi

import (
	"encoding/json"
	"errors"
	"io"
	"net/http"
	"strconv"

	"github.com/google/uuid"

	"github.com/Sow-0429/ring_tryon/internal/tryon/application"
	tryondomain "github.com/Sow-0429/ring_tryon/internal/tryon/domain"
)

const maxImageBytes = 32 << 20

func RegisterRoutes(mux *http.ServeMux, svc *application.Service) {
	h := &handler{svc: svc}
	mux.HandleFunc("POST /api/users/{id}/tryons", h.recordTryOn)
	mux.HandleFunc("POST /api/tryon/generate", h.generate)
}

type handler struct {
	svc *application.Service
}

func (h *handler) recordTryOn(w http.ResponseWriter, r *http.Request) {
	id, err := uuid.Parse(r.PathValue("id"))
	if err != nil {
		writeError(w, http.StatusBadRequest, "invalid user id")
		return
	}
	var req struct {
		RingID string `json:"ring_id"`
		Finger string `json:"finger"`
	}
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		writeError(w, http.StatusBadRequest, "invalid JSON body")
		return
	}
	if req.RingID == "" {
		writeError(w, http.StatusBadRequest, "ring_id is required")
		return
	}
	err = h.svc.RecordTryOn(r.Context(), id, req.RingID, req.Finger)
	switch {
	case errors.Is(err, tryondomain.ErrInvalidFinger):
		writeError(w, http.StatusBadRequest, "invalid finger (index/middle/ring/pinky)")
		return
	case err != nil:
		writeError(w, http.StatusInternalServerError, "failed to record try-on")
		return
	}
	w.WriteHeader(http.StatusNoContent)
}

func (h *handler) generate(w http.ResponseWriter, r *http.Request) {
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

	placement := tryondomain.RingPlacement{
		CenterX:    formFloat(r, "center_x", 0.5),
		CenterY:    formFloat(r, "center_y", 0.55),
		WidthRatio: formFloat(r, "width_ratio", 0.25),
		AngleDeg:   formFloat(r, "angle_deg", 0),
	}
	appearance := tryondomain.RingAppearance{
		Metal:     formStr(r, "metal", "#b9975b"),
		MetalDark: formStr(r, "metal_dark", "#9c7c43"),
		Gem:       formStr(r, "gem", "#fff6e0"),
	}

	mode := formStr(r, "mode", "composite")
	png, err := h.svc.GenerateImage(r.Context(), image, header.Filename, placement, appearance, mode)
	if err != nil {
		writeError(w, http.StatusBadGateway, "generation failed: "+err.Error())
		return
	}
	w.Header().Set("Content-Type", "image/png")
	_, _ = w.Write(png)
}

func formFloat(r *http.Request, key string, def float64) float64 {
	if v := r.FormValue(key); v != "" {
		if f, err := strconv.ParseFloat(v, 64); err == nil {
			return f
		}
	}
	return def
}

func formStr(r *http.Request, key, def string) string {
	if v := r.FormValue(key); v != "" {
		return v
	}
	return def
}

func writeError(w http.ResponseWriter, status int, message string) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(status)
	_ = json.NewEncoder(w).Encode(map[string]string{"error": message})
}
