from __future__ import annotations

import json
from datetime import datetime, timezone

from sqlmodel import Session, select

from app.core.utils import clean_json, normalize_ticker
from app.db.models import Alert, AnalysisSnapshot, Memo, Position, Setting, Watchlist


DEFAULT_SETTINGS = {
    "defaultCapitalKRW": "5000000",
    "defaultRiskProfile": "balanced",
    "defaultExchangeRate": "1350",
    "cacheTTLSeconds": "300",
}


def ensure_default_settings(session: Session) -> None:
    for key, value in DEFAULT_SETTINGS.items():
        existing = session.exec(select(Setting).where(Setting.key == key)).first()
        if not existing:
            session.add(Setting(key=key, value=value))
    session.commit()


def get_settings_dict(session: Session) -> dict[str, str]:
    ensure_default_settings(session)
    settings = session.exec(select(Setting)).all()
    return {item.key: item.value for item in settings}


def update_settings(session: Session, values: dict[str, str]) -> dict[str, str]:
    ensure_default_settings(session)
    for key, value in values.items():
        existing = session.exec(select(Setting).where(Setting.key == key)).first()
        if existing:
            existing.value = str(value)
            session.add(existing)
        else:
            session.add(Setting(key=key, value=str(value)))
    session.commit()
    return get_settings_dict(session)


def add_watchlist(session: Session, ticker: str, note: str | None = None) -> Watchlist:
    normalized = normalize_ticker(ticker)
    existing = session.exec(select(Watchlist).where(Watchlist.ticker == normalized)).first()
    if existing:
        existing.note = note if note is not None else existing.note
        session.add(existing)
        session.commit()
        session.refresh(existing)
        return existing
    item = Watchlist(ticker=normalized, note=note)
    session.add(item)
    session.commit()
    session.refresh(item)
    return item


def update_watchlist_analysis(session: Session, ticker: str, analysis: dict) -> None:
    item = session.exec(select(Watchlist).where(Watchlist.ticker == normalize_ticker(ticker))).first()
    if not item:
        return
    item.last_analyzed_at = datetime.now(timezone.utc)
    item.last_decision = analysis.get("decision", {}).get("status")
    item.last_risk_score = analysis.get("risk", {}).get("score")
    item.last_reward_risk_ratio = analysis.get("rewardRisk", {}).get("ratioToSecondTarget")
    session.add(item)
    session.commit()


def save_snapshot(session: Session, analysis: dict, capital_krw: float) -> AnalysisSnapshot:
    snapshot = AnalysisSnapshot(
        ticker=analysis.get("ticker"),
        capital_krw=capital_krw,
        decision_status=analysis.get("decision", {}).get("status"),
        decision_label=analysis.get("decision", {}).get("label"),
        risk_score=analysis.get("risk", {}).get("score") or 0,
        reward_risk_ratio=analysis.get("rewardRisk", {}).get("ratioToSecondTarget"),
        summary=analysis.get("summary") or "",
        raw_json=json.dumps(clean_json(analysis), ensure_ascii=False),
    )
    session.add(snapshot)
    session.commit()
    session.refresh(snapshot)
    return snapshot


def recent_snapshots(session: Session, limit: int = 5) -> list[AnalysisSnapshot]:
    return session.exec(select(AnalysisSnapshot).order_by(AnalysisSnapshot.created_at.desc()).limit(limit)).all()


def upsert_memo(session: Session, ticker: str, payload: dict) -> Memo:
    normalized = normalize_ticker(ticker)
    memo = session.exec(select(Memo).where(Memo.ticker == normalized)).first()
    if not memo:
        memo = Memo(ticker=normalized)
    for field in ["title", "thesis", "entry_condition", "stop_condition", "checklist", "review"]:
        if field in payload:
            setattr(memo, field, payload.get(field))
    memo.updated_at = datetime.now(timezone.utc)
    session.add(memo)
    session.commit()
    session.refresh(memo)
    return memo
