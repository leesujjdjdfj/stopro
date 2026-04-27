from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from app.analysis.engine import AnalysisEngine
from app.core.errors import StockDataError
from app.core.utils import normalize_ticker
from app.db.database import get_session
from app.db.models import Watchlist
from app.db.repository import add_watchlist, get_settings_dict, save_snapshot, update_watchlist_analysis
from app.schemas.watchlist import WatchlistCreate

router = APIRouter(prefix="/api/watchlist", tags=["watchlist"])
engine = AnalysisEngine()


@router.get("")
def list_watchlist(session: Session = Depends(get_session)) -> list[Watchlist]:
    return session.exec(select(Watchlist).order_by(Watchlist.created_at.desc())).all()


@router.post("")
def create_watchlist(payload: WatchlistCreate, session: Session = Depends(get_session)) -> Watchlist:
    return add_watchlist(session, payload.ticker, payload.note)


@router.delete("/{ticker}")
def delete_watchlist(ticker: str, session: Session = Depends(get_session)) -> dict:
    item = session.exec(select(Watchlist).where(Watchlist.ticker == normalize_ticker(ticker))).first()
    if not item:
        raise HTTPException(status_code=404, detail="관심종목을 찾을 수 없습니다.")
    session.delete(item)
    session.commit()
    return {"ok": True}


@router.post("/analyze-all")
def analyze_all(session: Session = Depends(get_session)) -> dict:
    settings = get_settings_dict(session)
    capital = float(settings.get("defaultCapitalKRW", 5_000_000))
    risk_profile = settings.get("defaultRiskProfile", "balanced")
    items = session.exec(select(Watchlist).order_by(Watchlist.created_at.desc())).all()
    results = []
    errors = []
    for item in items:
        try:
            result = engine.analyze(item.ticker, capital, risk_profile)
            save_snapshot(session, result, capital)
            update_watchlist_analysis(session, item.ticker, result)
            results.append(result)
        except StockDataError as exc:
            errors.append({"ticker": item.ticker, "message": exc.message})
    return {"results": results, "errors": errors}
