from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from app.core.errors import StockDataError
from app.core.utils import normalize_ticker, safe_float
from app.data.market_data import MarketDataProvider
from app.db.database import get_session
from app.db.models import Alert
from app.schemas.alert import AlertCreate, AlertUpdate

router = APIRouter(prefix="/api/alerts", tags=["alerts"])
provider = MarketDataProvider()


@router.get("")
def list_alerts(session: Session = Depends(get_session)) -> list[Alert]:
    return session.exec(select(Alert).order_by(Alert.created_at.desc())).all()


@router.post("")
def create_alert(payload: AlertCreate, session: Session = Depends(get_session)) -> Alert:
    item = Alert(
        ticker=normalize_ticker(payload.ticker),
        condition_type=payload.conditionType,
        target_price=payload.targetPrice,
        message=payload.message,
        is_active=payload.isActive,
    )
    session.add(item)
    session.commit()
    session.refresh(item)
    return item


@router.put("/{alert_id}")
def update_alert(alert_id: int, payload: AlertUpdate, session: Session = Depends(get_session)) -> Alert:
    item = session.get(Alert, alert_id)
    if not item:
        raise HTTPException(status_code=404, detail="알림 조건을 찾을 수 없습니다.")
    item.ticker = normalize_ticker(payload.ticker)
    item.condition_type = payload.conditionType
    item.target_price = payload.targetPrice
    item.message = payload.message
    item.is_active = payload.isActive
    session.add(item)
    session.commit()
    session.refresh(item)
    return item


@router.delete("/{alert_id}")
def delete_alert(alert_id: int, session: Session = Depends(get_session)) -> dict:
    item = session.get(Alert, alert_id)
    if not item:
        raise HTTPException(status_code=404, detail="알림 조건을 찾을 수 없습니다.")
    session.delete(item)
    session.commit()
    return {"ok": True}


@router.get("/triggered")
def triggered_alerts(session: Session = Depends(get_session)) -> list[dict]:
    alerts = session.exec(select(Alert).where(Alert.is_active == True)).all()  # noqa: E712
    results = []
    for alert in alerts:
        evaluated = evaluate_alert(alert)
        if evaluated.get("triggered"):
            alert.triggered_at = datetime.now(timezone.utc)
            session.add(alert)
            results.append(evaluated)
    session.commit()
    return results


def evaluate_alert(alert: Alert) -> dict:
    try:
        quote = provider.get_quote(alert.ticker)
        price = quote.get("price")
        triggered = False
        if price is not None:
            if alert.condition_type in {"above", "price_above", "현재가 이상"}:
                triggered = price >= alert.target_price
            elif alert.condition_type in {"below", "price_below", "현재가 이하"}:
                triggered = price <= alert.target_price
            elif alert.condition_type in {"target_reached", "목표가 도달"}:
                triggered = price >= alert.target_price
            elif alert.condition_type in {"stop_near", "손절가 근접"}:
                triggered = price <= alert.target_price * 1.03
        return {
            "id": alert.id,
            "ticker": alert.ticker,
            "conditionType": alert.condition_type,
            "targetPrice": alert.target_price,
            "message": alert.message,
            "currentPrice": safe_float(price, 4),
            "triggered": triggered,
        }
    except StockDataError as exc:
        return {
            "id": alert.id,
            "ticker": alert.ticker,
            "conditionType": alert.condition_type,
            "targetPrice": alert.target_price,
            "message": exc.message,
            "currentPrice": None,
            "triggered": False,
        }
