from __future__ import annotations

from fastapi import APIRouter, Query

from app.data.symbol_search import search_symbols
from app.schemas.search import SymbolSearchResult

router = APIRouter(prefix="/api/search", tags=["search"])


@router.get("", response_model=list[SymbolSearchResult])
def search(q: str = Query(..., min_length=1), limit: int = Query(10, ge=1, le=10)) -> list[dict]:
    return search_symbols(q, limit)
