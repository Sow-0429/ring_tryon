"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { clearSession, getSession, login, signup, type AuthSession } from "@/lib/api";

export default function AuthPage() {
  const router = useRouter();
  const [mode, setMode] = useState<"login" | "signup">("login");
  const [userName, setUserName] = useState("");
  const [password, setPassword] = useState("");
  const [session, setSessionState] = useState<AuthSession | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => setSessionState(getSession()), []);

  function submit() {
    setBusy(true);
    setError(null);
    const fn = mode === "login" ? login : signup;
    fn(userName.trim(), password)
      .then((s) => {
        setSessionState(s);
        router.push("/sizing");
      })
      .catch((e: unknown) => setError(e instanceof Error ? e.message : String(e)))
      .finally(() => setBusy(false));
  }

  if (session) {
    return (
      <main className="container" style={{ maxWidth: 480, paddingTop: 28 }}>
        <section className="glass card">
          <h1 style={{ fontSize: 24, marginTop: 0 }}>ログイン中</h1>
          <p className="muted">{session.user_name} としてログインしています。</p>
          <button
            className="btn"
            onClick={() => {
              clearSession();
              setSessionState(null);
            }}
          >
            ログアウト
          </button>
        </section>
      </main>
    );
  }

  return (
    <main className="container" style={{ maxWidth: 480, paddingTop: 28 }}>
      <span className="pill">ACCOUNT</span>
      <h1 style={{ fontSize: 28, margin: "12px 0 18px" }}>
        {mode === "login" ? "ログイン" : "アカウント作成"}
      </h1>
      {error && <div className="error" style={{ marginBottom: 14 }}>{error}</div>}
      <section className="glass card" style={{ display: "grid", gap: 12 }}>
        <input
          className="field"
          placeholder="ユーザー名"
          value={userName}
          onChange={(e) => setUserName(e.target.value)}
          disabled={busy}
        />
        <input
          className="field"
          type="password"
          placeholder="パスワード"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          disabled={busy}
        />
        <button
          className="btn btn-primary"
          onClick={submit}
          disabled={busy || !userName || !password}
        >
          {mode === "login" ? "ログイン" : "登録してはじめる"}
        </button>
        <button
          className="btn"
          onClick={() => setMode(mode === "login" ? "signup" : "login")}
          disabled={busy}
          style={{ background: "transparent", border: "none", color: "var(--gold-deep)" }}
        >
          {mode === "login" ? "アカウントを作成する" : "ログインに戻る"}
        </button>
      </section>
    </main>
  );
}
