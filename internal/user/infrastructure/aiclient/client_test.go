package aiclient

import (
	"context"
	"net/http"
	"net/http/httptest"
	"strings"
	"testing"

	"github.com/Sow-0429/ring_tryon/internal/user/application"
)

func TestClient_Measure(t *testing.T) {
	t.Run("circumference_mm を写像し、号数は無視する", func(t *testing.T) {
		// Arrange: ai_service を模した httptest サーバ(号数フィールドも含む)。
		var gotContentType string
		var gotPath string
		srv := httptest.NewServer(http.HandlerFunc(
			func(w http.ResponseWriter, r *http.Request) {
				gotContentType = r.Header.Get("Content-Type")
				gotPath = r.URL.Path
				w.Header().Set("Content-Type", "application/json")
				_, _ = w.Write([]byte(`{
				  "pixels_per_mm": 10.0,
				  "calibration_method": "card_id1",
				  "handedness": "Right",
				  "confidence": 0.95,
				  "fingers": {
				    "index":  {"circumference_mm": 50.5, "length_mm": 70, "base_width_mm": 16, "pip_width_mm": 16, "width_mm": 16, "ring_size_jp": 99},
				    "middle": {"circumference_mm": 53.5, "length_mm": 80, "base_width_mm": 17, "pip_width_mm": 17, "width_mm": 17, "ring_size_jp": 99},
				    "ring":   {"circumference_mm": 52.5, "length_mm": 75, "base_width_mm": 16, "pip_width_mm": 17, "width_mm": 17, "ring_size_jp": 99},
				    "pinky":  {"circumference_mm": 45.0, "length_mm": 60, "base_width_mm": 14, "pip_width_mm": 14, "width_mm": 14, "ring_size_jp": 99}
				  }
				}`))
			}))
		defer srv.Close()

		client := NewClient(srv.URL)

		// Act
		c, err := client.Measure(
			context.Background(), []byte("imgdata"), "hand.jpg",
			application.Calibration{UseCard: true},
		)

		// Assert
		if err != nil {
			t.Fatalf("unexpected error: %v", err)
		}
		if c.Index != 50.5 || c.Middle != 53.5 || c.Ring != 52.5 || c.Pinky != 45.0 {
			t.Errorf("circumferences = %+v", c)
		}
		if gotPath != "/api/analyze-hand" {
			t.Errorf("path = %q", gotPath)
		}
		if !strings.HasPrefix(gotContentType, "multipart/form-data") {
			t.Errorf("content-type = %q", gotContentType)
		}
	})

	t.Run("非200はエラー", func(t *testing.T) {
		srv := httptest.NewServer(http.HandlerFunc(
			func(w http.ResponseWriter, _ *http.Request) {
				w.WriteHeader(http.StatusUnprocessableEntity)
				_, _ = w.Write([]byte(`{"detail":"No hand detected in image"}`))
			}))
		defer srv.Close()

		_, err := NewClient(srv.URL).Measure(
			context.Background(), []byte("x"), "x.jpg",
			application.Calibration{UseCoin: true},
		)
		if err == nil {
			t.Fatal("expected error for non-200 response")
		}
	})
}
