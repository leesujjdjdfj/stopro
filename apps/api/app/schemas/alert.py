from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class AlertCreate(BaseModel):
    ticker: str = Field(min_length=1)
    conditionType: str
    targetPrice: float = Field(gt=0)
    message: Optional[str] = None
    isActive: bool = True


class AlertUpdate(AlertCreate):
    pass
