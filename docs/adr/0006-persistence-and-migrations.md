# ADR-0006: 永続化とマイグレーション

- ステータス: Accepted
- 日付: 2026-06-01
- 関連: ADR-0001, ADR-0004

## コンテキスト

較正ループ(ADR-0004)には計測結果と正解ラベルを蓄積する永続化が要る。ADR-0001 で
永続化は Go 側 = PostgreSQL と決めたが、具体的なスキーマ・マイグレーション運用・接続方式が
未定だった。

## 決定

### スキーマ

- `users(id UUID, user_name TEXT, created_at)` — ユーザーID は UUID(`gen_random_uuid()`)。
- `hands(user_id UUID PK&FK 1:1, index/middle/ring/pinky_jp_size, updated_at)` — ユーザーの
  現在の各指号数。計測後に当てはめる(未計測は NULL)。
- `measurement_records(id UUID, user_id UUID FK, calibration_method, pixels_per_mm,
  handedness, hand_confidence, frame_count, confidence, actual_ring_size_jp,
  actual_ring_finger, user_age, user_gender, created_at)` — 1 回の計測。較正ラベル
  (actual_ring_size_jp + actual_ring_finger)は計測後に付与。
- `finger_measurements(id UUID, measurement_record_id UUID FK, finger_name,
  length_mm, base_width_mm, pip_width_mm, width_mm, circumference_mm,
  UNIQUE(record,finger))` — 指別の回帰特徴量+推定周囲長。**号数列は持たない**(ADR-0001)。
- 号数は 1-25、finger_name は index/middle/ring/pinky を CHECK 制約で担保。

### マイグレーション運用

- golang-migrate(v4)。SQL は `db/migrations/NNNNNN_name.(up|down).sql`。
- `db/embed.go` が `//go:embed migrations/*.sql` でバイナリに埋め込む。
- `cmd/migrate`(pgx5 ドライバ + source/iofs)で `up|down|version`。接続は `DATABASE_URL`。

### 接続

- API サーバ(`cmd/api`)とマイグレーションは同一 `DATABASE_URL` を共用。`pgxpool` 側は
  `pgx5://` を `postgres://` に正規化して受ける。

## 根拠

- UUID はユーザー列挙耐性・分散採番の容易さ。指号数は 1:1 の `hands` に分けて「現在値」を
  明示しつつ、生計測は `measurement_records`/`finger_measurements` に時系列で残す。
- 埋め込み(embed)で単一バイナリ配布、golang-migrate で標準的・可逆な適用。

## 影響

- 計測フローは「生計測を records に保存 → hands に号数を当てはめ」を 1 リクエストで行う。
- 較正ラベルは別 API(ADR-0007)で後付けし、教師データを蓄積する。

## 代替案と却下理由

- GORM AutoMigrate: スキーマがモデル定義に従属し、可逆マイグレーション/SQLレビューがしづらい。
- ORM フル採用: 本プロジェクトは pgx + 明示SQL で十分、隠れた N+1 や魔法を避ける。
