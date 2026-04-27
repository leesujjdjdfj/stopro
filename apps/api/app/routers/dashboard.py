from __future__ import annotations

import json

from fastapi import APIRouter, Depends
from sqlmodel import Session, select

from app.analysis.engine import AnalysisEngine
from app.core.errors import StockDataError
from app.db.database import get_session
from app.db.models import Alert, AnalysisSnapshot, Position, Watchlist
from app.db.repository import get_settings_dict, recent_snapshots, save_snapshot, update_watchlist_analysis
from app.routers.alerts import evaluate_alert

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])
engine = AnalysisEngine()


@router.get("")
def dashboard(session: Session = Depends(get_session)) -> dict:
    settings = get_settings_dict(session)
    capital = float(settings.get("defaultCapitalKRW", 5_000_000))
    risk_profile = settings.get("defaultRiskProfile", "balanced")
    watchlist = session.exec(select(Watchlist).order_by(Watchlist.created_at.desc())).all()
    alerts = session.exec(select(Alert).where(Alert.is_active == True)).all()  # noqa: E712
    positions = session.exec(select(Position)).all()

    analyzed = []
    errors = []
    for item in watchlist[:12]:
        try:
            result = engine.analyze(item.ticker, capital, risk_profile)
            save_snapshot(session, result, capital)
            update_watchlist_analysis(session, item.ticker, result)
            analyzed.append(_signal_from_analysis(result))
        except StockDataError as exc:
            errors.append({"ticker": item.ticker, "message": exc.message})

    triggered = []
    for alert in alerts:
        item = evaluate_alert(alert)
        if item.get("triggered"):
            triggered.append(item)

    top_candidates = [
        item
        for item in analyzed
        if item["decision"] in {"candidate", "split_buy"}
        and (item.get("riskScore") or 100) < 60
        and (item.get("rewardRiskRatio") or 0) >= 1.5
    ][:5]
    risk_alerts = [
        item
        for item in analyzed
        if (item.get("riskScore") or 0) >= 70 or item.get("priceBelowMA20") or item["decision"] in {"caution", "avoid"}
    ][:8]

    recent = []
    for snapshot in recent_snapshots(session, 6):
        try:
            raw = json.loads(snapshot.raw_json)
            recent.append(
                {
                    "ticker": snapshot.ticker,
                    "label": snapshot.decision_label,
                    "summary": snapshot.summary,
                    "riskScore": snapshot.risk_score,
                    "rewardRiskRatio": snapshot.reward_risk_ratio,
                    "createdAt": snapshot.created_at.isoformat(),
                    "price": raw.get("currentPrice"),
                }
            )
        except Exception:
            recent.append(
                {
                    "ticker": snapshot.ticker,
                    "label": snapshot.decision_label,
                    "summary": snapshot.summary,
                    "riskScore": snapshot.risk_score,
                    "rewardRiskRatio": snapshot.reward_risk_ratio,
                    "createdAt": snapshot.created_at.isoformat(),
                    "price": None,
                }
            )

    return {
        "watchlistCount": len(watchlist),
        "positionCount": len(positions),
        "candidateCount": len(top_candidates),
        "cautionCount": len(risk_alerts),
        "triggeredAlertCount": len(triggered),
        "signals": analyzed,
        "topCandidates": top_candidates,
        "riskAlerts": risk_alerts,
        "triggeredAlerts": triggered,
        "recentlyAnalyzed": recent,
        "errors": errors,
    }


def _signal_from_analysis(result: dict) -> dict:
    indicators = result.get("indicators", {})
    price = result.get("currentPrice")
    ma20 = indicators.get("ma20")
    return {
        "ticker": result.get("ticker"),
        "displayTicker": result.get("displayTicker"),
        "name": result.get("name"),
        "market": result.get("market"),
        "exchange": result.get("exchange"),
        "currency": result.get("currency"),
        "price": price,
        "dailyChangePercent": result.get("dailyChangePercent"),
        "decision": result.get("decision", {}).get("status"),
        "decisionLabel": result.get("decision", {}).get("label"),
        "riskScore": result.get("risk", {}).get("score"),
        "rewardRiskRatio": result.get("rewardRisk", {}).get("ratioToSecondTarget"),
        "lastAnalyzedAt": result.get("dataQuality", {}).get("lastUpdated"),
        "priceBelowMA20": bool(ma20 and price and price < ma20),
        "macdBullish": bool(indicators.get("macd") is not None and indicators.get("macdSignal") is not None and indicators.get("macd") > indicators.get("macdSignal")),
    }
