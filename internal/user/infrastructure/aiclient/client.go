// Package aiclient は Python ai_service を呼ぶ計測クライアント。
// application.HandMeasurer を実装する。
package aiclient

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"io"
	"mime/multipart"
	"net/http"
	"strconv"
	"time"

	measurementdomain "github.com/Sow-0429/ring_tryon/internal/measurement/domain"
	"github.com/Sow-0429/ring_tryon/internal/user/application"
)

// Client は ai_service への HTTP クライアント。
type Client struct {
	baseURL    string
	httpClient *http.Client
}

func NewClient(baseURL string) *Client {
	return &Client{
		baseURL:    baseURL,
		httpClient: &http.Client{Timeout: 30 * time.Second},
	}
}

// analyzeResponse は ai_service /api/analyze-hand の応答のうち Go が必要とする部分のみ。
// 号数フィールド(ring_size_*)は意図的に取り込まない(号数化は Go = ADR-0001)。
type analyzeResponse struct {
	PixelsPerMM       float64 `json:"pixels_per_mm"`
	CalibrationMethod string  `json:"calibration_method"`
	Handedness        string  `json:"handedness"`
	Confidence        float64 `json:"confidence"` // 手検出(ランドマーク)の信頼度
	Fingers           map[string]struct {
		CircumferenceMM float64 `json:"circumference_mm"`
		LengthMM        float64 `json:"length_mm"`
		BaseWidthMM     float64 `json:"base_width_mm"`
		PipWidthMM      float64 `json:"pip_width_mm"`
		WidthMM         float64 `json:"width_mm"`
	} `json:"fingers"`
}

// Measure は画像を ai_service に送り、計測結果(周囲長+特徴量+メタ)を返す。
func (c *Client) Measure(
	ctx context.Context,
	image []byte,
	filename string,
	cal application.Calibration,
	tier string,
) (measurementdomain.Measurement, error) {
	var zero measurementdomain.Measurement

	body, contentType, err := buildMultipart(image, filename, cal, tier)
	if err != nil {
		return zero, err
	}

	req, err := http.NewRequestWithContext(
		ctx, http.MethodPost, c.baseURL+"/api/analyze-hand", body,
	)
	if err != nil {
		return zero, err
	}
	req.Header.Set("Content-Type", contentType)

	resp, err := c.httpClient.Do(req)
	if err != nil {
		return zero, fmt.Errorf("call ai_service: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		b, _ := io.ReadAll(io.LimitReader(resp.Body, 2048))
		return zero, fmt.Errorf(
			"ai_service status %d: %s", resp.StatusCode, string(b),
		)
	}

	var parsed analyzeResponse
	if err := json.NewDecoder(resp.Body).Decode(&parsed); err != nil {
		return zero, fmt.Errorf("decode ai_service response: %w", err)
	}

	return toMeasurement(parsed), nil
}

func buildMultipart(
	image []byte, filename string, cal application.Calibration, tier string,
) (*bytes.Buffer, string, error) {
	var buf bytes.Buffer
	mw := multipart.NewWriter(&buf)

	fw, err := mw.CreateFormFile("image", filename)
	if err != nil {
		return nil, "", err
	}
	if _, err := fw.Write(image); err != nil {
		return nil, "", err
	}

	if tier != "" {
		_ = mw.WriteField("tier", tier)
	}

	switch {
	case cal.UseCoin:
		_ = mw.WriteField("use_coin", "true")
	case cal.UseCard:
		_ = mw.WriteField("use_card", "true")
	case cal.MiddleFingerLengthMM != nil:
		_ = mw.WriteField(
			"middle_finger_length_mm",
			strconv.FormatFloat(*cal.MiddleFingerLengthMM, 'f', -1, 64),
		)
	}

	if err := mw.Close(); err != nil {
		return nil, "", err
	}
	return &buf, mw.FormDataContentType(), nil
}

func toMeasurement(r analyzeResponse) measurementdomain.Measurement {
	fingers := make(map[string]measurementdomain.FingerMeasurement, len(r.Fingers))
	for name, f := range r.Fingers {
		fingers[name] = measurementdomain.FingerMeasurement{
			FingerName:      name,
			LengthMM:        f.LengthMM,
			BaseWidthMM:     f.BaseWidthMM,
			PipWidthMM:      f.PipWidthMM,
			WidthMM:         f.WidthMM,
			CircumferenceMM: f.CircumferenceMM,
		}
	}
	// 単発計測なのでフレーム集約の信頼度は持たない(nil)。
	return measurementdomain.Measurement{
		CalibrationMethod: r.CalibrationMethod,
		PixelsPerMM:       r.PixelsPerMM,
		Handedness:        r.Handedness,
		HandConfidence:    r.Confidence,
		FrameCount:        1,
		Confidence:        nil,
		Fingers:           fingers,
	}
}
