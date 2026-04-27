from __future__ import annotations


def build_scenarios(close: float, previous_close: float | None, indicators: dict, strategy: dict, risk: dict, reward_risk: dict) -> list[dict]:
    up = 40
    sideways = 35
    down = 25

    macd = indicators.get("macd")
    macd_signal = indicators.get("macdSignal")
    ma20 = indicators.get("ma20")
    ma60 = indicators.get("ma60")
    rsi = indicators.get("rsi")
    volume_ratio = indicators.get("volumeRatio") or 1
    rr = reward_risk.get("ratioToSecondTarget")

    if macd is not None and macd_signal is not None and macd > macd_signal:
        up += 8
    if ma20 is not None and close > ma20:
        up += 7
    if ma20 is not None and ma60 is not None and ma20 > ma60:
        up += 5
    if rsi is not None and rsi > 70:
        down += 8
        up -= 4
    if ma20 is not None and close < ma20:
        down += 10
    if rr is not None and rr < 1.0:
        down += 8
    if (risk.get("score") or 0) > 70:
        down += 12
    if previous_close is not None and volume_ratio > 1.5 and close > previous_close:
        up += 5
    if previous_close is not None and volume_ratio > 1.5 and close < previous_close:
        down += 8

    up = max(5, up)
    sideways = max(5, sideways)
    down = max(5, down)
    total = up + sideways + down
    up_pct = round(up / total * 100)
    down_pct = round(down / total * 100)
    sideways_pct = 100 - up_pct - down_pct

    return [
        {
            "name": "상승 시나리오",
            "probability": up_pct,
            "condition": "1차 목표가를 거래량과 함께 돌파",
            "response": "일부 익절 후 나머지는 2차 목표까지 추적하는 방식이 더 안정적일 수 있습니다.",
            "checkPrice": strategy.get("firstTarget"),
        },
        {
            "name": "횡보 시나리오",
            "probability": sideways_pct,
            "condition": "현재가와 MA20 사이에서 방향성 부족",
            "response": "추가 매수보다 지지 확인을 우선하고 손절 기준을 유지합니다.",
            "checkPrice": ma20,
        },
        {
            "name": "하락 시나리오",
            "probability": down_pct,
            "condition": "손절가 또는 MA20 이탈",
            "response": "손실 확대 방지를 위해 비중 축소나 관망을 고려합니다.",
            "checkPrice": strategy.get("stopLoss"),
        },
    ]
