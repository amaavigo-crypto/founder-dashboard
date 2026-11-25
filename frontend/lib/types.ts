export type Tone = "good" | "warn" | "critical" | "muted";

export type Kpi = {
  key?: string;
  label: string;
  value: number | null;
  previous: number | null;
  kind: "money" | "count" | "percent";
  delta_mode?: "pct" | "abs" | "pts";
  good_when?: "up" | "down";
  series?: number[];
};

export type Stat = { label: string; value: string };
export type Attention = { level: "info" | "warn" | "critical"; title: string; project?: string };

export type Overview = {
  range: string;
  synced_at: string | null;
  has_sample: boolean;
  kpis: Kpi[];
  months: { label: string; revenue: number; cost: number }[];
  projects: { id: number; name: string; color: string; status: string; tone: Tone; headline: Stat[] }[];
  attention: Attention[];
};

export type ProjectItem = { id: number; name: string; color: string };

export type ProjectDetail = {
  project: { id: number; name: string; color: string; is_sample: boolean; status: string; tone: Tone; last_pull_error: string | null };
  labels: { customers: string; size: string; trend: string };
  tiles: Kpi[];
  trend: { date: string; value: number | null }[];
  panel: { title: string; rows: { label: string; value: string; pct: number }[] } | null;
  customers: { name: string; plan: string; size: string; last_active: string; revenue: string; status: "active" | "quiet" | "at_risk" }[];
};

export type Money = {
  range: string;
  has_sample: boolean;
  tiles: Kpi[];
  projects: { id: number; name: string; color: string; revenue: number; cost: number; profit: number; margin: number | null; parts: { label: string; value: number }[] }[];
  ai_by_customer: { project: string; name: string; cost: number }[];
};
