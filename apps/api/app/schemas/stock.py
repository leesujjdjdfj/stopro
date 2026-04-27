from __future__ import annotations

from pydantic import BaseModel


class HistoryResponse(BaseModel):
    ticker: str
    period: str
    cacheHit: bool
    source: str
    rows: list[dict]
