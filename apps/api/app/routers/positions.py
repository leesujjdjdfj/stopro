from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from app.analysis.indicators import add_indicators, latest_indicators
from app.core.errors import StockDataError
from app.core.utils import normalize_ticker, safe_float
from app.data.market_data import MarketDataProvider
from app.db.database import get_session
from app.db.models import Position
from app.schemas.position import PositionCreate, PositionUpdate

router = APIRouter(prefix="/api/positions", tags=["positions"])
provider = MarketDataProvider()


@router.get("")
def list_positions(session: Session = Depends(get_session)) -> list[dict]:
    positions = session.exec(select(Position).order_by(Position.created_at.desc())).all()
    return [enrich_position(position) for position in positions]


@router.post("")
def create_position(payload: PositionCreate, session: Session = Depends(get_session)) -> Position:
    item = Position(
        ticker=normalize_ticker(payload.ticker),
        average_price=payload.averagePrice,
        quantity=payload.quantity,
        target_price=payload.targetPrice,
        stop_loss=payload.stopLoss,
        note=payload.note,
    )
    session.add(item)
    session.commit()
    session.refresh(item)
    return item


@router.put("/{position_id}")
def update_position(position_id: int, payload: PositionUpdate, session: Session = Depends(get_session)) -> Position:
    item = session.get(Position, position_id)
    if not item:
        raise HTTPException(status_code=404, detail="보유 종목을 찾을 수 없습니다.")
    item.ticker = normalize_ticker(payload.ticker)
    item.average_price = payload.averagePrice
    item.quantity = payload.quantity
    item.target_price = payload.targetPrice
    item.stop_loss = payload.stopLoss
    item.note = payload.note
    item.updated_at = datetime.now(timezone.utc)
    session.add(item)
    session.commit()
    session.refresh(item)
    return item


@router.delete("/{position_id}")
def delete_position(position_id: int, session: Session = Depends(get_session)) -> dict:
    item = session.get(Position, position_id)
    if not item:
        raise HTTPException(status_code=404, detail="보유 종목을 찾을 수 없습니다.")
    session.delete(item)
    session.commit()
    return {"ok": True}


def enrich_position(position: Position) -> dict:
    base = position.model_dump()
    try:
        quote = provider.get_quote(position.ticker)
        history, _, _ = provider.get_history(position.ticker, "6m")
        indicators = latest_indicators(add_indicators(history))
        current = quote.get("price")
        current_value = current * position.quantity if current else None
        cost = position.average_price * position.quantity
        pnl = current_value - cost if current_value is not None else None
        pnl_percent = (pnl / cost) * 100 if pnl is not None and cost else None
        stop_distance = ((current - position.stop_loss) / current) * 100 if current and position.stop_loss else None
        target_distance = ((position.target_price - current) / current) * 100 if current and position.target_price else None
        risk_state = "보통"
        risk_reasons = []
        if current and position.stop_loss and current <= position.stop_loss:
            risk_state = "손절 기준 이탈"
            risk_reasons.append("현재가가 손절 기준가 아래에 있습니다.")
        elif stop_distance is not None and stop_distance <= 5:
            risk_state = "주의"
            risk_reasons.append("현재가가 손절가에 가까워졌습니다.")
        if current and indicators.get("ma20") and current < indicators.get("ma20"):
            risk_state = "주의" if risk_state == "보통" else risk_state
            risk_reasons.append("현재가가 MA20 아래로 내려와 단기 추세 약화가 보입니다.")
        return {
            **base,
            "currentPrice": safe_float(current, 4),
            "currentValue": safe_float(current_value, 2),
            "profitLoss": safe_float(pnl, 2),
            "profitLossPercent": safe_float(pnl_percent, 2),
            "stopDistancePercent": safe_float(stop_distance, 2),
            "targetDistancePercent": safe_float(target_distance, 2),
            "riskState": risk_state,
            "riskReasons": risk_reasons or ["현재 입력한 기준에서는 즉시 위험 신호가 크지 않습니다."],
        }
    except StockDataError as exc:
        return {**base, "currentPrice": None, "riskState": "데이터 확인 필요", "riskReasons": [exc.message]}
