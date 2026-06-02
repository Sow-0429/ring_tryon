import "./globals.css";
import type { Metadata } from "next";
import type { ReactNode } from "react";
import Link from "next/link";
import AuthStatus from "@/components/AuthStatus";

export const metadata: Metadata = {
  title: "KIRAKU — 指輪の号数計測と試着",
  description:
    "手の写真から指の号数を計測し、指輪を試着できる。クリームとガラスの上質な体験。",
};

const links = [
  { href: "/", label: "ホーム" },
  { href: "/sizing", label: "号数計測" },
  { href: "/try-on", label: "リアル試着" },
  { href: "/generate", label: "試着画像生成" },
];

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="ja">
      <body>
        <nav className="nav glass">
          <Link href="/" className="brand">
            KIRAKU
            <small>FINE JEWELRY</small>
          </Link>
          <div className="nav-links">
            {links.map((l) => (
              <Link key={l.href} href={l.href}>
                {l.label}
              </Link>
            ))}
            <AuthStatus />
          </div>
        </nav>
        {children}
      </body>
    </html>
  );
}
