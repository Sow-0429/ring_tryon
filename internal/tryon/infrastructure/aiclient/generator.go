// Package aiclient は ai_service の試着画像生成へのプロキシ。
package aiclient

import (
	"bytes"
	"context"
	"fmt"
	"io"
	"mime/multipart"
	"net/http"
	"strconv"
	"time"

	tryondomain "github.com/Sow-0429/ring_tryon/internal/tryon/domain"
)

// Generator は tryondomain.ImageGenerator を ai_service 呼び出しで実装する。
type Generator struct {
	baseURL    string
	httpClient *http.Client
}

func NewGenerator(baseURL string) *Generator {
	return &Generator{baseURL: baseURL, httpClient: &http.Client{Timeout: 60 * time.Second}}
}

func (g *Generator) Generate(
	ctx context.Context,
	image []byte,
	filename string,
	p tryondomain.RingPlacement,
	a tryondomain.RingAppearance,
	mode string,
) ([]byte, error) {
	var buf bytes.Buffer
	mw := multipart.NewWriter(&buf)
	fw, err := mw.CreateFormFile("image", filename)
	if err != nil {
		return nil, err
	}
	if _, err := fw.Write(image); err != nil {
		return nil, err
	}
	f := func(k string, v float64) { _ = mw.WriteField(k, strconv.FormatFloat(v, 'f', -1, 64)) }
	f("center_x", p.CenterX)
	f("center_y", p.CenterY)
	f("width_ratio", p.WidthRatio)
	f("angle_deg", p.AngleDeg)
	_ = mw.WriteField("metal", a.Metal)
	_ = mw.WriteField("metal_dark", a.MetalDark)
	_ = mw.WriteField("gem", a.Gem)
	if mode != "" {
		_ = mw.WriteField("mode", mode)
	}
	if err := mw.Close(); err != nil {
		return nil, err
	}

	req, err := http.NewRequestWithContext(
		ctx, http.MethodPost, g.baseURL+"/api/generate-tryon", &buf,
	)
	if err != nil {
		return nil, err
	}
	req.Header.Set("Content-Type", mw.FormDataContentType())

	resp, err := g.httpClient.Do(req)
	if err != nil {
		return nil, fmt.Errorf("call ai_service generate: %w", err)
	}
	defer resp.Body.Close()
	if resp.StatusCode != http.StatusOK {
		b, _ := io.ReadAll(io.LimitReader(resp.Body, 2048))
		return nil, fmt.Errorf("ai_service generate status %d: %s", resp.StatusCode, string(b))
	}
	return io.ReadAll(resp.Body)
}
