// Command migrate は埋め込んだSQLマイグレーションを PostgreSQL に適用する。
//
// 使い方:
//
//	DATABASE_URL=pgx5://user:pass@localhost:5432/ring_tryon?sslmode=disable \
//	  go run ./cmd/migrate up      # 最新まで適用
//	  go run ./cmd/migrate down     # 1 つ戻す
//	  go run ./cmd/migrate version  # 現在のバージョンを表示
package main

import (
	"errors"
	"fmt"
	"log"
	"os"

	"github.com/golang-migrate/migrate/v4"
	_ "github.com/golang-migrate/migrate/v4/database/pgx/v5"
	"github.com/golang-migrate/migrate/v4/source/iofs"

	"github.com/Sow-0429/ring_tryon/db"
)

func main() {
	if err := run(); err != nil {
		log.Fatal(err)
	}
}

func run() error {
	command := "up"
	if len(os.Args) > 1 {
		command = os.Args[1]
	}

	dsn := os.Getenv("DATABASE_URL")
	if dsn == "" {
		return errors.New(
			"DATABASE_URL is required " +
				"(e.g. pgx5://user:pass@localhost:5432/ring_tryon?sslmode=disable)",
		)
	}

	source, err := iofs.New(db.MigrationsFS, "migrations")
	if err != nil {
		return fmt.Errorf("load embedded migrations: %w", err)
	}

	m, err := migrate.NewWithSourceInstance("iofs", source, dsn)
	if err != nil {
		return fmt.Errorf("init migrate: %w", err)
	}
	defer m.Close()

	switch command {
	case "up":
		err = m.Up()
	case "down":
		err = m.Steps(-1)
	case "version":
		version, dirty, verr := m.Version()
		if errors.Is(verr, migrate.ErrNilVersion) {
			fmt.Println("no migrations applied yet")
			return nil
		}
		if verr != nil {
			return fmt.Errorf("read version: %w", verr)
		}
		fmt.Printf("version=%d dirty=%t\n", version, dirty)
		return nil
	default:
		return fmt.Errorf("unknown command %q (use: up | down | version)", command)
	}

	if err != nil && !errors.Is(err, migrate.ErrNoChange) {
		return fmt.Errorf("migrate %s: %w", command, err)
	}
	log.Printf("migrate %s: ok", command)
	return nil
}
