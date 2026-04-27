from __future__ import annotations

from app.core.utils import safe_float


def calculate_risk(close: float, previous_close: float | None, indicators: dict, reward_risk: dict) -> dict:
    atr = indicators.get("atr") or close * 0.03
    rsi = indicators.get("rsi")
    stochastic_k = indicators.get("stochasticK")
    ma20 = indicators.get("ma20")
    ma60 = indicators.get("ma60")
    volume_ratio = indicators.get("volumeRatio") or 1
    adx = indicators.get("adx")
    plus_di = indicators.get("plusDI")
    minus_di = indicators.get("minusDI")
    mfi = indicators.get("mfi")
    distance_high = indicators.get("distanceFrom52WeekHighPercent")
    rr = reward_risk.get("ratioToSecondTarget")

    volatility_risk = min(25, max(0, (atr / close) / 0.08 * 25)) if close else 15
    overbought_risk = 4
    if rsi is not None:
        if rsi > 75:
            overbought_risk += 12
        elif rsi > 70:
            overbought_risk += 9
        elif rsi > 65:
            overbought_risk += 6
        elif rsi < 35:
            overbought_risk += 8
    if stochastic_k is not None and stochastic_k > 85:
        overbought_risk += 5
    overbought_risk = min(20, overbought_risk)

    trend_break_risk = 4
    if ma20 and close < ma20:
        trend_break_risk += 10
    if ma60 and close < ma60:
        trend_break_risk += 6
    if adx is not None and adx >= 25 and plus_di is not None and minus_di is not None and minus_di > plus_di:
        trend_break_risk += 5
    trend_break_risk = min(20, trend_break_risk)

    volume_risk = 3
    if volume_ratio > 3:
        volume_risk = 15
    elif volume_ratio > 2:
        volume_risk = 11
    elif volume_ratio > 1.5:
        volume_risk = 7
    if previous_close and close < previous_close and volume_ratio > 1.5:
        volume_risk = min(15, volume_risk + 4)
    if mfi is not None and mfi > 80:
        volume_risk = min(15, volume_risk + 3)

    high_proximity_risk = 4
    if distance_high is not None:
        distance_abs = abs(distance_high)
        if distance_abs <= 3:
            high_proximity_risk = 10
        elif distance_abs <= 7:
            high_proximity_risk = 7
        elif distance_abs <= 15:
            high_proximity_risk = 5
        else:
            high_proximity_risk = 2

    reward_risk_penalty = 3
    if rr is None:
        reward_risk_penalty = 7
    elif rr < 1:
        reward_risk_penalty = 10
    elif rr < 1.5:
        reward_risk_penalty = 7
    elif rr < 2:
        reward_risk_penalty = 4
    else:
        reward_risk_penalty = 1

    score = round(min(100, volatility_risk + overbought_risk + trend_break_risk + volume_risk + high_proximity_risk + reward_risk_penalty))
    if score <= 34:
        label = "상대적 위험 낮음"
        description = "현재 지표 조합에서는 위험 신호가 비교적 제한적입니다."
    elif score <= 69:
        label = "보통"
        description = "추세와 손익비는 함께 확인해야 하며, 손절 기준을 먼저 정하는 것이 중요합니다."
    else:
        label = "위험 신호 높음"
        description = "변동성, 추세 이탈, 과열 등 리스크 관리가 우선인 구간입니다."

    return {
        "score": score,
        "label": label,
        "description": description,
        "factors": [
            {
                "name": "변동성",
                "score": round(volatility_risk),
                "description": f"ATR 기준 일간 변동성은 약 {safe_float((atr / close) * 100 if close else None, 2)}% 수준입니다.",
            },
            {
                "name": "과열",
                "score": round(overbought_risk),
                "description": "RSI와 스토캐스틱 위치를 기준으로 과열 가능성을 점검했습니다.",
            },
            {
                "name": "추세 이탈",
                "score": round(trend_break_risk),
                "description": "현재가, 주요 이동평균선, ADX 방향성을 기준으로 추세 훼손 여부를 확인했습니다.",
            },
            {
                "name": "거래량",
                "score": round(volume_risk),
                "description": f"최근 거래량은 20일 평균 대비 {safe_float(volume_ratio, 2)}배 수준이며 MFI 과열 여부도 반영했습니다.",
            },
            {
                "name": "고점 근접",
                "score": round(high_proximity_risk),
                "description": "52주 고점과의 거리를 기준으로 추격 위험을 반영했습니다.",
            },
            {
                "name": "손익비",
                "score": round(reward_risk_penalty),
                "description": "목표가 대비 손절 위험이 충분히 보상되는지 반영했습니다.",
            },
        ],
    }
