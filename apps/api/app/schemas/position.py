from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class PositionCreate(BaseModel):
    ticker: str = Field(min_length=1)
    averagePrice: float = Field(gt=0)
    quantity: float = Field(gt=0)
    targetPrice: Optional[float] = None
    stopLoss: Optional[float] = None
    note: Optional[str] = None


class PositionUpdate(PositionCreate):
    pass
