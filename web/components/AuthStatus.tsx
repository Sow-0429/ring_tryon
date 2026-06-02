"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { getSession, type AuthSession } from "@/lib/api";

// ナビ右端のログイン状態表示(クライアント)。
export default function AuthStatus() {
  const [session, setSession] = useState<AuthSession | null>(null);

  useEffect(() => {
    setSession(getSession());
    const onFocus = () => setSession(getSession());
    window.addEventListener("focus", onFocus);
    return () => window.removeEventListener("focus", onFocus);
  }, []);

  return (
    <Link href="/auth" style={{ color: session ? "var(--gold-deep)" : undefined }}>
      {session ? session.user_name : "ログイン"}
    </Link>
  );
}
