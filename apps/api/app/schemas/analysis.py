from __future__ import annotations

from pydantic import BaseModel, Field


class AnalysisRequest(BaseModel):
    ticker: str = Field(min_length=1)
