// Command api はユーザーAPIサーバを起動する。
//
// 環境変数:
//
//	DATABASE_URL  接続文字列(pgx5:// または postgres://、migrate と共用可)
//	PORT          待受ポート(既定 8080)
package main

import (
	"context"
	"errors"
	"log"
	"net/http"
	"os"
	"os/signal"
	"syscall"
	"time"

	platformpg "github.com/Sow-0429/ring_tryon/internal/platform/postgres"
	"github.com/Sow-0429/ring_tryon/internal/user/application"
	"github.com/Sow-0429/ring_tryon/internal/user/infrastructure/aiclient"
	userpg "github.com/Sow-0429/ring_tryon/internal/user/infrastructure/postgres"
	"github.com/Sow-0429/ring_tryon/internal/user/interfaces/httpapi"
)

func main() {
	if err := run(); err != nil {
		log.Fatal(err)
	}
}

func run() error {
	ctx, stop := signal.NotifyContext(
		context.Background(), syscall.SIGINT, syscall.SIGTERM,
	)
	defer stop()

	dsn := os.Getenv("DATABASE_URL")
	if dsn == "" {
		return errors.New("DATABASE_URL is required")
	}
	port := os.Getenv("PORT")
	if port == "" {
		port = "8080"
	}
	aiServiceURL := os.Getenv("AI_SERVICE_URL")
	if aiServiceURL == "" {
		aiServiceURL = "http://localhost:8000"
	}

	pool, err := platformpg.NewPool(ctx, dsn)
	if err != nil {
		return err
	}
	defer pool.Close()

	repo := userpg.NewUserRepository(pool)
	measurer := aiclient.NewClient(aiServiceURL)
	userSvc := application.NewUserService(repo)
	measurementSvc := application.NewMeasurementService(measurer, repo)
	router := httpapi.NewRouter(userSvc, measurementSvc)

	server := &http.Server{
		Addr:         ":" + port,
		Handler:      router,
		ReadTimeout:  10 * time.Second,
		WriteTimeout: 10 * time.Second,
	}

	errCh := make(chan error, 1)
	go func() {
		log.Printf("api listening on :%s", port)
		if err := server.ListenAndServe(); err != nil &&
			!errors.Is(err, http.ErrServerClosed) {
			errCh <- err
		}
	}()

	select {
	case err := <-errCh:
		return err
	case <-ctx.Done():
		log.Println("shutting down...")
		shutdownCtx, cancel := context.WithTimeout(
			context.Background(), 10*time.Second,
		)
		defer cancel()
		return server.Shutdown(shutdownCtx)
	}
}
