// Go API (ring_tryon) の型付きクライアント。
// 号数化は Go が担うため、フロントは号数(JP)をそのまま受け取る。

const BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8080";

export type Hand = {
  index_jp_size: number;
  middle_jp_size: number;
  ring_jp_size: number;
  pinky_jp_size: number;
};

export type User = {
  user_id: string;
  user_name: string;
  hand: Hand;
};

export type MeasureResult = User & {
  record_id: string;
};

export type CalibrationReport = {
  total: number;
  within_one_size: number;
  within_one_size_ratio: number;
  mean_abs_size_error: number;
};

export type FingerName = "index" | "middle" | "ring" | "pinky";

export type Calibration =
  | { kind: "card" }
  | { kind: "coin" }
  | { kind: "finger"; middleFingerLengthMm: number };

async function asError(res: Response): Promise<Error> {
  let detail = `${res.status} ${res.statusText}`;
  try {
    const body = await res.json();
    if (body?.error) detail = typeof body.error === "string" ? body.error : JSON.stringify(body.error);
  } catch {
    /* ignore */
  }
  return new Error(detail);
}

// ===== 認証(トークンは localStorage 保持) =====
const TOKEN_KEY = "kiraku_auth";

export type AuthSession = { token: string; user_id: string; user_name: string };

export function getSession(): AuthSession | null {
  if (typeof window === "undefined") return null;
  const raw = window.localStorage.getItem(TOKEN_KEY);
  return raw ? (JSON.parse(raw) as AuthSession) : null;
}

export function setSession(s: AuthSession): void {
  window.localStorage.setItem(TOKEN_KEY, JSON.stringify(s));
}

export function clearSession(): void {
  window.localStorage.removeItem(TOKEN_KEY);
}

function authHeader(): Record<string, string> {
  const s = getSession();
  return s ? { Authorization: `Bearer ${s.token}` } : {};
}

export async function signup(userName: string, password: string): Promise<AuthSession> {
  const res = await fetch(`${BASE_URL}/api/auth/signup`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ user_name: userName, password }),
  });
  if (!res.ok) throw await asError(res);
  const s = (await res.json()) as AuthSession;
  setSession(s);
  return s;
}

export async function login(userName: string, password: string): Promise<AuthSession> {
  const res = await fetch(`${BASE_URL}/api/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ user_name: userName, password }),
  });
  if (!res.ok) throw await asError(res);
  const s = (await res.json()) as AuthSession;
  setSession(s);
  return s;
}

export async function createUser(userName: string): Promise<User> {
  const res = await fetch(`${BASE_URL}/api/users`, {
    method: "POST",
    headers: { "Content-Type": "application/json", ...authHeader() },
    body: JSON.stringify({ user_name: userName }),
  });
  if (!res.ok) throw await asError(res);
  return res.json();
}

export async function getUser(userId: string): Promise<User> {
  const res = await fetch(`${BASE_URL}/api/users/${userId}`, {
    headers: { ...authHeader() },
  });
  if (!res.ok) throw await asError(res);
  return res.json();
}

export async function measure(
  userId: string,
  image: Blob,
  calibration: Calibration,
  filename = "hand.jpg",
): Promise<MeasureResult> {
  const form = new FormData();
  form.append("image", image, filename);
  if (calibration.kind === "card") form.append("use_card", "true");
  else if (calibration.kind === "coin") form.append("use_coin", "true");
  else form.append("middle_finger_length_mm", String(calibration.middleFingerLengthMm));

  const res = await fetch(`${BASE_URL}/api/users/${userId}/measure`, {
    method: "POST",
    headers: { ...authHeader() },
    body: form,
  });
  if (!res.ok) throw await asError(res);
  return res.json();
}

export async function setActualRingSize(
  recordId: string,
  finger: FingerName,
  actualRingSizeJp: number,
): Promise<void> {
  const res = await fetch(`${BASE_URL}/api/records/${recordId}/actual`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json", ...authHeader() },
    body: JSON.stringify({ finger, actual_ring_size_jp: actualRingSizeJp }),
  });
  if (!res.ok) throw await asError(res);
}

export async function calibrationReport(): Promise<CalibrationReport> {
  const res = await fetch(`${BASE_URL}/api/calibration/report`);
  if (!res.ok) throw await asError(res);
  return res.json();
}

export async function recordTryOn(
  userId: string,
  ringId: string,
  finger: FingerName,
): Promise<void> {
  const res = await fetch(`${BASE_URL}/api/users/${userId}/tryons`, {
    method: "POST",
    headers: { "Content-Type": "application/json", ...authHeader() },
    body: JSON.stringify({ ring_id: ringId, finger }),
  });
  if (!res.ok) throw await asError(res);
}

export type RingAppearanceInput = {
  metal: string;
  metalDark: string;
  gem: string;
};

export type RingPlacementInput = {
  centerX: number;
  centerY: number;
  widthRatio: number;
  angleDeg: number;
};

// 手画像にリングを合成した PNG の Blob URL を返す(Go→ai_service)。
export type GenerateMode = "composite" | "photoreal";

export async function generateTryOn(
  image: Blob,
  placement: RingPlacementInput,
  appearance: RingAppearanceInput,
  mode: GenerateMode = "composite",
  filename = "hand.jpg",
): Promise<string> {
  const form = new FormData();
  form.append("image", image, filename);
  form.append("center_x", String(placement.centerX));
  form.append("center_y", String(placement.centerY));
  form.append("width_ratio", String(placement.widthRatio));
  form.append("angle_deg", String(placement.angleDeg));
  form.append("metal", appearance.metal);
  form.append("metal_dark", appearance.metalDark);
  form.append("gem", appearance.gem);
  form.append("mode", mode);

  const res = await fetch(`${BASE_URL}/api/tryon/generate`, {
    method: "POST",
    headers: { ...authHeader() },
    body: form,
  });
  if (!res.ok) throw await asError(res);
  const blob = await res.blob();
  return URL.createObjectURL(blob);
}
