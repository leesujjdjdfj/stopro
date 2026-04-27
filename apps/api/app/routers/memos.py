from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlmodel import Session, select

from app.core.utils import normalize_ticker
from app.db.database import get_session
from app.db.models import Memo
from app.db.repository import upsert_memo
from app.schemas.memo import MemoUpsert

router = APIRouter(prefix="/api/memos", tags=["memos"])


@router.get("/{ticker}")
def get_memo(ticker: str, session: Session = Depends(get_session)) -> dict:
    memo = session.exec(select(Memo).where(Memo.ticker == normalize_ticker(ticker))).first()
    return memo.model_dump() if memo else {"ticker": normalize_ticker(ticker)}


@router.post("")
def save_memo(payload: MemoUpsert, session: Session = Depends(get_session)) -> Memo:
    data = {
        "title": payload.title,
        "thesis": payload.thesis,
        "entry_condition": payload.entryCondition,
        "stop_condition": payload.stopCondition,
        "checklist": payload.checklist,
        "review": payload.review,
    }
    return upsert_memo(session, payload.ticker, data)
