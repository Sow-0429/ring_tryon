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

	"github.com/Sow-0429/ring_tryon/internal/user/application"
	userdomain "github.com/Sow-0429/ring_tryon/internal/user/domain"
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
	Fingers           map[string]struct {
		CircumferenceMM float64 `json:"circumference_mm"`
		LengthMM        float64 `json:"length_mm"`
		BaseWidthMM     float64 `json:"base_width_mm"`
		PipWidthMM      float64 `json:"pip_width_mm"`
		WidthMM         float64 `json:"width_mm"`
	} `json:"fingers"`
}

// Measure は画像を ai_service に送り、各指の周囲長を返す。
func (c *Client) Measure(
	ctx context.Context,
	image []byte,
	filename string,
	cal application.Calibration,
) (userdomain.FingerCircumferences, error) {
	var zero userdomain.FingerCircumferences

	body, contentType, err := buildMultipart(image, filename, cal)
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

	return toFingerCircumferences(parsed)
}

func buildMultipart(
	image []byte, filename string, cal application.Calibration,
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

func toFingerCircumferences(
	r analyzeResponse,
) (userdomain.FingerCircumferences, error) {
	get := func(name string) (float64, error) {
		f, ok := r.Fingers[name]
		if !ok {
			return 0, fmt.Errorf("missing finger %q in ai_service response", name)
		}
		return f.CircumferenceMM, nil
	}

	index, err := get("index")
	if err != nil {
		return userdomain.FingerCircumferences{}, err
	}
	middle, err := get("middle")
	if err != nil {
		return userdomain.FingerCircumferences{}, err
	}
	ring, err := get("ring")
	if err != nil {
		return userdomain.FingerCircumferences{}, err
	}
	pinky, err := get("pinky")
	if err != nil {
		return userdomain.FingerCircumferences{}, err
	}

	return userdomain.FingerCircumferences{
		Index:  index,
		Middle: middle,
		Ring:   ring,
		Pinky:  pinky,
	}, nil
}
