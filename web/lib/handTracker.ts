// MediaPipe Hands (tasks-vision HandLandmarker) のブラウザ実行ラッパー。
// WASM/モデルは CDN から取得する(クライアント実行のみ)。
import type { HandLandmarker as HL } from "@mediapipe/tasks-vision";

const WASM_BASE =
  "https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@0.10.35/wasm";
const MODEL_URL =
  "https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task";

export type Landmark = { x: number; y: number; z: number };

export async function createHandLandmarker(): Promise<HL> {
  const vision = await import("@mediapipe/tasks-vision");
  const fileset = await vision.FilesetResolver.forVisionTasks(WASM_BASE);
  return vision.HandLandmarker.createFromOptions(fileset, {
    baseOptions: { modelAssetPath: MODEL_URL, delegate: "GPU" },
    runningMode: "VIDEO",
    numHands: 1,
  });
}

// 指ごとの [MCP, PIP] ランドマーク添字。
export const FINGER_LANDMARKS: Record<string, [number, number]> = {
  index: [5, 6],
  middle: [9, 10],
  ring: [13, 14],
  pinky: [17, 18],
};

export type RingTransform = {
  /** stage に対する中心位置(%) */
  xPct: number;
  yPct: number;
  /** リング幅(px) */
  widthPx: number;
  /** 回転(deg) */
  angleDeg: number;
};

/**
 * 対象指の MCP/PIP から、リングの配置(位置/サイズ/回転)を求める。
 * landmarks は映像フレームに対する正規化座標 [0,1]。
 */
export function ringTransformFor(
  landmarks: Landmark[],
  finger: string,
  stageWidthPx: number,
): RingTransform | null {
  const idx = FINGER_LANDMARKS[finger];
  if (!idx) return null;
  const mcp = landmarks[idx[0]];
  const pip = landmarks[idx[1]];
  if (!mcp || !pip) return null;

  const t = 0.35; // 付け根寄りに配置
  const cx = mcp.x + (pip.x - mcp.x) * t;
  const cy = mcp.y + (pip.y - mcp.y) * t;

  const dx = pip.x - mcp.x;
  const dy = pip.y - mcp.y;
  const fingerAngle = (Math.atan2(dy, dx) * 180) / Math.PI;
  const segLen = Math.hypot(dx, dy); // 正規化長

  return {
    xPct: cx * 100,
    yPct: cy * 100,
    widthPx: Math.max(40, segLen * stageWidthPx * 1.05),
    angleDeg: fingerAngle + 90,
  };
}
