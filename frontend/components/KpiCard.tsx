import { delta, value } from "@/lib/format";
import type { Kpi } from "@/lib/types";
import Sparkline from "./Sparkline";

export default function KpiCard({ kpi, suffix = "vs previous" }: { kpi: Kpi; suffix?: string }) {
  const d = delta(kpi);
  return (
    <div className="card kpi">
      <div className="label">{kpi.label}</div>
      <div className="between">
        <div className="big">{value(kpi)}</div>
        {kpi.series && <Sparkline data={kpi.series} />}
      </div>
      {d && (
        <div className={`delta ${d.tone}`}>
          {d.text} {d.tone !== "flat" || d.text !== "No change" ? <span>{suffix}</span> : null}
        </div>
      )}
    </div>
  );
}
