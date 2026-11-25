import KpiCard from "@/components/KpiCard";
import RangeToggle from "@/components/RangeToggle";
import { api, parseRange } from "@/lib/api";
import { inr } from "@/lib/format";
import type { Money } from "@/lib/types";

const SHADES = ["var(--bar)", "var(--bar-2)", "var(--bar-3)", "#e1e6fb"];

export default async function MoneyPage({ searchParams }: { searchParams: Promise<{ range?: string }> }) {
  const range = parseRange((await searchParams).range);
  const d = await api<Money>(`/api/money?range=${range}`);
  const maxAi = Math.max(1, ...d.ai_by_customer.map((r) => r.cost));
  const days = { "7d": "Last 7 days", "30d": "Last 30 days", "90d": "Last 90 days" }[range];

  return (
    <main className="main">
      <header className="head">
        <div>
          <div className="eyebrow">{days} · all projects</div>
          <h1>Money</h1>
        </div>
        <div className="row">
          {d.has_sample && <span className="chip">Sample data</span>}
          <RangeToggle current={range} />
        </div>
      </header>

      <section className="grid">{d.tiles.map((k) => <KpiCard key={k.label} kpi={k} />)}</section>

      <section className="section">
        <h2>Profit by project</h2>
        <div className="grid">
          {d.projects.map((p) => {
            const none = p.revenue === 0 && p.cost === 0;
            return (
              <div key={p.id} className="card pcard" style={{ flex: "1 1 380px", minWidth: 0 }}>
                <div className="between-row">
                  <div className="row" style={{ gap: 10 }}><span className="dot" style={{ background: p.color, width: 10, height: 10, borderRadius: 5 }} /><b style={{ fontSize: 16 }}>{p.name}</b></div>
                  {p.margin !== null && <span className="small" style={{ fontSize: 13 }}>Margin <b style={{ color: "var(--ink)" }}>{Math.round(p.margin)}%</b></span>}
                </div>
                {none ? (
                  <div className="small" style={{ fontSize: 13 }}>No revenue or cost reported for this period. If this product does not send money yet, add it by hand through the API.</div>
                ) : (
                  <>
                    <div className="row" style={{ gap: 32 }}>
                      {[["Revenue", p.revenue, ""], ["Cost", p.cost, ""], ["Profit", p.profit, "var(--good)"]].map(([l, v, c]) => (
                        <div key={l as string}><div className="small">{l}</div><div style={{ marginTop: 4, fontSize: 22, fontWeight: 600, color: (c as string) || undefined }}>{inr(v as number)}</div></div>
                      ))}
                    </div>
                    <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
                      <div className="small">Where the cost goes</div>
                      <div className="stack">{p.parts.map((c, i) => <i key={c.label} style={{ background: SHADES[i % 4], flex: `${c.value} 1 0` }} />)}</div>
                      <div className="legend" style={{ color: "var(--ink-2)" }}>
                        {p.parts.map((c, i) => <span key={c.label}><i style={{ background: SHADES[i % 4], width: 8, height: 8, borderRadius: 2 }} />{c.label} {inr(c.value)}</span>)}
                      </div>
                    </div>
                  </>
                )}
              </div>
            );
          })}
        </div>
      </section>

      <section className="card" style={{ display: "flex", flexDirection: "column", gap: 16 }}>
        <div className="between-row"><h2>AI cost by customer</h2><span className="small">Last 30 days, as reported by each product</span></div>
        {d.ai_by_customer.length === 0 && <div className="empty">No AI cost reported yet.</div>}
        {d.ai_by_customer.map((r) => (
          <div key={`${r.project}-${r.name}`} className="aibar">
            <div className="name">{r.name} <small>{r.project}</small></div>
            <div className="meter"><i style={{ width: `${(r.cost / maxAi) * 100}%` }} /></div>
            <div className="amt">{inr(r.cost)}</div>
          </div>
        ))}
      </section>
    </main>
  );
}
