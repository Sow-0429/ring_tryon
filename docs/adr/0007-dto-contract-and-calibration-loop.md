# ADR-0007: Python↔Go の DTO 契約と較正ループの運用

- ステータス: Accepted
- 日付: 2026-06-01
- 関連: ADR-0001, ADR-0004, ADR-0006

## コンテキスト

ADR-0001 で「Python は周囲長まで、号数化は Go」と決めたが、当初は Python の
`/api/analyze-hand` が号数(JP/US/EU)も返しており、号数テーブルが Python と Go で二重に
存在していた(移行債務)。較正ループ(ADR-0004)の運用フロー(正解ラベルの受領→蓄積→評価)も
未配線だった。

## 決定

### DTO 契約(Python → Go)

Python ai_service の応答は **周囲長 + 回帰特徴量 + 撮影メタ + 信頼度** のみとし、**号数を
返さない**。Python の `RingSize`(号数化)は廃し `CircumferenceEstimate`(周囲長のみ)に置換。

- 1 指あたり: `circumference_mm, length_mm, base_width_mm, pip_width_mm, width_mm`。
- セッション: `pixels_per_mm, calibration_method, handedness, confidence(手検出), frame_count`。
- Go の AI クライアントは circumference_mm 等のみ取り込み、号数は `ring_size`(Go = 唯一の
  真実の源)で算出する。

### 較正ループの運用

- `POST /api/users/{id}/measure`: 画像 → Python計測 → Go で号数化 → `measurement_records`/
  `finger_measurements` に生計測を保存 → `hands` に号数を当てはめ。
- `PATCH /api/records/{id}/actual {finger, actual_ring_size_jp}`: 正解号数(較正ラベル)を
  対象指に付与。
- `GET /api/calibration/report`: 蓄積ラベルに対する現行推定の精度。予測周囲長→`ring_size`の
  号数 と 正解号数 を**号数空間で ±1号**比較し、`within_one_size_ratio`(受け入れ基準
  ±1号@80%)と `mean_abs_size_error` を返す。
- 号数↔周囲長の双方向変換(`RingSize.JPSize` / `CircumferenceForJPSize`)は Go の
  `ring_size` パッケージに一本化。

### 回帰モデル(Phase3 本命)

Python に `CircumferenceRegressionModel`(指種別の線形回帰、特徴量[付け根幅,関節幅,指長])と
`RegressionCircumferenceEstimator` を用意。蓄積データが貯まれば固定比(EllipseFit)から
回帰へ無停止で差し替える(戦略IF / ADR-0005)。

## 根拠

- 号数化を Go に一本化することで二重管理(バグ源)を解消。Python は数値計算に専念。
- 受け入れ評価を号数空間の ±1号で測ることで、製品要件(±1号@80%)と直結。
- 回帰は系統バイアスを正解データで吸収でき、固定比より精度レバーが大きい(ADR-0004)。

## 影響

- Python 応答から号数フィールドを削除(Go は元々無視しており実害なし)。
- 較正データは Go が保持し、回帰学習は Python が蓄積データのエクスポートを受けて行う
  (学習データの受け渡し方式は未確定 = 今後の課題)。

## 代替案と却下理由

- Python が号数を返し続ける: 号数テーブル二重管理が残り、真実の源が二つになる。却下。
- 較正評価を Python 側で行う: 号数化が Go にあるため評価も Go(DB近接)が自然。
