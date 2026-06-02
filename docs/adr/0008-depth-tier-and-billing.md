# ADR-0008: 深度ティアと課金判定の配置

- ステータス: Accepted
- 日付: 2026-06-01
- 関連: ADR-0004, ADR-0005

## コンテキスト

ADR-0005 で「標準ティア(全機種・マルチフレーム)＋プレミアムティア(深度センサ・買い切り)」と
戦略IF化を決めた。実装にあたり、(1) 深度推定戦略の実体、(2) 課金判定をどこに置くか、を
確定する必要がある。

## 決定

### 推定戦略(Python)

`CircumferenceEstimator` を Protocol(戦略IF)とし、

- `EllipseFitCircumferenceEstimator`(標準): 真上2Dの幅に固定 深さ/幅比を掛けて楕円近似。
- `DepthBasedCircumferenceEstimator`(プレミアム): 深度センサで実測した厚み(`depth_mm`)で
  固定比を排した楕円近似。`depth_mm` 不在なら `DepthDataRequiredError`。
- `RegressionCircumferenceEstimator`(較正後の標準): 回帰モデル(ADR-0007)。

ティア→戦略の選択は `estimator_for_tier(tier)`。リクエストの `tier`(standard/premium)で
切替える。

### 課金判定(Go アプリ層)

課金/エンタイトルメント判定は **Go のアプリ層**(`internal/billing/application`)に置き、
ユーザー/計測のドメインには混ぜない。

- `billing/domain.Tier`(standard/premium)。
- `EntitlementPolicy.TierFor(userID) Tier` ポート + `StaticEntitlementPolicy`(暫定)。
- 計測フロー(`MeasurementService`)が `EntitlementPolicy` でティアを決め、AI クライアント経由で
  Python に `tier` を渡す。Python はティアに応じた戦略を選ぶ。

## 根拠

- 推定の数値ロジックは Python、課金というビジネス判断は Go アプリ層、という関心の分離
  (ADR-0001/0005)。ドメインに課金を混ぜないことでテスト容易性と置換性を保つ。
- 戦略IF化で標準/回帰/深度を無停止で差し替え可能。

## 影響

- 現状の 2D 画像パイプラインには深度入力が無いため、premium 選択時は
  `DepthDataRequiredError` → 422。**深度キャプチャ(LiDAR/TrueDepth フレーム)連携は今後の
  課題**で、本ADRはその受け皿(戦略+ティア選択+課金配置)を確定するもの。
- `StaticEntitlementPolicy` は暫定。実際の課金プロバイダ連携実装に差し替える。

## 代替案と却下理由

- 課金判定をドメイン/Python に置く: 関心の混在でテスト・保守性が悪化。却下。
- 深度を必須化: 全機種対応(標準ティア)の製品要件に反する。プレミアム併設とする。
