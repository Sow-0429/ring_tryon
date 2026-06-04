"use client";

import { useState } from "react";
import {
  calibrationReport,
  createUser,
  getSession,
  measure,
  setActualRingSize,
  type Calibration,
  type CalibrationReport,
  type FingerName,
  type Hand,
  type MeasureResult,
} from "@/lib/api";

const FINGERS: { key: FingerName; label: string; sizeKey: keyof Hand }[] = [
  { key: "index", label: "人差し指", sizeKey: "index_jp_size" },
  { key: "middle", label: "中指", sizeKey: "middle_jp_size" },
  { key: "ring", label: "薬指", sizeKey: "ring_jp_size" },
  { key: "pinky", label: "小指", sizeKey: "pinky_jp_size" },
];

type CalKind = "card" | "coin" | "finger";

export default function SizingPage() {
  const [userName, setUserName] = useState("");
  const [userId, setUserId] = useState<string | null>(null);

  const [file, setFile] = useState<File | null>(null);
  const [calKind, setCalKind] = useState<CalKind>("card");
  const [middleLen, setMiddleLen] = useState("75");
  const [depthMm, setDepthMm] = useState("");

  const [result, setResult] = useState<MeasureResult | null>(null);
  const [actualFinger, setActualFinger] = useState<FingerName>("ring");
  const [actualSize, setActualSize] = useState("");
  const [report, setReport] = useState<CalibrationReport | null>(null);

  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  function run<T>(fn: () => Promise<T>, after?: (v: T) => void) {
    setBusy(true);
    setError(null);
    fn()
      .then((v) => after?.(v))
      .catch((e: unknown) => setError(e instanceof Error ? e.message : String(e)))
      .finally(() => setBusy(false));
  }

  function onCreateUser() {
    const session = getSession();
    if (session) {
      setUserId(session.user_id);
      setResult(null);
      setReport(null);
      return;
    }
    run(() => createUser(userName.trim() || `guest-${Date.now()}`), (u) => {
      setUserId(u.user_id);
      setResult(null);
      setReport(null);
    });
  }

  function onMeasure() {
    if (!userId || !file) return;
    const calibration: Calibration =
      calKind === "card"
        ? { kind: "card" }
        : calKind === "coin"
          ? { kind: "coin" }
          : { kind: "finger", middleFingerLengthMm: Number(middleLen) };
    const depth = depthMm ? Number(depthMm) : undefined;
    run(() => measure(userId, file, calibration, { filename: file.name, depthMm: depth }), setResult);
  }

  function onSubmitActual() {
    if (!result || !actualSize) return;
    run(
      () => setActualRingSize(result.record_id, actualFinger, Number(actualSize)),
      () => run(calibrationReport, setReport),
    );
  }

  return (
    <main className="container" style={{ maxWidth: 720, paddingTop: 28, paddingBottom: 48 }}>
      <span className="pill">MEASURE</span>
      <h1 style={{ fontSize: 32, margin: "12px 0 22px" }}>指号数の計測</h1>

      {error && <div className="error" style={{ marginBottom: 18 }}>エラー: {error}</div>}

      <section className="glass card" style={{ marginBottom: 16 }}>
        <h2 style={{ fontSize: 18, marginTop: 0 }}>1. ユーザー</h2>
        <div style={{ display: "flex", gap: 10 }}>
          <input
            className="field"
            style={{ flex: 1 }}
            placeholder="お名前"
            value={userName}
            onChange={(e) => setUserName(e.target.value)}
            disabled={busy}
          />
          <button className="btn btn-primary" onClick={onCreateUser} disabled={busy}>
            はじめる
          </button>
        </div>
        {userId && (
          <p className="muted" style={{ fontSize: 12, marginBottom: 0 }}>ID: {userId}</p>
        )}
      </section>

      <section className="glass card" style={{ marginBottom: 16, opacity: userId ? 1 : 0.5 }}>
        <h2 style={{ fontSize: 18, marginTop: 0 }}>2. 撮影と計測</h2>
        <p className="muted" style={{ fontSize: 13, marginTop: 0 }}>
          手のひらを平らに置き、真上から撮影してください。基準物（カード等）を一緒に写します。
        </p>
        <input
          className="field"
          type="file"
          accept="image/*"
          capture="environment"
          onChange={(e) => setFile(e.target.files?.[0] ?? null)}
          disabled={!userId || busy}
        />
        <div style={{ marginTop: 14, display: "flex", gap: 12, alignItems: "center", flexWrap: "wrap" }}>
          <label className="muted" style={{ fontSize: 13 }}>
            基準物{" "}
            <select
              className="field"
              value={calKind}
              onChange={(e) => setCalKind(e.target.value as CalKind)}
              disabled={busy}
            >
              <option value="card">カード(ID-1)</option>
              <option value="coin">100円玉</option>
              <option value="finger">中指実長(mm)</option>
            </select>
          </label>
          {calKind === "finger" && (
            <input
              className="field"
              style={{ width: 96 }}
              type="number"
              value={middleLen}
              onChange={(e) => setMiddleLen(e.target.value)}
              disabled={busy}
            />
          )}
          <button className="btn btn-primary" onClick={onMeasure} disabled={!userId || !file || busy}>
            {busy ? "計測中…" : "計測する"}
          </button>
        </div>
        <label className="muted" style={{ fontSize: 12, display: "block", marginTop: 12 }}>
          指の厚み実測 mm（任意・プレミアム/深度センサ。入力すると深度ベース推定を使用）
          <input
            className="field"
            style={{ width: 110, display: "block", marginTop: 4 }}
            type="number"
            placeholder="例: 14.5"
            value={depthMm}
            onChange={(e) => setDepthMm(e.target.value)}
            disabled={busy}
          />
        </label>
      </section>

      {result && (
        <section className="glass card glass-strong" style={{ marginBottom: 16 }}>
          <h2 style={{ fontSize: 18, marginTop: 0 }}>3. 計測結果</h2>
          <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 8 }}>
            {FINGERS.map((f) => (
              <div key={f.key} style={{ textAlign: "center" }}>
                <div className="muted" style={{ fontSize: 12 }}>{f.label}</div>
                <div style={{ fontFamily: "var(--serif)", fontSize: 34, color: "var(--gold-deep)" }}>
                  {result.hand[f.sizeKey]}
                  <span className="muted" style={{ fontSize: 12 }}>号</span>
                </div>
              </div>
            ))}
          </div>
        </section>
      )}

      {result && (
        <section className="glass card">
          <h2 style={{ fontSize: 18, marginTop: 0 }}>4. 較正（実際の号数）</h2>
          <p className="muted" style={{ fontSize: 13, marginTop: 0 }}>
            既に分かっている号数を登録すると、推定精度の改善に使われます。
          </p>
          <div style={{ display: "flex", gap: 10, alignItems: "center", flexWrap: "wrap" }}>
            <select
              className="field"
              value={actualFinger}
              onChange={(e) => setActualFinger(e.target.value as FingerName)}
              disabled={busy}
            >
              {FINGERS.map((f) => (
                <option key={f.key} value={f.key}>{f.label}</option>
              ))}
            </select>
            <input
              className="field"
              style={{ width: 96 }}
              type="number"
              min={1}
              max={25}
              placeholder="号数"
              value={actualSize}
              onChange={(e) => setActualSize(e.target.value)}
              disabled={busy}
            />
            <button className="btn btn-primary" onClick={onSubmitActual} disabled={!actualSize || busy}>
              登録
            </button>
          </div>
          {report && (
            <p style={{ fontSize: 13, marginTop: 14 }}>
              較正レポート：±1号一致 {report.within_one_size}/{report.total}（
              {(report.within_one_size_ratio * 100).toFixed(0)}%）、平均誤差{" "}
              {report.mean_abs_size_error.toFixed(2)} 号
            </p>
          )}
        </section>
      )}
    </main>
  );
}
