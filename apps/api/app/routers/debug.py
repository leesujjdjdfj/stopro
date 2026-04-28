from __future__ import annotations

from fastapi import APIRouter

from app.core.errors import StockDataError
from app.data.providers.kis_token_manager import kis_token_manager


router = APIRouter(prefix="/api/debug", tags=["debug"])


@router.get("/kis/status")
def kis_status(issue: bool = True) -> dict:
    if issue and kis_token_manager.is_configured() and not kis_token_manager.has_valid_token():
        try:
            kis_token_manager.get_token()
        except StockDataError:
            pass
    return kis_token_manager.status()


@router.post("/kis/invalidate")
def kis_invalidate() -> dict:
    kis_token_manager.invalidate_token()
    return kis_token_manager.status()
