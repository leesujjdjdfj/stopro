from __future__ import annotations

from pydantic import BaseModel


class SymbolSearchResult(BaseModel):
    name: str
    ticker: str
    market: str
    exchange: str
    currency: str
