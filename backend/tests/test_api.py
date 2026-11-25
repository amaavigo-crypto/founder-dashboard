import os
import tempfile

os.environ["DATABASE_URL"] = f"sqlite:///{tempfile.mkdtemp()}/test.db"
os.environ["FOUNDER_EMAIL"] = "f@example.com"
os.environ["FOUNDER_PASSWORD"] = "pw12345"
os.environ["PULL_SECRET"] = "sekret"
os.environ["CRON_SECRET"] = "cronsekret"

import httpx  # noqa: E402
import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402
from app.seed import seed  # noqa: E402


@pytest.fixture(scope="module")
def client():
    seed()
    with TestClient(app) as c:
        yield c


@pytest.fixture(scope="module")
def auth(client):
    r = client.post("/api/auth/login", json={"email": "f@example.com", "password": "pw12345"})
    assert r.status_code == 200
    return {"Authorization": f"Bearer {r.json()['token']}"}


def test_requires_login(client):
    assert client.get("/api/overview").status_code == 401
    bad = client.post("/api/auth/login", json={"email": "f@example.com", "password": "nope"})
    assert bad.status_code == 401


def test_overview(client, auth):
    d = client.get("/api/overview?range=30d", headers=auth).json()
    assert [k["key"] for k in d["kpis"]] == ["revenue", "customers", "users", "profit"]
    assert all(len(k["series"]) == 8 for k in d["kpis"])
    assert d["kpis"][1]["value"] == 24  # 18 companies + 6 tenants
    assert len(d["projects"]) == 2 and len(d["months"]) == 6 and d["has_sample"]
    assert d["attention"][0]["level"] == "critical"
    seven = client.get("/api/overview?range=7d", headers=auth).json()
    assert len(seven["kpis"][0]["series"]) == 7
    assert seven["kpis"][0]["value"] < d["kpis"][0]["value"]


def test_profit_is_revenue_minus_cost(client, auth):
    d = client.get("/api/money?range=30d", headers=auth).json()
    rev, cost, profit = (t["value"] for t in d["tiles"][:3])
    assert abs(rev - cost - profit) < 0.01
    assert sum(p["revenue"] for p in d["projects"]) == pytest.approx(rev)


def test_project_detail(client, auth):
    pid = client.get("/api/projects", headers=auth).json()[1]["id"]
    d = client.get(f"/api/projects/{pid}?range=30d", headers=auth).json()
    assert d["labels"]["customers"] == "Tenants" and len(d["trend"]) == 30
    assert d["panel"]["title"].startswith("Lead funnel") and len(d["customers"]) == 5
    assert client.get("/api/projects/9999", headers=auth).status_code == 404


def test_manual_money_and_new_project(client, auth):
    r = client.post("/api/projects", headers=auth, json={"slug": "vedessa", "name": "Vedessa"})
    assert r.status_code == 201
    pid = r.json()["id"]
    assert client.post("/api/projects", headers=auth, json={"slug": "vedessa", "name": "x"}).status_code == 409
    before = client.get("/api/money?range=30d", headers=auth).json()["tiles"][0]["value"]
    client.post("/api/manual-money", headers=auth, json={"project_id": pid, "day": __import__("datetime").date.today().isoformat(), "revenue": 5000})
    after = client.get("/api/money?range=30d", headers=auth).json()["tiles"][0]["value"]
    assert after - before == pytest.approx(5000)


def test_pull_stores_snapshot_and_reports_errors(client, auth):
    from app.db import SessionLocal
    from app.models import Project
    from app.puller import pull_project

    good = {"customers": {"total": 3}, "users": {"active_daily": 10, "active_monthly": 40}}
    handler = lambda req: httpx.Response(200, json=good) if req.headers.get("authorization") == "Bearer k" else httpx.Response(401)  # noqa: E731
    mock = httpx.Client(transport=httpx.MockTransport(handler))
    with SessionLocal() as db:
        p = Project(slug="live", name="Live", base_url="https://x.test/m", api_key="k")
        db.add(p)
        db.commit()
        assert pull_project(db, p, mock) is None
        p.api_key = "wrong"
        assert pull_project(db, p, mock) is not None and p.last_pull_error
    ov = client.get("/api/overview", headers=auth).json()
    live = next(x for x in ov["projects"] if x["name"] == "Live")
    assert live["status"] == "Sync failing"


def test_internal_pull_needs_secret(client):
    assert client.post("/internal/pull").status_code == 401
    assert client.post("/internal/pull", headers={"X-Pull-Secret": "sekret"}).status_code == 200


def test_vercel_cron_endpoint(client):
    assert client.get("/api/cron/pull").status_code == 401
    assert client.get("/api/cron/pull", headers={"Authorization": "Bearer wrong"}).status_code == 401
    assert client.get("/api/cron/pull", headers={"Authorization": "Bearer cronsekret"}).status_code == 200


def test_database_url_is_normalised():
    from app.db import _normalise

    assert _normalise("postgres://u:p@h/db") == "postgresql+psycopg://u:p@h/db"
    assert _normalise("postgresql://u:p@h/db?sslmode=require") == "postgresql+psycopg://u:p@h/db?sslmode=require"
    assert _normalise("sqlite:///x.db") == "sqlite:///x.db"
