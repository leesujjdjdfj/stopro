from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from sqlmodel import Field, SQLModel


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class Watchlist(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    ticker: str = Field(index=True, unique=True)
    note: Optional[str] = None
    created_at: datetime = Field(default_factory=utc_now)
    last_analyzed_at: Optional[datetime] = None
    last_decision: Optional[str] = None
    last_risk_score: Optional[int] = None
    last_reward_risk_ratio: Optional[float] = None


class Position(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    ticker: str = Field(index=True)
    average_price: float
    quantity: float
    target_price: Optional[float] = None
    stop_loss: Optional[float] = None
    note: Optional[str] = None
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)


class Alert(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    ticker: str = Field(index=True)
    condition_type: str
    target_price: float
    message: Optional[str] = None
    is_active: bool = True
    triggered_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=utc_now)


class AnalysisSnapshot(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    ticker: str = Field(index=True)
    capital_krw: float = 0
    decision_status: str
    decision_label: str
    risk_score: int
    reward_risk_ratio: Optional[float] = None
    summary: str
    raw_json: str
    created_at: datetime = Field(default_factory=utc_now)


class Memo(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    ticker: str = Field(index=True, unique=True)
    title: Optional[str] = None
    thesis: Optional[str] = None
    entry_condition: Optional[str] = None
    stop_condition: Optional[str] = None
    checklist: Optional[str] = None
    review: Optional[str] = None
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)


class Setting(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    key: str = Field(index=True, unique=True)
    value: str
