from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class MemoUpsert(BaseModel):
    ticker: str = Field(min_length=1)
    title: Optional[str] = None
    thesis: Optional[str] = None
    entryCondition: Optional[str] = None
    stopCondition: Optional[str] = None
    checklist: Optional[str] = None
    review: Optional[str] = None
