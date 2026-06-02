"use client";

import { useEffect, useRef, useState } from "react";
import { Ring, RING_CATALOG, type RingStyle } from "@/components/Ring";
import { createHandLandmarker, ringTransformFor, type RingTransform } from "@/lib/handTracker";
import { createUser, getSession, recordTryOn, type FingerName } from "@/lib/api";

const FINGERS: { key: FingerName; label: string }[] = [
  { key: "index", label: "人差し指" },
  { key: "middle", label: "中指" },
  { key: "ring", label: "薬指" },
  { key: "pinky", label: "小指" },
];

export default function TryOnPage() {
  const videoRef = useRef<HTMLVideoElement | null>(null);
  const stageRef = useRef<HTMLDivElement | null>(null);
  const rafRef = useRef<number | null>(null);
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const landmarkerRef = useRef<any>(null);

  const [streaming, setStreaming] = useState(false);
  const [tracking, setTracking] = useState(false);
  const [handDetected, setHandDetected] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [ring, setRing] = useState<RingStyle>(RING_CATALOG[0]);
  const [finger, setFinger] = useState<FingerName>("ring");
  const [xf, setXf] = useState<RingTransform | null>(null);
  const [saveMsg, setSaveMsg] = useState<string | null>(null);

  const fingerRef = useRef<FingerName>(finger);
  fingerRef.current = finger;

  useEffect(() => {
    return () => {
      if (rafRef.current) cancelAnimationFrame(rafRef.current);
      const s = videoRef.current?.srcObject as MediaStream | null;
      s?.getTracks().forEach((t) => t.stop());
    };
  }, []);

  async function start() {
    setError(null);
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: "environment" },
        audio: false,
      });
      if (!videoRef.current) return;
      videoRef.current.srcObject = stream;
      await videoRef.current.play();
      setStreaming(true);

      landmarkerRef.current = await createHandLandmarker();
      setTracking(true);
      loop();
    } catch (e) {
      setError(
        "カメラまたは手認識モデルを起動できませんでした。" +
          (e instanceof Error ? `（${e.message}）` : ""),
      );
    }
  }

  function loop() {
    const video = videoRef.current;
    const stage = stageRef.current;
    const lm = landmarkerRef.current;
    if (video && stage && lm && video.readyState >= 2) {
      const res = lm.detectForVideo(video, performance.now());
      const hands = res?.landmarks;
      if (hands && hands.length > 0) {
        setHandDetected(true);
        setXf(ringTransformFor(hands[0], fingerRef.current, stage.clientWidth));
      } else {
        setHandDetected(false);
        setXf(null);
      }
    }
    rafRef.current = requestAnimationFrame(loop);
  }

  function onSave() {
    setSaveMsg(null);
    // ログイン中ならそのユーザー、未ログインはユニークなゲストを作成。
    const session = getSession();
    const userIdP = session
      ? Promise.resolve(session.user_id)
      : createUser(`guest-${Date.now()}`).then((u) => u.user_id);
    userIdP
      .then((uid) => recordTryOn(uid, ring.id, finger))
      .then(() => setSaveMsg("試着履歴に保存しました。"))
      .catch((e: unknown) => setSaveMsg("保存に失敗：" + (e instanceof Error ? e.message : String(e))));
  }

  return (
    <main className="container" style={{ maxWidth: 820, paddingTop: 28, paddingBottom: 48 }}>
      <span className="pill">TRY-ON · LIVE</span>
      <h1 style={{ fontSize: 32, margin: "12px 0 6px" }}>リアルタイム試着</h1>
      <p className="muted" style={{ marginTop: 0, fontSize: 14 }}>
        カメラに手をかざすと、選んだ指にリングを自動で重ねます（指認識はオンデバイス）。
      </p>

      {error && <div className="error" style={{ margin: "12px 0" }}>{error}</div>}

      <div
        ref={stageRef}
        className="glass"
        style={{
          position: "relative",
          aspectRatio: "4 / 3",
          marginTop: 14,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
        }}
      >
        <video
          ref={videoRef}
          playsInline
          muted
          style={{
            width: "100%",
            height: "100%",
            objectFit: "cover",
            borderRadius: "var(--radius)",
            display: streaming ? "block" : "none",
          }}
        />
        {!streaming && (
          <button className="btn btn-primary" onClick={start}>
            カメラを起動して試着
          </button>
        )}
        {streaming && xf && (
          <div
            style={{
              position: "absolute",
              left: `${xf.xPct}%`,
              top: `${xf.yPct}%`,
              transform: `translate(-50%, -50%) rotate(${xf.angleDeg}deg)`,
              filter: "drop-shadow(0 6px 10px rgba(0,0,0,0.35))",
              pointerEvents: "none",
              transition: "left 0.05s linear, top 0.05s linear",
            }}
          >
            <Ring ring={ring} width={xf.widthPx} />
          </div>
        )}
        {streaming && tracking && !handDetected && (
          <div
            className="pill"
            style={{ position: "absolute", bottom: 12, left: "50%", transform: "translateX(-50%)" }}
          >
            手をかざしてください
          </div>
        )}
      </div>

      <section className="glass card" style={{ marginTop: 16 }}>
        <div style={{ display: "flex", gap: 18, flexWrap: "wrap", alignItems: "center" }}>
          <label className="muted" style={{ fontSize: 13 }}>
            指{" "}
            <select className="field" value={finger} onChange={(e) => setFinger(e.target.value as FingerName)}>
              {FINGERS.map((f) => (
                <option key={f.key} value={f.key}>{f.label}</option>
              ))}
            </select>
          </label>
          <button className="btn" onClick={onSave} disabled={!streaming}>
            この試着を保存
          </button>
          {saveMsg && <span className="muted" style={{ fontSize: 13 }}>{saveMsg}</span>}
        </div>
        <h2 style={{ fontSize: 16, margin: "18px 0 10px" }}>リングを選ぶ</h2>
        <div style={{ display: "flex", gap: 12, flexWrap: "wrap" }}>
          {RING_CATALOG.map((r) => (
            <button
              key={r.id}
              onClick={() => setRing(r)}
              className="glass"
              style={{
                padding: 10,
                cursor: "pointer",
                background: "rgba(255,255,255,0.5)",
                boxShadow: ring.id === r.id ? "0 0 0 2px var(--gold)" : undefined,
              }}
            >
              <Ring ring={r} width={84} />
              <div className="muted" style={{ fontSize: 11, marginTop: 4 }}>{r.name}</div>
            </button>
          ))}
        </div>
      </section>
    </main>
  );
}
