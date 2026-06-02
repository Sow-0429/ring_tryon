import type { CSSProperties } from "react";

export type RingStyle = {
  id: string;
  name: string;
  metal: string;
  metalDark: string;
  gem: string;
};

export const RING_CATALOG: RingStyle[] = [
  { id: "gold-champagne", name: "シャンパンゴールド", metal: "#e7c98f", metalDark: "#b9975b", gem: "#fff6e0" },
  { id: "rose", name: "ローズゴールド", metal: "#e8b9a6", metalDark: "#c98a73", gem: "#ffd9cf" },
  { id: "platinum", name: "プラチナ", metal: "#e4e6ea", metalDark: "#a9adb6", gem: "#d8ecff" },
  { id: "emerald", name: "ゴールド × エメラルド", metal: "#e7c98f", metalDark: "#b9975b", gem: "#3da57a" },
];

/** 指に対し真上から見たリング(楕円バンド+ジェム)のSVG。 */
export function Ring({
  ring,
  width = 120,
  style,
}: {
  ring: RingStyle;
  width?: number;
  style?: CSSProperties;
}) {
  const h = width * 0.62;
  const gid = `m-${ring.id}`;
  const ggid = `g-${ring.id}`;
  return (
    <svg
      width={width}
      height={h}
      viewBox="0 0 120 74"
      style={style}
      aria-label={ring.name}
    >
      <defs>
        <linearGradient id={gid} x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor={ring.metal} />
          <stop offset="50%" stopColor={ring.metalDark} />
          <stop offset="100%" stopColor={ring.metal} />
        </linearGradient>
        <radialGradient id={ggid} cx="50%" cy="38%" r="65%">
          <stop offset="0%" stopColor="#ffffff" />
          <stop offset="45%" stopColor={ring.gem} />
          <stop offset="100%" stopColor={ring.metalDark} />
        </radialGradient>
      </defs>
      {/* バンド外周/内周で帯を表現 */}
      <ellipse cx="60" cy="42" rx="52" ry="28" fill="none" stroke={`url(#${gid})`} strokeWidth="11" />
      <ellipse cx="60" cy="42" rx="52" ry="28" fill="none" stroke="rgba(255,255,255,0.5)" strokeWidth="1.5" />
      {/* ジェム(石座+石) */}
      <circle cx="60" cy="13" r="13" fill={ring.metalDark} />
      <circle cx="60" cy="13" r="9.5" fill={`url(#${ggid})`} />
      <circle cx="56" cy="10" r="2.4" fill="rgba(255,255,255,0.85)" />
    </svg>
  );
}
