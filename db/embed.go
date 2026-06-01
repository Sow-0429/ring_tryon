// Package db はマイグレーションSQLをバイナリに埋め込んで公開する。
package db

import "embed"

// MigrationsFS は db/migrations 配下の golang-migrate 形式SQLを埋め込む。
// embed は親ディレクトリを参照できないため、この埋め込み口は db パッケージに置く。
//
//go:embed migrations/*.sql
var MigrationsFS embed.FS
