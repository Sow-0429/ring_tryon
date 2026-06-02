"use client";

import { useRef, useState } from "react";
import { Ring, RING_CATALOG, type RingStyle } from "@/components/Ring";
import { generateTryOn, type GenerateMode } from "@/lib/api";

// 手画像 + リング配置をバックエンド(Go→ai_service / Pillow合成)に送り、
// 合成済み PNG を受け取って表示する。
export default function GeneratePage() {
  const [file, setFile] = useState<File | null>(null);
  const [imageUrl, setImageUrl] = useState<string | null>(null);
  const [ring, setRing] = useState<RingStyle>(RING_CATALOG[0]);
  const [result, setResult] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const wrapRef = useRef<HTMLDivElement | null>(null);
  const dragging = useRef(false);
  const [pos, setPos] = useState({ x: 50, y: 55 });
  const [ringWidth, setRingWidth] = useState(120);
  const [angle, setAngle] = useState(0);

  function onFile(f: File | null) {
    setResult(null);
    setError(null);
    setFile(f);
    setImageUrl(f ? URL.createObjectURL(f) : null);
  }

  function move(clientX: number, clientY: number) {
    const el = wrapRef.current;
    if (!el) return;
    const r = el.getBoundingClientRect();
    setPos({
      x: Math.max(0, Math.min(100, ((clientX - r.left) / r.width) * 100)),
      y: Math.max(0, Math.min(100, ((clientY - r.top) / r.height) * 100)),
    });
  }

  function onGenerate() {
    if (!file || !wrapRef.current) return;
    setBusy(true);
    setError(null);
    const widthRatio = ringWidth / wrapRef.current.clientWidth;
    generateTryOn(
      file,
      { centerX: pos.x / 100, centerY: pos.y / 100, widthRatio, angleDeg: angle },
      { metal: ring.metal, metalDark: ring.metalDark, gem: ring.gem },
      file.name,
    )
      .then(setResult)
      .catch((e: unknown) => setError(e instanceof Error ? e.message : String(e)))
      .finally(() => setBusy(false));
  }

  return (
    <main className="container" style={{ maxWidth: 820, paddingTop: 28, paddingBottom: 48 }}>
      <span className="pill">GENERATE</span>
      <h1 style={{ fontSize: 32, margin: "12px 0 6px" }}>試着画像生成</h1>
      <p className="muted" style={{ marginTop: 0, fontSize: 14 }}>
        手の写真にリングを重ねた一枚を、サーバ側で合成して書き出します。
      </p>

      {error && <div className="error" style={{ margin: "12px 0" }}>{error}</div>}

      <section className="glass card" style={{ marginTop: 14 }}>
        <input className="field" type="file" accept="image/*" onChange={(e) => onFile(e.target.files?.[0] ?? null)} />
        <div style={{ display: "flex", gap: 12, flexWrap: "wrap", marginTop: 14 }}>
          {RING_CATALOG.map((r) => (
            <button
              key={r.id}
              onClick={() => setRing(r)}
              className="glass"
              style={{
                padding: 8,
                cursor: "pointer",
                background: "rgba(255,255,255,0.5)",
                boxShadow: ring.id === r.id ? "0 0 0 2px var(--gold)" : undefined,
              }}
            >
              <Ring ring={r} width={72} />
            </button>
          ))}
        </div>
      </section>

      {imageUrl && (
        <div
          ref={wrapRef}
          className="glass"
          style={{ position: "relative", marginTop: 16, overflow: "hidden", touchAction: "none" }}
          onPointerMove={(e) => dragging.current && move(e.clientX, e.clientY)}
          onPointerUp={() => (dragging.current = false)}
          onPointerLeave={() => (dragging.current = false)}
        >
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img src={imageUrl} alt="hand" style={{ width: "100%", display: "block" }} />
          <div
            onPointerDown={(e) => {
              dragging.current = true;
              e.currentTarget.setPointerCapture(e.pointerId);
            }}
            style={{
              position: "absolute",
              left: `${pos.x}%`,
              top: `${pos.y}%`,
              transform: `translate(-50%, -50%) rotate(${angle}deg)`,
              cursor: "grab",
              filter: "drop-shadow(0 6px 10px rgba(0,0,0,0.35))",
            }}
          >
            <Ring ring={ring} width={ringWidth} />
          </div>
        </div>
      )}

      {imageUrl && (
        <section className="glass card" style={{ marginTop: 16 }}>
          <label className="muted" style={{ fontSize: 13 }}>
            サイズ
            <input
              type="range" min={40} max={260} value={ringWidth}
              onChange={(e) => setRingWidth(Number(e.target.value))}
              style={{ display: "block", width: "100%", marginTop: 6, accentColor: "var(--gold-deep)" }}
            />
          </label>
          <label className="muted" style={{ fontSize: 13, display: "block", marginTop: 12 }}>
            角度
            <input
              type="range" min={-90} max={90} value={angle}
              onChange={(e) => setAngle(Number(e.target.value))}
              style={{ display: "block", width: "100%", marginTop: 6, accentColor: "var(--gold-deep)" }}
            />
          </label>
          <div style={{ display: "flex", gap: 12, marginTop: 16 }}>
            <button className="btn btn-primary" onClick={onGenerate} disabled={busy}>
              {busy ? "生成中…" : "サーバで生成"}
            </button>
            {result && (
              <a className="btn" href={result} download="ring-tryon.png">
                ダウンロード
              </a>
            )}
          </div>
        </section>
      )}

      {result && (
        <section className="glass card" style={{ marginTop: 16 }}>
          <h2 style={{ fontSize: 16, marginTop: 0 }}>生成結果</h2>
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img src={result} alt="generated" style={{ width: "100%", borderRadius: 14 }} />
        </section>
      )}
    </main>
  );
}
