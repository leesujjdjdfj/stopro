from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class WatchlistCreate(BaseModel):
    ticker: str = Field(min_length=1)
    note: Optional[str] = None
