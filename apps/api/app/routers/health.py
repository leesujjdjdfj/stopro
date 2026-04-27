from __future__ import annotations

from fastapi import APIRouter

from app.core.utils import now_iso

router = APIRouter()


@router.get("/health")
def health() -> dict:
    return {"status": "ok", "service": "StoPro API", "time": now_iso()}
