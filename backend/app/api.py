import hmac
from datetime import date

from fastapi import APIRouter, Depends, Header, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from . import metrics
from .config import settings
from .db import get_db
from .models import Founder, ManualMoney, Project
from .puller import pull_all, pull_project
from .security import create_token, current_founder, verify_password

router = APIRouter(prefix="/api")
internal = APIRouter()


class LoginIn(BaseModel):
    email: str
    password: str


class ProjectIn(BaseModel):
    slug: str = Field(pattern=r"^[a-z0-9][a-z0-9-]{0,62}$")
    name: str = Field(min_length=1, max_length=120)
    color: str = Field(default="#2F4BD0", pattern=r"^#[0-9a-fA-F]{6}$")
    base_url: str | None = None  # the product's metrics endpoint, e.g. https://hr.example.com/api/founder/metrics
    api_key: str | None = None


class ManualMoneyIn(BaseModel):
    project_id: int
    day: date
    revenue: float = Field(default=0, ge=0)
    ai: float = Field(default=0, ge=0)
    hosting: float = Field(default=0, ge=0)
    messaging: float = Field(default=0, ge=0)
    other: float = Field(default=0, ge=0)
    note: str | None = Field(default=None, max_length=255)


RangeQ = Query("30d", alias="range", pattern="^(7d|30d|90d)$")


@router.post("/auth/login")
def login(body: LoginIn, db: Session = Depends(get_db)):
    founder = db.scalar(select(Founder).where(Founder.email == body.email.strip().lower()))
    if not founder or not verify_password(body.password, founder.password_hash):
        raise HTTPException(401, "Wrong email or password")
    return {"token": create_token(founder), "email": founder.email}


@router.get("/overview")
def overview(rng: str = RangeQ, _: Founder = Depends(current_founder), db: Session = Depends(get_db)):
    return metrics.overview(db, rng)


@router.get("/projects")
def projects(_: Founder = Depends(current_founder), db: Session = Depends(get_db)):
    return metrics.project_list(db)


@router.get("/projects/{project_id}")
def project(project_id: int, rng: str = RangeQ, _: Founder = Depends(current_founder),
            db: Session = Depends(get_db)):
    p = db.get(Project, project_id)
    if not p or not p.active:
        raise HTTPException(404, "Project not found")
    return metrics.project_detail(db, p, rng)


@router.get("/money")
def money(rng: str = RangeQ, _: Founder = Depends(current_founder), db: Session = Depends(get_db)):
    return metrics.money(db, rng)


@router.post("/projects", status_code=201)
def add_project(body: ProjectIn, _: Founder = Depends(current_founder), db: Session = Depends(get_db)):
    if db.scalar(select(Project).where(Project.slug == body.slug)):
        raise HTTPException(409, "A project with this slug already exists")
    p = Project(**body.model_dump())
    db.add(p)
    db.commit()
    error = pull_project(db, p) if p.base_url else None
    return {"id": p.id, "first_pull_error": error}


@router.post("/projects/{project_id}/pull")
def pull_now(project_id: int, _: Founder = Depends(current_founder), db: Session = Depends(get_db)):
    p = db.get(Project, project_id)
    if not p:
        raise HTTPException(404, "Project not found")
    return {"error": pull_project(db, p)}


@router.post("/manual-money", status_code=201)
def add_manual_money(body: ManualMoneyIn, _: Founder = Depends(current_founder), db: Session = Depends(get_db)):
    if not db.get(Project, body.project_id):
        raise HTTPException(404, "Project not found")
    row = ManualMoney(**body.model_dump())
    db.add(row)
    db.commit()
    return {"id": row.id}


@internal.post("/internal/pull")
def scheduled_pull(x_pull_secret: str = Header(default=""), db: Session = Depends(get_db)):
    """Called nightly by cronjob.org with the PULL_SECRET header."""
    if not hmac.compare_digest(x_pull_secret, settings.pull_secret):
        raise HTTPException(401, "Bad secret")
    return pull_all(db)
