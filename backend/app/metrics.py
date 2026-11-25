"""Turns stored snapshots into the numbers each dashboard page shows."""
from bisect import bisect_right
from collections import defaultdict
from datetime import date, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from .models import ManualMoney, Project, Snapshot
from .puller import today

RANGES = {"7d": 7, "30d": 30, "90d": 90}
COST_KEYS = ("ai", "hosting", "messaging", "other")
LEVEL_RANK = {"critical": 0, "warn": 1, "info": 2}


class Series:
    """All snapshots of one project, ordered by day, with nearest-earlier lookup."""

    def __init__(self, snaps: list[Snapshot]):
        self.days = [s.day for s in snaps]
        self.payloads = [s.payload for s in snaps]
        self.by_day = dict(zip(self.days, self.payloads))
        self.created = [s.created_at for s in snaps]

    def at(self, day: date) -> dict | None:
        i = bisect_right(self.days, day) - 1
        return self.payloads[i] if i >= 0 else None

    def latest(self) -> dict | None:
        return self.payloads[-1] if self.payloads else None


def _empty_day() -> dict:
    return {"revenue": 0.0, **{k: 0.0 for k in COST_KEYS}}


def load(db: Session, project: Project) -> tuple[Series, dict[date, dict]]:
    snaps = db.scalars(select(Snapshot).where(Snapshot.project_id == project.id).order_by(Snapshot.day)).all()
    days: dict[date, dict] = defaultdict(_empty_day)
    for s in snaps:
        m = s.payload.get("money")
        if m:
            d = days[s.day]
            d["revenue"] += m.get("revenue", 0) or 0
            for k in COST_KEYS:
                d[k] += (m.get("cost") or {}).get(k, 0) or 0
    for r in db.scalars(select(ManualMoney).where(ManualMoney.project_id == project.id)):
        d = days[r.day]
        d["revenue"] += r.revenue
        for k in COST_KEYS:
            d[k] += getattr(r, k)
    return Series(snaps), days


def total(days: dict[date, dict], start: date, end: date) -> dict:
    out = _empty_day()
    for day, v in days.items():
        if start <= day <= end:
            for k, x in v.items():
                out[k] += x
    out["cost"] = sum(out[k] for k in COST_KEYS)
    out["profit"] = out["revenue"] - out["cost"]
    return out


def window(rng: str) -> tuple[int, date, date, date, date]:
    n = RANGES.get(rng, 30)
    end = today()
    start = end - timedelta(days=n - 1)
    return n, start, end, start - timedelta(days=n), start - timedelta(days=1)


def buckets(start: date, n: int, k: int = 8) -> list[tuple[date, date]]:
    k = min(k, n)
    out = []
    for i in range(k):
        a, b = i * n // k, (i + 1) * n // k - 1
        out.append((start + timedelta(days=a), start + timedelta(days=b)))
    return out


def status_for(project: Project, latest: dict | None) -> tuple[str, str]:
    if project.last_pull_error:
        return "Sync failing", "warn"
    if not latest:
        return "No data yet", "muted"
    att = latest.get("attention", [])
    crit = [a for a in att if a["level"] == "critical"]
    if crit:
        return f"{len(crit)} critical", "critical"
    n = len([a for a in att if a["level"] == "warn"])
    if n:
        return f"{n} item{'s' if n > 1 else ''}", "warn"
    return "Healthy", "good"


def _kpi(key, label, value, previous, kind, series, delta_mode="pct", good_when="up"):
    return {"key": key, "label": label, "value": value, "previous": previous, "kind": kind,
            "delta_mode": delta_mode, "good_when": good_when, "series": series}


def _all(db: Session) -> list[tuple[Project, Series, dict]]:
    projects = db.scalars(select(Project).where(Project.active).order_by(Project.id)).all()
    return [(p, *load(db, p)) for p in projects]


def _sum_pt(rows, day, fn) -> float:
    return sum(fn(pl) if (pl := s.at(day)) else 0 for _, s, _ in rows)


def _attention(rows) -> list[dict]:
    items = []
    for p, s, _ in rows:
        if p.last_pull_error:
            items.append({"level": "warn", "title": "Metrics sync is failing", "project": p.name})
        for a in (s.latest() or {}).get("attention", []):
            items.append({"level": a["level"], "title": a["title"], "project": p.name})
    return sorted(items, key=lambda a: LEVEL_RANK[a["level"]])[:8]


def overview(db: Session, rng: str) -> dict:
    n, start, end, pstart, pend = window(rng)
    rows = _all(db)
    cur = {"revenue": 0.0, "cost": 0.0, "profit": 0.0}
    prev = dict(cur)
    for _, _, days in rows:
        for target, (a, b) in ((cur, (start, end)), (prev, (pstart, pend))):
            t = total(days, a, b)
            for k in cur:
                target[k] += t[k]
    bks = buckets(start, n)

    def money_series(key):
        return [sum(total(d, a, b)[key] for _, _, d in rows) for a, b in bks]

    def pt_series(fn):
        return [_sum_pt(rows, b, fn) for _, b in bks]

    cust = lambda pl: pl["customers"]["total"]  # noqa: E731
    mau = lambda pl: pl["users"]["active_monthly"]  # noqa: E731
    kpis = [
        _kpi("revenue", "Revenue", cur["revenue"], prev["revenue"], "money", money_series("revenue")),
        _kpi("customers", "Active customers", _sum_pt(rows, end, cust), _sum_pt(rows, pend, cust), "count",
             pt_series(cust), delta_mode="abs"),
        _kpi("users", "Active users", _sum_pt(rows, end, mau), _sum_pt(rows, pend, mau), "count", pt_series(mau)),
        _kpi("profit", "Profit", cur["profit"], prev["profit"], "money", money_series("profit")),
    ]

    months = []
    first = date(end.year, end.month, 1)
    starts = []
    for i in range(5, -1, -1):
        y, m = first.year, first.month - i
        while m <= 0:
            y, m = y - 1, m + 12
        starts.append(date(y, m, 1))
    for i, ms in enumerate(starts):
        me = (starts[i + 1] - timedelta(days=1)) if i + 1 < len(starts) else end
        rev = sum(total(d, ms, me)["revenue"] for _, _, d in rows)
        cost = sum(total(d, ms, me)["cost"] for _, _, d in rows)
        months.append({"label": ms.strftime("%b"), "revenue": rev, "cost": cost})

    projects = []
    synced = None
    for p, s, _ in rows:
        latest = s.latest()
        label, tone = status_for(p, latest)
        headline = (latest or {}).get("headline") or []
        if not headline and latest:
            headline = [{"label": latest["labels"]["customers"], "value": str(latest["customers"]["total"])},
                        {"label": "Active users", "value": str(latest["users"]["active_monthly"])}]
        stamp = p.last_pull_at or (s.created[-1] if s.created else None)
        if stamp and (synced is None or stamp > synced):
            synced = stamp
        projects.append({"id": p.id, "name": p.name, "color": p.color, "status": label, "tone": tone,
                         "headline": headline, "synced_at": stamp.isoformat() if stamp else None})
    return {"range": rng if rng in RANGES else "30d", "synced_at": synced.isoformat() if synced else None,
            "has_sample": any(p.is_sample for p, _, _ in rows), "kpis": kpis, "months": months,
            "projects": projects, "attention": _attention(rows)}


def project_list(db: Session) -> list[dict]:
    return [{"id": p.id, "name": p.name, "color": p.color} for p, _, _ in _all(db)]


def project_detail(db: Session, project: Project, rng: str) -> dict:
    n, start, end, pstart, pend = window(rng)
    s, days = load(db, project)
    latest = s.latest()
    labels = (latest or {}).get("labels", {"customers": "Customers", "size": "Users", "trend": "Daily active users"})
    t_cur, t_prev = total(days, start, end), total(days, pstart, pend)
    prev_pl = s.at(pend)

    def val(pl, f):
        return f(pl) if pl else 0

    tiles = [
        {"label": labels["customers"], "value": val(latest, lambda p: p["customers"]["total"]),
         "previous": val(prev_pl, lambda p: p["customers"]["total"]), "kind": "count", "delta_mode": "abs"},
        {"label": "Active users", "value": val(latest, lambda p: p["users"]["active_monthly"]),
         "previous": val(prev_pl, lambda p: p["users"]["active_monthly"]), "kind": "count", "delta_mode": "pct"},
        {"label": "Revenue", "value": t_cur["revenue"], "previous": t_prev["revenue"], "kind": "money",
         "delta_mode": "pct"},
        {"label": "Uptime", "value": (latest or {}).get("health", {}).get("uptime_pct"), "previous": None,
         "kind": "percent", "delta_mode": "pct"},
    ]
    trend = []
    for i in range(n):
        d = start + timedelta(days=i)
        pl = s.by_day.get(d)
        v = None
        if pl:
            v = pl.get("trend_value")
            v = pl["users"]["active_daily"] if v is None else v
        trend.append({"date": d.isoformat(), "value": v})
    status_label, tone = status_for(project, latest)
    return {"project": {"id": project.id, "name": project.name, "color": project.color,
                        "is_sample": project.is_sample, "status": status_label, "tone": tone,
                        "last_pull_error": project.last_pull_error},
            "labels": labels, "tiles": tiles, "trend": trend,
            "panel": (latest or {}).get("panel"), "customers": (latest or {}).get("customers_list", []),
            "attention": (latest or {}).get("attention", [])}


def money(db: Session, rng: str) -> dict:
    n, start, end, pstart, pend = window(rng)
    rows = _all(db)
    cur, prev = _empty_day(), _empty_day()
    for t in (cur, prev):
        t.update(cost=0.0, profit=0.0)
    projects = []
    for p, s, days in rows:
        c, pv = total(days, start, end), total(days, pstart, pend)
        for k in cur:
            cur[k] += c[k]
            prev[k] += pv[k]
        parts = sorted(({"label": k.title(), "value": c[k]} for k in COST_KEYS if c[k] > 0),
                       key=lambda x: -x["value"])
        projects.append({"id": p.id, "name": p.name, "color": p.color, "revenue": c["revenue"], "cost": c["cost"],
                         "profit": c["profit"], "margin": (c["profit"] / c["revenue"] * 100) if c["revenue"] else None,
                         "parts": parts, "reports_money": any(d["revenue"] or d["cost"] for d in days.values()) if days else False})
    margin = lambda t: (t["profit"] / t["revenue"] * 100) if t["revenue"] else None  # noqa: E731
    tiles = [
        {"label": "Revenue", "value": cur["revenue"], "previous": prev["revenue"], "kind": "money", "good_when": "up"},
        {"label": "Cost", "value": cur["cost"], "previous": prev["cost"], "kind": "money", "good_when": "down"},
        {"label": "Profit", "value": cur["profit"], "previous": prev["profit"], "kind": "money", "good_when": "up"},
        {"label": "Margin", "value": margin(cur), "previous": margin(prev), "kind": "percent", "good_when": "up",
         "delta_mode": "pts"},
    ]
    ai: dict[tuple[str, str], float] = defaultdict(float)
    for p, s, _ in rows:
        for r in (s.latest() or {}).get("ai_cost_by_customer", []):
            ai[(p.name, r["name"])] += r["cost"]
    top = sorted(ai.items(), key=lambda kv: -kv[1])[:6]
    return {"range": rng if rng in RANGES else "30d", "tiles": tiles, "projects": projects,
            "ai_by_customer": [{"project": k[0], "name": k[1], "cost": v} for k, v in top],
            "has_sample": any(p.is_sample for p, _, _ in rows)}
