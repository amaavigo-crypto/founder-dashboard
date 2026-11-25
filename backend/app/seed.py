"""Create the founder login and (optionally) two sample projects with 90 days of demo data.

    python -m app.seed              # founder + sample projects (first run only)
    python -m app.seed --no-sample  # founder only; add real projects through the API
"""
import argparse
import math
from datetime import timedelta

from sqlalchemy import select

from .config import settings
from .contract import MetricsPayload
from .db import Base, SessionLocal, engine
from .models import Founder, Project, Snapshot
from .puller import today
from .security import hash_password

DAYS = 90


def _hr(i: int, t: float, last: bool) -> dict:
    daily = round(380 + 260 * t + 40 * math.sin(i / 2.3))
    return {
        "labels": {"customers": "Companies", "size": "Employees", "trend": "Daily active users"},
        "customers": {"total": round(14 + 4 * t), "new": 1 if i % 22 == 0 else 0},
        "users": {"active_daily": daily, "active_weekly": round(daily * 2.6), "active_monthly": round(daily * 5.2)},
        "money": {"revenue": round(8000 + 4000 * t + 1500 * math.sin(i / 3)),
                  "cost": {"ai": round(200 + 100 * t), "hosting": 800, "other": 650}},
        "health": {"uptime_pct": 99.9, "errors": 3, "failed_jobs": 2 if last else 0},
        "attention": [{"level": "critical", "title": "2 nightly jobs failed"}] if last else [],
        "headline": [{"label": "Companies", "value": "18"}, {"label": "Employees managed", "value": "3,420"},
                     {"label": "Revenue", "value": "₹2.9L"}, {"label": "AI cost", "value": "₹6.1K"}],
        "panel": {"title": "Companies using each module", "rows": [
            {"label": "Leave and attendance", "value": "17 of 18", "pct": 94},
            {"label": "Payroll", "value": "11 of 18", "pct": 61},
            {"label": "Claims", "value": "8 of 18", "pct": 44},
            {"label": "AI agent", "value": "5 of 18", "pct": 28}]},
        "customers_list": [
            {"name": "Company A", "plan": "Growth", "size": "640", "last_active": "Today", "revenue": "₹48K"},
            {"name": "Company B", "plan": "Growth", "size": "410", "last_active": "Today", "revenue": "₹36K"},
            {"name": "Company C", "plan": "Starter", "size": "120", "last_active": "2 days ago", "revenue": "₹12K"},
            {"name": "Company D", "plan": "Growth", "size": "980", "last_active": "Today", "revenue": "₹62K"},
            {"name": "Company E", "plan": "Starter", "size": "75", "last_active": "9 days ago", "revenue": "₹9K",
             "status": "quiet"}],
        "ai_cost_by_customer": [{"name": "Company D", "cost": 3100}, {"name": "Company A", "cost": 2400},
                                {"name": "Company B", "cost": 1100}],
    }


def _lead(i: int, t: float, last: bool) -> dict:
    daily = round(60 + 25 * t + 12 * math.sin(i / 2.9 + 1.7))
    return {
        "labels": {"customers": "Tenants", "size": "Leads", "trend": "Leads captured per day"},
        "customers": {"total": 5 if t < 0.6 else 6, "new": 1 if i == 55 else 0},
        "users": {"active_daily": round(daily * 0.6), "active_weekly": round(daily * 2), "active_monthly": 520},
        "trend_value": daily,
        "money": {"revenue": round(4500 + 2500 * t + 900 * math.sin(i / 4)),
                  "cost": {"ai": round(350 + 120 * t), "messaging": round(900 + 700 * t), "hosting": 500}},
        "health": {"uptime_pct": 99.7, "errors": 5, "failed_jobs": 0},
        "attention": [{"level": "warn", "title": "WhatsApp token expires in 6 days"},
                      {"level": "warn", "title": "Messaging cost up 38% this week"}] if last else [],
        "headline": [{"label": "Tenants", "value": "6"}, {"label": "Leads", "value": "2,180"},
                     {"label": "Messages sent", "value": "9,640"}, {"label": "Revenue", "value": "₹1.9L"}],
        "panel": {"title": "Lead funnel this month", "rows": [
            {"label": "Leads", "value": "2,180", "pct": 100}, {"label": "Contacted", "value": "1,420", "pct": 65},
            {"label": "Replied", "value": "610", "pct": 28}, {"label": "Won", "value": "74", "pct": 4}]},
        "customers_list": [
            {"name": "Tenant A", "plan": "Pro", "size": "720", "last_active": "Today", "revenue": "₹52K"},
            {"name": "Tenant B", "plan": "Pro", "size": "540", "last_active": "Today", "revenue": "₹44K"},
            {"name": "Amaavigo", "plan": "Internal", "size": "480", "last_active": "Today", "revenue": "—",
             "status": "quiet"},
            {"name": "Tenant C", "plan": "Starter", "size": "260", "last_active": "3 days ago", "revenue": "₹14K"},
            {"name": "Tenant D", "plan": "Starter", "size": "180", "last_active": "6 days ago", "revenue": "₹8K",
             "status": "quiet"}],
        "ai_cost_by_customer": [{"name": "Tenant A", "cost": 6200}, {"name": "Tenant B", "cost": 1800}],
    }


def seed(sample: bool = True) -> None:
    Base.metadata.create_all(engine)
    with SessionLocal() as db:
        email = settings.founder_email.strip().lower()
        if not db.scalar(select(Founder).where(Founder.email == email)):
            db.add(Founder(email=email, password_hash=hash_password(settings.founder_password)))
        if sample and not db.scalar(select(Project)):
            specs = [("hr-portal", "HR Portal", "#6D5BD0", _hr), ("lead-gen", "Lead-Gen", "#0E9F8E", _lead)]
            for slug, name, color, make in specs:
                p = Project(slug=slug, name=name, color=color, is_sample=True)
                db.add(p)
                db.flush()
                for i in range(DAYS):
                    payload = MetricsPayload.model_validate(make(i, i / (DAYS - 1), i == DAYS - 1))
                    db.add(Snapshot(project_id=p.id, day=today() - timedelta(days=DAYS - 1 - i),
                                    payload=payload.model_dump(mode="json")))
        db.commit()


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-sample", action="store_true")
    seed(sample=not ap.parse_args().no_sample)
    print("Seeded.")
