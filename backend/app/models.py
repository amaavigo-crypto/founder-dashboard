from datetime import date, datetime, timezone

from sqlalchemy import JSON, Boolean, Date, DateTime, Float, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from .db import Base


def _now() -> datetime:
    return datetime.now(timezone.utc)


class Founder(Base):
    __tablename__ = "founders"
    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)


class Project(Base):
    __tablename__ = "projects"
    id: Mapped[int] = mapped_column(primary_key=True)
    slug: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(120))
    color: Mapped[str] = mapped_column(String(9), default="#2F4BD0")
    base_url: Mapped[str | None] = mapped_column(String(500), nullable=True)  # full URL of its metrics endpoint
    api_key: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_sample: Mapped[bool] = mapped_column(Boolean, default=False)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    last_pull_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_pull_error: Mapped[str | None] = mapped_column(Text, nullable=True)


class Snapshot(Base):
    """One metrics payload per project per day (later pulls the same day overwrite it)."""

    __tablename__ = "snapshots"
    __table_args__ = (UniqueConstraint("project_id", "day", name="uq_snapshot_project_day"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"), index=True)
    day: Mapped[date] = mapped_column(Date, index=True)
    payload: Mapped[dict] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)


class ManualMoney(Base):
    """For products that do not report money yet: revenue/cost typed in by a founder."""

    __tablename__ = "manual_money"
    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"), index=True)
    day: Mapped[date] = mapped_column(Date, index=True)
    revenue: Mapped[float] = mapped_column(Float, default=0)
    ai: Mapped[float] = mapped_column(Float, default=0)
    hosting: Mapped[float] = mapped_column(Float, default=0)
    messaging: Mapped[float] = mapped_column(Float, default=0)
    other: Mapped[float] = mapped_column(Float, default=0)
    note: Mapped[str | None] = mapped_column(String(255), nullable=True)
