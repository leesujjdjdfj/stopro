from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlmodel import Session, delete

from app.core.cache import cache
from app.db.database import get_session
from app.db.models import Alert, AnalysisSnapshot, Memo, Position, Setting, Watchlist
from app.db.repository import get_settings_dict, update_settings
from app.schemas.settings import SettingsUpdate

router = APIRouter(prefix="/api/settings", tags=["settings"])


@router.get("")
def get_settings(session: Session = Depends(get_session)) -> dict[str, str]:
    return get_settings_dict(session)


@router.put("")
def put_settings(payload: SettingsUpdate, session: Session = Depends(get_session)) -> dict[str, str]:
    values = {key: value for key, value in payload.model_dump().items() if value is not None}
    return update_settings(session, values)


@router.post("/clear-cache")
def clear_cache() -> dict:
    cache.clear()
    return {"ok": True}


@router.post("/reset-db")
def reset_db(session: Session = Depends(get_session)) -> dict:
    for model in [Watchlist, Position, Alert, AnalysisSnapshot, Memo, Setting]:
        session.exec(delete(model))
    session.commit()
    cache.clear()
    get_settings_dict(session)
    return {"ok": True}
