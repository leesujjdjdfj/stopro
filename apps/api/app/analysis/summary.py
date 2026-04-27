from __future__ import annotations


LABELS = {
    "candidate": "매수 후보",
    "split_buy": "분할 접근",
    "watch": "관망",
    "caution": "주의",
    "avoid": "회피",
}


def make_decision(close: float, indicators: dict, risk: dict, reward_risk: dict, quality: dict) -> dict:
    rsi = indicators.get("rsi")
    stochastic_k = indicators.get("stochasticK")
    ma20 = indicators.get("ma20")
    ma60 = indicators.get("ma60")
    macd = indicators.get("macd")
    macd_signal = indicators.get("macdSignal")
    rr = reward_risk.get("ratioToSecondTarget")
    score = max(0, min(100, 100 - (risk.get("score") or 50)))

    macd_bullish = macd is not None and macd_signal is not None and macd > macd_signal
    macd_bearish = macd is not None and macd_signal is not None and macd < macd_signal
    trend_weak = (ma20 is not None and close < ma20) or macd_bearish
    data_status = quality.get("status")

    if data_status == "poor":
        status = "avoid"
        reason = "데이터 부족으로 분석 신뢰도가 낮아 신규 판단은 보류하는 편이 적절합니다."
    elif ma60 and close < ma60 and macd_bearish and (rr is None or rr < 1.0):
        status = "avoid"
        reason = "중기 추세가 약하고 손익비가 부족해 신규 진입 매력은 낮습니다."
    elif (risk.get("score") or 0) >= 70 or (rsi is not None and rsi > 75) or (stochastic_k is not None and stochastic_k > 85) or (ma20 is not None and close < ma20):
        status = "caution"
        reason = "위험 신호가 높아졌거나 주요 지지선 아래에 있어 리스크 관리가 우선입니다."
    elif (
        (risk.get("score") or 100) < 45
        and rr is not None
        and rr >= 1.5
        and ma20 is not None
        and close > ma20
        and macd_bullish
        and rsi is not None
        and 40 <= rsi <= 65
    ):
        status = "candidate"
        reason = "추세, 리스크, 손익비 조건이 비교적 양호해 매수 후보로 볼 수 있습니다."
    elif (risk.get("score") or 100) < 60 and rr is not None and rr >= 1.3 and not trend_weak and (rsi is None or rsi <= 70):
        status = "split_buy"
        reason = "추세는 유지되고 있지만 일부 확인이 필요해 분할 접근이 더 안정적일 수 있습니다."
    elif trend_weak or rr is None or rr < 1.5 or (rsi is not None and 65 <= rsi <= 75):
        status = "watch"
        reason = "방향성이 애매하거나 손익비가 충분하지 않아 신규 진입보다 확인이 우선입니다."
    else:
        status = "watch"
        reason = "조건이 혼재되어 있어 지지선과 목표가 사이의 움직임을 더 확인하는 편이 좋습니다."

    if rr is not None and rr < 1.5 and status in {"candidate", "split_buy"}:
        status = "watch"
        reason = "손익비가 1.5 미만이라 신규 진입 매력은 제한적으로 봅니다."

    suitability = calculate_buy_suitability(close, indicators, risk, reward_risk, quality, status)
    return {
        "status": status,
        "label": LABELS[status],
        "score": round(score),
        "reason": reason,
        "buySuitabilityPercent": suitability["percent"],
        "buySuitability": suitability,
    }


def calculate_buy_suitability(close: float, indicators: dict, risk: dict, reward_risk: dict, quality: dict, status: str) -> dict:
    ma20 = indicators.get("ma20")
    ma60 = indicators.get("ma60")
    ma200 = indicators.get("ma200")
    macd = indicators.get("macd")
    macd_signal = indicators.get("macdSignal")
    rsi = indicators.get("rsi")
    stochastic_k = indicators.get("stochasticK")
    adx = indicators.get("adx")
    plus_di = indicators.get("plusDI")
    minus_di = indicators.get("minusDI")
    mfi = indicators.get("mfi")
    obv_trend = indicators.get("obvTrend")
    support20 = indicators.get("support20")
    volume_ratio = indicators.get("volumeRatio") or 1
    rr = reward_risk.get("ratioToSecondTarget")
    risk_score = risk.get("score") or 50

    trend_score = 0
    if ma20 is not None and close > ma20:
        trend_score += 8
    if ma20 is not None and ma60 is not None and ma20 >= ma60:
        trend_score += 7
    if ma60 is not None and ma200 is not None and ma60 >= ma200:
        trend_score += 5
    if macd is not None and macd_signal is not None and macd > macd_signal:
        trend_score += 6
    if adx is not None and adx >= 20 and plus_di is not None and minus_di is not None and plus_di > minus_di:
        trend_score += 4
    trend_score = min(30, trend_score)

    momentum_score = 0
    if rsi is not None:
        if 45 <= rsi <= 62:
            momentum_score += 12
        elif 40 <= rsi <= 65:
            momentum_score += 10
        elif 35 <= rsi <= 70:
            momentum_score += 6
        elif rsi > 75 or rsi < 30:
            momentum_score += 1
        else:
            momentum_score += 3
    if stochastic_k is not None:
        momentum_score += 5 if 20 <= stochastic_k <= 80 else 2
    if mfi is not None:
        momentum_score += 3 if 35 <= mfi <= 75 else 1
    momentum_score = min(20, momentum_score)

    if rr is None:
        reward_score = 4
    elif rr >= 2:
        reward_score = 20
    elif rr >= 1.5:
        reward_score = 16
    elif rr >= 1.2:
        reward_score = 11
    elif rr >= 1:
        reward_score = 7
    else:
        reward_score = 2

    if risk_score <= 34:
        risk_control_score = 20
    elif risk_score <= 50:
        risk_control_score = 15
    elif risk_score <= 69:
        risk_control_score = 9
    else:
        risk_control_score = 3

    structure_score = 0
    if 0.8 <= volume_ratio <= 1.8:
        structure_score += 3
    elif volume_ratio > 1.8:
        structure_score += 2
    if obv_trend is not None and obv_trend > 0:
        structure_score += 3
    if support20 is not None and close > support20:
        structure_score += 4
    structure_score = min(10, structure_score)

    percent = trend_score + momentum_score + reward_score + risk_control_score + structure_score
    if quality.get("status") == "partial":
        percent -= 8
    elif quality.get("status") == "poor":
        percent -= 25

    caps = {"avoid": 25, "caution": 45, "watch": 64, "split_buy": 78, "candidate": 90}
    percent = max(0, min(caps.get(status, 70), round(percent)))

    if percent >= 75:
        label = "높음"
        description = "현재 지표 조합은 매수 후보 검토에 비교적 우호적입니다. 그래도 손절 기준과 분할 접근을 전제로 봐야 합니다."
    elif percent >= 60:
        label = "보통 이상"
        description = "일부 조건은 긍정적이지만 손익비, 과열, 지지 확인을 함께 봐야 합니다."
    elif percent >= 45:
        label = "중립"
        description = "조건이 혼재되어 있어 신규 진입보다 확인 절차가 더 중요합니다."
    else:
        label = "낮음"
        description = "현재 조건만 보면 신규 진입 매력은 제한적이며 관망 또는 리스크 관리가 우선입니다."

    return {
        "percent": percent,
        "label": label,
        "description": description,
        "factors": [
            {"name": "추세", "score": round(trend_score), "maxScore": 30},
            {"name": "모멘텀", "score": round(momentum_score), "maxScore": 20},
            {"name": "손익비", "score": round(reward_score), "maxScore": 20},
            {"name": "리스크", "score": round(risk_control_score), "maxScore": 20},
            {"name": "수급/지지", "score": round(structure_score), "maxScore": 10},
        ],
        "note": "이 수치는 매수 권유나 수익 확률이 아니라 현재 지표 조건 충족도를 0~100으로 환산한 값입니다.",
    }


def make_rule_based_summary(decision: dict, close: float, indicators: dict, reward_risk: dict, quality: dict) -> str:
    status = decision.get("status")
    if status == "candidate":
        text = "추세, 리스크, 손익비가 비교적 양호한 구간이에요. 다만 한 번에 진입하기보다 손절가를 기준으로 분할 접근하는 편이 안정적입니다."
    elif status == "split_buy":
        text = "추세는 유지되고 있지만 일부 과열 신호가 있을 수 있어요. 현재가 추격보다 눌림 구간에서 나눠 접근하는 전략이 더 적절할 수 있습니다."
    elif status == "caution":
        text = "위험 신호가 높아진 구간이에요. 변동성이 커질 수 있으므로 신규 진입보다는 리스크 관리가 우선입니다."
    elif status == "avoid":
        text = "현재 조건에서는 신규 진입 매력이 낮습니다. 추세 회복이나 손익비 개선을 확인한 뒤 다시 분석하는 편이 좋습니다."
    else:
        text = "방향성이 애매하거나 손익비가 충분하지 않아요. 신규 진입보다는 목표가와 지지선 사이의 움직임을 확인하는 편이 좋습니다."

    rsi = indicators.get("rsi")
    ma20 = indicators.get("ma20")
    adx = indicators.get("adx")
    plus_di = indicators.get("plusDI")
    minus_di = indicators.get("minusDI")
    mfi = indicators.get("mfi")
    rr = reward_risk.get("ratioToSecondTarget")
    additions: list[str] = []
    if rsi is not None and rsi > 70:
        additions.append("RSI가 높은 편이라 과열 가능성도 함께 봐야 합니다.")
    if ma20 is not None and close < ma20:
        additions.append("현재가가 MA20 아래에 있어 단기 추세 약화 신호가 있습니다.")
    if rr is not None and rr < 1.5:
        additions.append("손익비가 충분하지 않아 신규 진입 매력 낮음으로 해석할 수 있습니다.")
    if adx is not None and adx >= 25 and plus_di is not None and minus_di is not None:
        if plus_di > minus_di:
            additions.append("ADX 기준 추세 강도는 살아 있는 편입니다.")
        else:
            additions.append("ADX 기준 하락 방향의 추세 압력이 강해질 수 있습니다.")
    if mfi is not None and mfi > 80:
        additions.append("MFI가 높은 편이라 자금 흐름 과열 가능성도 확인해야 합니다.")
    if quality.get("status") == "poor":
        additions.append("데이터 신뢰도가 낮아 결과를 보수적으로 해석해야 합니다.")
    return " ".join([text, *additions])
