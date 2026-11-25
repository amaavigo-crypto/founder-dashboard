import Link from "next/link";
import KpiCard from "@/components/KpiCard";
import RangeToggle from "@/components/RangeToggle";
import { api, parseRange } from "@/lib/api";
import { syncedLabel, today } from "@/lib/format";
import type { Overview } from "@/lib/types";

const DOT = { critical: "var(--crit)", warn: "var(--warn)", info: "var(--accent)" } as const;

export default async function OverviewPage({ searchParams }: { searchParams: Promise<{ range?: string }> }) {
  const range = parseRange((await searchParams).range);
  const d = await api<Overview>(`/api/overview?range=${range}`);
  const maxM = Math.max(1, ...d.months.map((m) => Math.max(m.revenue, m.cost)));
  const lakh = (n: number) => (n / 1e5).toFixed(1);

  return (
    <main className="main">
      <header className="head">
        <div>
          <div className="eyebrow">{today()}</div>
          <h1>Business health</h1>
        </div>
        <div className="row">
          <span className="chip">{syncedLabel(d.synced_at)}{d.has_sample ? " · sample data" : ""}</span>
          <RangeToggle current={range} />
        </div>
      </header>

      <section className="grid">{d.kpis.map((k) => <KpiCard key={k.key} kpi={k} />)}</section>

      <section className="section">
        <div className="between-row"><h2>Projects</h2><Link href="/projects" className="small" style={{ color: "var(--accent)", fontWeight: 500 }}>View all</Link></div>
        <div className="grid">
          {d.projects.map((p) => (
            <div key={p.id} className="card pcard">
              <div className="between-row">
                <div className="row" style={{ gap: 10 }}>
                  <span className="dot" style={{ background: p.color, width: 10, height: 10, borderRadius: 5 }} />
                  <b style={{ fontSize: 16 }}>{p.name}</b>
                </div>
                <span className={`pill t-${p.tone}`}><i />{p.status}</span>
              </div>
              <div className="stats">
                {p.headline.map((s) => (
                  <div key={s.label} className="stat"><div className="k">{s.label}</div><div className="v">{s.value}</div></div>
                ))}
              </div>
              <div className="between-row"><span className="small" style={{ fontSize: 13 }}>{syncedLabel(d.synced_at)}</span><Link href={`/projects/${p.id}`} style={{ fontSize: 13, fontWeight: 500 }}>Open</Link></div>
            </div>
          ))}
          <Link href="/projects/new" className="add"><b style={{ fontSize: 15 }}>Add a project</b><small>Paste its metrics URL and API key. It appears here on the next sync.</small></Link>
        </div>
      </section>

      <section className="grid">
        <div className="card" style={{ flex: "3 1 420px", minWidth: 0, display: "flex", flexDirection: "column", gap: 18 }}>
          <div className="between-row">
            <h2>Revenue and cost</h2>
            <div className="legend"><span><i style={{ background: "var(--bar)" }} />Revenue</span><span><i style={{ background: "var(--bar-3)" }} />Cost</span><span>₹ lakh</span></div>
          </div>
          <div className="bars">
            {d.months.map((m) => (
              <div key={m.label} className="mcol">
                <div style={{ fontSize: 12, fontWeight: 500, color: "var(--ink-2)" }}>{lakh(m.revenue)}</div>
                <div className="mpair">
                  <i style={{ background: "var(--bar)", height: Math.max(2, Math.round((m.revenue / maxM) * 164)) }} />
                  <i style={{ background: "var(--bar-3)", height: Math.max(2, Math.round((m.cost / maxM) * 164)) }} />
                </div>
                <div className="small">{m.label}</div>
              </div>
            ))}
          </div>
        </div>
        <div className="card" style={{ flex: "2 1 300px", minWidth: 0, display: "flex", flexDirection: "column", gap: 6 }}>
          <div className="between-row" style={{ marginBottom: 8 }}><h2>Needs attention</h2><span className="small">{d.attention.length} {d.attention.length === 1 ? "item" : "items"}</span></div>
          {d.attention.length === 0 && <div className="empty" style={{ padding: "24px 0" }}>Nothing needs you right now.</div>}
          {d.attention.map((a, i) => (
            <div key={i} className="alert">
              <span className="dot" style={{ background: DOT[a.level] }} />
              <div><b>{a.title}</b><span>{a.project}</span></div>
            </div>
          ))}
        </div>
      </section>
    </main>
  );
}
