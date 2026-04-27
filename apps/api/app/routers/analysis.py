from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session

from app.analysis.engine import AnalysisEngine
from app.core.errors import StockDataError
from app.db.database import get_session
from app.db.repository import save_snapshot, update_watchlist_analysis
from app.schemas.analysis import AnalysisRequest

router = APIRouter(prefix="/api", tags=["analysis"])
engine = AnalysisEngine()


@router.post("/analyze")
def analyze(payload: AnalysisRequest, session: Session = Depends(get_session)) -> dict:
    try:
        result = engine.analyze(payload.ticker)
    except StockDataError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc
    save_snapshot(session, result)
    update_watchlist_analysis(session, payload.ticker, result)
    return result
