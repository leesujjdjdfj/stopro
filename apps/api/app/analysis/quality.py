from __future__ import annotations

import pandas as pd

from app.core.utils import now_iso


def check_data_quality(
    history: pd.DataFrame,
    indicators: dict,
    source: str,
    cache_hit: bool,
    is_realtime: bool = False,
    quote_source: str | None = None,
) -> dict:
    row_count = len(history)
    missing_close = int(history["Close"].isna().sum()) if "Close" in history else row_count
    missing_volume = int(history["Volume"].isna().sum()) if "Volume" in history else row_count
    latest_close_exists = row_count > 0 and pd.notna(history["Close"].iloc[-1])
    has_core_indicators = indicators.get("ma20") is not None and indicators.get("rsi") is not None and indicators.get("atr") is not None
    has_enough_history = row_count >= 80

    if not latest_close_exists or row_count < 40 or source == "mock-fallback":
        status = "poor" if row_count < 40 else "partial"
    elif not has_enough_history or not has_core_indicators or missing_close > 0:
        status = "partial"
    else:
        status = "good"

    display_source = quote_source if quote_source and quote_source != source else source
    if quote_source and quote_source != source:
        display_source = f"{quote_source} 현재가 + {source} 일봉"

    if status == "good" and quote_source == "KIS":
        message = "KIS 현재가와 일봉 데이터 기반 분석입니다. 주문 기능은 제공하지 않습니다."
    elif status == "good":
        message = "무료 데이터 소스 기반이므로 실제 시세와 차이가 있을 수 있습니다."
    elif status == "partial":
        message = "일부 데이터가 부족할 수 있어 분석 결과를 보수적으로 해석해야 합니다."
    else:
        message = "데이터 부족으로 분석 신뢰도가 낮습니다."

    return {
        "source": display_source,
        "status": status,
        "hasEnoughHistory": has_enough_history,
        "missingRows": missing_close,
        "missingVolumeRows": missing_volume,
        "latestCloseExists": bool(latest_close_exists),
        "indicatorsAvailable": bool(has_core_indicators),
        "analysisAvailable": bool(latest_close_exists and row_count >= 40),
        "lastUpdated": now_iso(),
        "cacheHit": cache_hit,
        "isRealtime": is_realtime,
        "message": message,
    }
