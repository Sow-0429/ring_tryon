// Go API クライアント(React Native)。Web 版 lib/api.ts と同契約。
// 端末からは localhost 不可。EXPO_PUBLIC_API_BASE_URL に LAN IP を設定する。

const BASE_URL = process.env.EXPO_PUBLIC_API_BASE_URL ?? "http://localhost:8080";

export type Hand = {
  index_jp_size: number;
  middle_jp_size: number;
  ring_jp_size: number;
  pinky_jp_size: number;
};

export type MeasureResult = {
  user_id: string;
  user_name: string;
  hand: Hand;
  record_id: string;
};

export type AuthSession = { token: string; user_id: string; user_name: string };

let session: AuthSession | null = null;
export function setSession(s: AuthSession | null) {
  session = s;
}
export function currentSession(): AuthSession | null {
  return session;
}

function authHeader(): Record<string, string> {
  return session ? { Authorization: `Bearer ${session.token}` } : {};
}

async function asError(res: Response): Promise<Error> {
  let detail = `${res.status}`;
  try {
    const body = await res.json();
    if (body?.error) detail = typeof body.error === "string" ? body.error : JSON.stringify(body.error);
  } catch {
    /* ignore */
  }
  return new Error(detail);
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

export type Calibration =
  | { kind: "card" }
  | { kind: "coin" }
  | { kind: "finger"; middleFingerLengthMm: number };

// RN の FormData は { uri, name, type } のファイル指定を受け付ける。
export async function measure(
  userId: string,
  imageUri: string,
  calibration: Calibration,
): Promise<MeasureResult> {
  const form = new FormData();
  // @ts-expect-error React Native の FormData ファイル形式
  form.append("image", { uri: imageUri, name: "hand.jpg", type: "image/jpeg" });
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
