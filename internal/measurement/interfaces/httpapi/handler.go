// Package httpapi は計測・較正APIのHTTPハンドラを提供する。
package httpapi

import (
	"encoding/json"
	"errors"
	"net/http"

	"github.com/google/uuid"

	"github.com/Sow-0429/ring_tryon/internal/measurement/application"
	measurementdomain "github.com/Sow-0429/ring_tryon/internal/measurement/domain"
)

// RegisterRoutes は較正APIを既存の mux に登録する。
func RegisterRoutes(mux *http.ServeMux, svc *application.CalibrationService) {
	h := &handler{svc: svc}
	mux.HandleFunc("PATCH /api/records/{id}/actual", h.setActual)
	mux.HandleFunc("GET /api/calibration/report", h.report)
	mux.HandleFunc("GET /api/calibration/dataset", h.dataset)
}

type handler struct {
	svc *application.CalibrationService
}

func (h *handler) setActual(w http.ResponseWriter, r *http.Request) {
	id, err := uuid.Parse(r.PathValue("id"))
	if err != nil {
		writeError(w, http.StatusBadRequest, "invalid record id")
		return
	}

	var req struct {
		Finger           string `json:"finger"`
		ActualRingSizeJP int    `json:"actual_ring_size_jp"`
	}
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		writeError(w, http.StatusBadRequest, "invalid JSON body")
		return
	}

	err = h.svc.SetActualRingSize(r.Context(), id, req.Finger, req.ActualRingSizeJP)
	switch {
	case errors.Is(err, measurementdomain.ErrInvalidFinger):
		writeError(w, http.StatusBadRequest, "invalid finger (index/middle/ring/pinky)")
		return
	case errors.Is(err, measurementdomain.ErrInvalidRingSize):
		writeError(w, http.StatusBadRequest, "invalid ring size (1-25)")
		return
	case errors.Is(err, measurementdomain.ErrNotFound):
		writeError(w, http.StatusNotFound, "measurement record not found")
		return
	case err != nil:
		writeError(w, http.StatusInternalServerError, "failed to set actual ring size")
		return
	}
	w.WriteHeader(http.StatusNoContent)
}

func (h *handler) report(w http.ResponseWriter, r *http.Request) {
	report, err := h.svc.Evaluate(r.Context())
	if err != nil {
		writeError(w, http.StatusInternalServerError, "failed to evaluate calibration")
		return
	}
	writeJSON(w, http.StatusOK, report)
}

func (h *handler) dataset(w http.ResponseWriter, r *http.Request) {
	samples, err := h.svc.TrainingDataset(r.Context())
	if err != nil {
		writeError(w, http.StatusInternalServerError, "failed to load training dataset")
		return
	}
	if samples == nil {
		samples = []measurementdomain.TrainingSample{}
	}
	writeJSON(w, http.StatusOK, samples)
}

func writeJSON(w http.ResponseWriter, status int, body any) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(status)
	_ = json.NewEncoder(w).Encode(body)
}

func writeError(w http.ResponseWriter, status int, message string) {
	writeJSON(w, status, map[string]string{"error": message})
}
