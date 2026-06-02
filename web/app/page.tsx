import Link from "next/link";
import { Ring, RING_CATALOG } from "@/components/Ring";

const features = [
  {
    href: "/sizing",
    title: "号数計測",
    desc: "手のひらを撮影するだけで、4本の指の号数を推定します。",
    badge: "MEASURE",
  },
  {
    href: "/try-on",
    title: "リアルタイム試着",
    desc: "カメラ越しに指輪を重ねて、着け心地の印象を確かめます。",
    badge: "TRY-ON",
  },
  {
    href: "/generate",
    title: "試着画像生成",
    desc: "あなたの手の写真に指輪を合成し、一枚の作品に。",
    badge: "GENERATE",
  },
];

export default function Home() {
  return (
    <main className="container">
      <section
        className="glass card"
        style={{ padding: "56px 40px", marginTop: 28, textAlign: "center" }}
      >
        <span className="pill">FINE JEWELRY EXPERIENCE</span>
        <h1 style={{ fontSize: 44, lineHeight: 1.2, margin: "18px 0 10px" }}>
          指先に、ぴたりと。
        </h1>
        <p className="muted" style={{ maxWidth: 520, margin: "0 auto 26px", fontSize: 16 }}>
          写真から号数を測り、試着して、生成する。
          クリームとガラスの質感で、指輪選びを上質な体験に。
        </p>
        <div style={{ display: "flex", gap: 12, justifyContent: "center", flexWrap: "wrap" }}>
          <Link href="/sizing" className="btn btn-primary">
            号数を計測する
          </Link>
          <Link href="/try-on" className="btn">
            試着してみる
          </Link>
        </div>
        <div style={{ display: "flex", gap: 18, justifyContent: "center", marginTop: 34 }}>
          {RING_CATALOG.map((r) => (
            <Ring key={r.id} ring={r} width={92} />
          ))}
        </div>
      </section>

      <section
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(240px, 1fr))",
          gap: 18,
          marginTop: 20,
          marginBottom: 40,
        }}
      >
        {features.map((f) => (
          <Link key={f.href} href={f.href} className="glass card" style={{ display: "block" }}>
            <span className="pill">{f.badge}</span>
            <h2 style={{ fontSize: 22, margin: "14px 0 8px" }}>{f.title}</h2>
            <p className="muted" style={{ margin: 0, fontSize: 14 }}>{f.desc}</p>
            <p style={{ marginTop: 16, color: "var(--gold-deep)", fontSize: 14 }}>
              ひらく →
            </p>
          </Link>
        ))}
      </section>
    </main>
  );
}
