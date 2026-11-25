import Link from "next/link";
import { notFound } from "next/navigation";
import KpiCard from "@/components/KpiCard";
import RangeToggle from "@/components/RangeToggle";
import { api, parseRange } from "@/lib/api";
import type { ProjectDetail, ProjectItem } from "@/lib/types";

const STATUS = { active: ["Active", "good"], quiet: ["Quiet", "warn"], at_risk: ["At risk", "critical"] } as const;

export default async function ProjectPage({
  params,
  searchParams,
}: {
  params: Promise<{ id: string }>;
  searchParams: Promise<{ range?: string }>;
}) {
  const { id } = await params;
  const range = parseRange((await searchParams).range);
  let d: ProjectDetail;
  try {
    d = await api<ProjectDetail>(`/api/projects/${Number(id)}?range=${range}`);
  } catch {
    notFound();
  }
  const projects = await api<ProjectItem[]>("/api/projects");
  const max = Math.max(1, ...d.trend.map((t) => t.value ?? 0));
  const first = d.trend[0]?.date, last = d.trend[d.trend.length - 1]?.date;
  const fmt = (iso?: string) => (iso ? new Date(iso + "T00:00:00").toLocaleDateString("en-IN", { day: "numeric", month: "short" }) : "");

  return (
    <main className="main">
      <header className="head">
        <div>
          <div className="eyebrow"><Link href="/">Overview</Link> / Projects</div>
          <h1>{d.project.name}</h1>
        </div>
        <div className="row">
          <nav className="tabs" aria-label="Projects">
            {projects.map((p) => (
              <Link key={p.id} href={`/projects/${p.id}?range=${range}`} aria-current={p.id === d.project.id}>{p.name}</Link>
            ))}
          </nav>
          <RangeToggle current={range} />
        </div>
      </header>

      {d.project.last_pull_error && <div className="err">The last sync failed: {d.project.last_pull_error}. Showing the most recent data we have.</div>}

      <section className="grid">{d.tiles.map((k) => <KpiCard key={k.label} kpi={k} suffix="vs previous" />)}</section>

      <section className="grid">
        <div className="card" style={{ flex: "3 1 420px", minWidth: 0, display: "flex", flexDirection: "column", gap: 18 }}>
          <div className="between-row"><h2>{d.labels.trend}</h2><span className="small">Last {d.trend.length} days</span></div>
          <div className="trend" role="img" aria-label={`${d.labels.trend}, last ${d.trend.length} days`}>
            {d.trend.map((t) => <i key={t.date} title={`${fmt(t.date)}: ${t.value ?? "no data"}`} style={{ height: Math.max(3, Math.round(((t.value ?? 0) / max) * 150)) }} />)}
          </div>
          <div className="axis"><span>{fmt(first)}</span><span>{fmt(last)}</span></div>
        </div>
        {d.panel && (
          <div className="card" style={{ flex: "2 1 300px", minWidth: 0, display: "flex", flexDirection: "column", gap: 18 }}>
            <h2>{d.panel.title}</h2>
            {d.panel.rows.map((r) => (
              <div key={r.label} className="mrow">
                <div><span style={{ color: "var(--ink-2)" }}>{r.label}</span><b>{r.value}</b></div>
                <div className="meter"><i style={{ width: `${r.pct}%` }} /></div>
              </div>
            ))}
          </div>
        )}
      </section>

      <section className="card" style={{ display: "flex", flexDirection: "column", gap: 8 }}>
        <div className="between-row"><h2>{d.labels.customers}</h2>{d.project.is_sample && <span className="small">Sample data</span>}</div>
        {d.customers.length === 0 ? <div className="empty">This product has not sent a customer list yet.</div> : (
          <div className="tablewrap">
            <table>
              <thead><tr><th>Name</th><th>Plan</th><th>{d.labels.size}</th><th>Last active</th><th className="r">Revenue</th><th className="r">Status</th></tr></thead>
              <tbody>
                {d.customers.map((c) => {
                  const [label, tone] = STATUS[c.status] ?? STATUS.active;
                  return (
                    <tr key={c.name}>
                      <td>{c.name}</td><td>{c.plan}</td><td>{c.size}</td><td>{c.last_active}</td>
                      <td className="r" style={{ fontWeight: 500, color: "var(--ink)" }}>{c.revenue}</td>
                      <td className="r"><span className={`pill t-${tone}`}>{label}</span></td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </main>
  );
}
