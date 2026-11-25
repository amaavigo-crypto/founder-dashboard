import type { Kpi } from "./types";

export function inr(n: number | null | undefined): string {
  if (n === null || n === undefined) return "—";
  const a = Math.abs(n);
  const sign = n < 0 ? "-" : "";
  if (a >= 1e7) return `${sign}₹${(a / 1e7).toFixed(1)}Cr`;
  if (a >= 1e5) return `${sign}₹${(a / 1e5).toFixed(1)}L`;
  if (a >= 1e3) return `${sign}₹${(a / 1e3).toFixed(1)}K`;
  return `${sign}₹${Math.round(a)}`;
}

export function num(n: number | null | undefined): string {
  return n === null || n === undefined ? "—" : Math.round(n).toLocaleString("en-IN");
}

export function value(k: Kpi): string {
  if (k.kind === "money") return inr(k.value);
  if (k.kind === "percent") return k.value === null ? "—" : `${k.value.toFixed(k.value >= 99 ? 1 : 0)}%`;
  return num(k.value);
}

export function delta(k: Kpi): { text: string; tone: "up" | "down" | "flat" } | null {
  if (k.value === null || k.previous === null) return null;
  const diff = k.value - k.previous;
  const mode = k.delta_mode ?? "pct";
  let text: string;
  if (mode === "abs") text = diff === 0 ? "No change" : `${diff > 0 ? "+" : ""}${Math.round(diff)}`;
  else if (mode === "pts") text = diff === 0 ? "No change" : `${diff > 0 ? "+" : ""}${diff.toFixed(1)} pts`;
  else if (k.previous === 0) text = k.value === 0 ? "No change" : "New";
  else {
    const p = (diff / Math.abs(k.previous)) * 100;
    text = Math.abs(p) < 0.05 ? "No change" : `${p > 0 ? "+" : ""}${p.toFixed(1)}%`;
  }
  if (diff === 0 || text === "No change") return { text, tone: "flat" };
  const good = (k.good_when ?? "up") === "up" ? diff > 0 : diff < 0;
  return { text, tone: good ? "up" : "down" };
}

export function syncedLabel(iso: string | null): string {
  if (!iso) return "Not synced yet";
  const t = new Date(iso).toLocaleTimeString("en-IN", { hour: "2-digit", minute: "2-digit", hour12: false, timeZone: "Asia/Kolkata" });
  return `Synced ${t}`;
}

export function today(): string {
  return new Date().toLocaleDateString("en-IN", { weekday: "long", day: "numeric", month: "long", timeZone: "Asia/Kolkata" });
}
