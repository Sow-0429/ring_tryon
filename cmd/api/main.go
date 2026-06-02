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

	authapp "github.com/Sow-0429/ring_tryon/internal/auth/application"
	authdomain "github.com/Sow-0429/ring_tryon/internal/auth/domain"
	authpg "github.com/Sow-0429/ring_tryon/internal/auth/infrastructure/postgres"
	authhttp "github.com/Sow-0429/ring_tryon/internal/auth/interfaces/httpapi"
	billingapp "github.com/Sow-0429/ring_tryon/internal/billing/application"
	measurementapp "github.com/Sow-0429/ring_tryon/internal/measurement/application"
	measurementpg "github.com/Sow-0429/ring_tryon/internal/measurement/infrastructure/postgres"
	measurementhttp "github.com/Sow-0429/ring_tryon/internal/measurement/interfaces/httpapi"
	platformpg "github.com/Sow-0429/ring_tryon/internal/platform/postgres"
	tryonapp "github.com/Sow-0429/ring_tryon/internal/tryon/application"
	tryonai "github.com/Sow-0429/ring_tryon/internal/tryon/infrastructure/aiclient"
	tryonpg "github.com/Sow-0429/ring_tryon/internal/tryon/infrastructure/postgres"
	tryonhttp "github.com/Sow-0429/ring_tryon/internal/tryon/interfaces/httpapi"
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
	jwtSecret := os.Getenv("JWT_SECRET")
	if jwtSecret == "" {
		jwtSecret = "dev-insecure-secret-change-me"
	}

	pool, err := platformpg.NewPool(ctx, dsn)
	if err != nil {
		return err
	}
	defer pool.Close()

	repo := userpg.NewUserRepository(pool)
	recordRepo := measurementpg.NewRecordRepository(pool)
	measurer := aiclient.NewClient(aiServiceURL)
	entitlements := billingapp.NewStaticEntitlementPolicy()
	userSvc := application.NewUserService(repo)
	measurementSvc := application.NewMeasurementService(
		measurer, repo, recordRepo, entitlements,
	)
	calibrationSvc := measurementapp.NewCalibrationService(recordRepo)
	tryonSvc := tryonapp.NewService(
		tryonpg.NewTryOnRepository(pool),
		tryonai.NewGenerator(aiServiceURL),
	)
	authSvc := authapp.NewAuthService(
		authpg.NewCredentialRepository(pool),
		authdomain.NewTokenService(jwtSecret),
	)
	router := httpapi.NewRouter(userSvc, measurementSvc)
	measurementhttp.RegisterRoutes(router, calibrationSvc)
	tryonhttp.RegisterRoutes(router, tryonSvc)
	authhttp.RegisterRoutes(router, authSvc)

	corsOrigin := os.Getenv("CORS_ALLOW_ORIGIN")
	if corsOrigin == "" {
		corsOrigin = "*"
	}

	server := &http.Server{
		Addr:         ":" + port,
		Handler:      withCORS(router, corsOrigin),
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

// withCORS は開発時にフロントエンドから叩けるよう CORS ヘッダを付与する。
func withCORS(next http.Handler, origin string) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Access-Control-Allow-Origin", origin)
		w.Header().Set("Access-Control-Allow-Methods", "GET, POST, PATCH, OPTIONS")
		w.Header().Set("Access-Control-Allow-Headers", "Content-Type")
		if r.Method == http.MethodOptions {
			w.WriteHeader(http.StatusNoContent)
			return
		}
		next.ServeHTTP(w, r)
	})
}
