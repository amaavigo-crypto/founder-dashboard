"""The metrics contract (v1). Every product returns this JSON from its own metrics endpoint.

Money amounts are in INR for ONE DAY (payments received that day, costs incurred that day).
The dashboard sums days into ranges, so the same payload serves 7/30/90 days and monthly bars.
"""
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class Labels(BaseModel):
    customers: str = "Customers"  # what one customer is called here: Companies, Tenants...
    size: str = "Users"  # the size column in the customer table: Employees, Leads...
    trend: str = "Daily active users"  # title of the 30-day trend chart


class Customers(BaseModel):
    total: int = 0
    new: int = 0
    churned: int = 0


class Users(BaseModel):
    active_daily: int = 0
    active_weekly: int = 0
    active_monthly: int = 0


class Cost(BaseModel):
    ai: float = 0
    hosting: float = 0
    messaging: float = 0
    other: float = 0


class Money(BaseModel):
    revenue: float = 0
    cost: Cost = Field(default_factory=Cost)


class Health(BaseModel):
    uptime_pct: float | None = None
    errors: int = 0
    failed_jobs: int = 0


class Attention(BaseModel):
    level: Literal["info", "warn", "critical"] = "warn"
    title: str


class Stat(BaseModel):
    label: str
    value: str


class PanelRow(BaseModel):
    label: str
    value: str
    pct: float = Field(default=0, ge=0, le=100)


class Panel(BaseModel):
    title: str
    rows: list[PanelRow] = Field(default_factory=list, max_length=8)


class CustomerRow(BaseModel):
    name: str
    plan: str = ""
    size: str = ""
    last_active: str = ""
    revenue: str = ""
    status: Literal["active", "quiet", "at_risk"] = "active"


class AiCost(BaseModel):
    name: str
    cost: float


class MetricsPayload(BaseModel):
    contract_version: Literal[1] = 1
    generated_at: datetime | None = None
    labels: Labels = Field(default_factory=Labels)
    customers: Customers = Field(default_factory=Customers)
    users: Users = Field(default_factory=Users)
    trend_value: float | None = None  # the day's value for the trend chart; falls back to users.active_daily
    money: Money | None = None  # None = this product does not report money (use manual entry)
    health: Health = Field(default_factory=Health)
    attention: list[Attention] = Field(default_factory=list, max_length=10)
    headline: list[Stat] = Field(default_factory=list, max_length=4)  # the 4 numbers on the project card
    panel: Panel | None = None  # the project-specific panel
    customers_list: list[CustomerRow] = Field(default_factory=list, max_length=50)
    ai_cost_by_customer: list[AiCost] = Field(default_factory=list, max_length=50)  # last 30 days
