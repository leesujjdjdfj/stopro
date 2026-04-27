from __future__ import annotations

from pydantic import BaseModel, Field


class AnalysisRequest(BaseModel):
    ticker: str = Field(min_length=1)
    capitalKRW: float = Field(default=5_000_000, gt=0)
    riskProfile: str = "balanced"
