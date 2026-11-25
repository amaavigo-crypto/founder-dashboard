from datetime import date, datetime, timezone
from zoneinfo import ZoneInfo

import httpx
from sqlalchemy import select
from sqlalchemy.orm import Session

from .config import settings
from .contract import MetricsPayload
from .models import Project, Snapshot


def today() -> date:
    return datetime.now(ZoneInfo(settings.timezone)).date()


def pull_project(db: Session, project: Project, client: httpx.Client | None = None) -> str | None:
    """Fetch one project's metrics and store today's snapshot. Returns an error message or None."""
    if not project.base_url:
        return "no metrics URL set"
    own = client is None
    client = client or httpx.Client(timeout=15)
    try:
        headers = {"Authorization": f"Bearer {project.api_key}"} if project.api_key else {}
        res = client.get(project.base_url, headers=headers)
        res.raise_for_status()
        payload = MetricsPayload.model_validate(res.json())
        data = payload.model_dump(mode="json")
        snap = db.scalar(select(Snapshot).where(Snapshot.project_id == project.id, Snapshot.day == today()))
        if snap:
            snap.payload = data
        else:
            db.add(Snapshot(project_id=project.id, day=today(), payload=data))
        project.last_pull_error = None
        error = None
    except Exception as exc:  # network, HTTP, or contract validation failure
        project.last_pull_error = str(exc)[:500]
        error = project.last_pull_error
    finally:
        project.last_pull_at = datetime.now(timezone.utc)
        db.commit()
        if own:
            client.close()
    return error


def pull_all(db: Session, client: httpx.Client | None = None) -> dict[str, str | None]:
    projects = db.scalars(select(Project).where(Project.active, Project.base_url.is_not(None))).all()
    return {p.slug: pull_project(db, p, client) for p in projects}
