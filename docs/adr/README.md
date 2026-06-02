# Architecture Decision Records (ADR)

ring_tryon の主要なアーキテクチャ判断を記録する。1ファイル=1決定。後で覆す場合は
新しいADRを起こし、旧ADRのステータスを `Superseded by ADR-XXXX` に変更する（履歴を消さない）。

## フォーマット

各ADRは以下の節を持つ。

- ステータス: `Proposed` / `Accepted` / `Superseded` / `Deprecated`
- 日付
- コンテキスト（なぜ判断が必要か）
- 決定（何を決めたか）
- 根拠（なぜそれを選んだか）
- 影響（結果として何が起きるか）
- 代替案と却下理由

## 一覧

| ADR | タイトル | ステータス |
| --- | --- | --- |
| [0001](0001-go-python-responsibility-split.md) | Go/Python のサービス責務分割 | Accepted |
| [0002](0002-scale-reference-object.md) | スケール基準物（ID-1カード主軸＋コインフォールバック） | Accepted |
| [0003](0003-measurement-signal-segmentation.md) | 計測信号＝手セグメンテーションマスク＋付け根/PIP最大円周 | Accepted |
| [0004](0004-accuracy-strategy-calibration-loop.md) | 精度戦略＝正解データ較正ループ＋レンジ提示UX | Accepted |
| [0005](0005-capture-multiframe-and-depth-tier.md) | 撮影方式＝マルチフレーム標準ティア＋深度プレミアムティア | Accepted |
| [0006](0006-persistence-and-migrations.md) | 永続化とマイグレーション（PostgreSQL/golang-migrate/UUID） | Accepted |
| [0007](0007-dto-contract-and-calibration-loop.md) | Python↔Go の DTO 契約と較正ループの運用 | Accepted |
| [0008](0008-depth-tier-and-billing.md) | 深度ティアと課金判定の配置 | Accepted |
