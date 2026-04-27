from __future__ import annotations

import math

from app.core.utils import safe_float


RISK_PROFILE_MAP = {
    "conservative": 1.0,
    "balanced": 1.5,
    "aggressive": 2.0,
}


def build_strategy(close: float, indicators: dict) -> dict:
    atr = indicators.get("atr") or close * 0.035
    ma20 = indicators.get("ma20") or close
    rsi = indicators.get("rsi")
    macd = indicators.get("macd")
    macd_signal = indicators.get("macdSignal")
    ma60 = indicators.get("ma60") or ma20

    macd_bullish = macd is not None and macd_signal is not None and macd > macd_signal
    trend_bullish = close > ma20 and ma20 >= ma60 and macd_bullish
    trend_weak = close < ma20 and macd is not None and macd_signal is not None and macd < macd_signal
    overheated = rsi is not None and rsi > 70

    entry_price = close
    if overheated:
        entry_price = min(close, ma20 + atr * 0.3)
    if trend_weak:
        entry_price = ma20

    first_buy_zone = entry_price - atr * 0.5
    second_buy_zone = entry_price - atr
    first_target = entry_price + atr * 1.2
    second_target = entry_price + atr * 2.2
    base_stop = entry_price - atr * 1.2
    ma_reference_stop = ma20 - atr * 0.5
    stop_loss = min(base_stop, ma_reference_stop) if ma20 < entry_price and base_stop > ma_reference_stop else base_stop

    if trend_weak:
        plan = [
            {
                "step": "관망",
                "condition": "종가가 MA20을 회복하고 MACD 약세가 완화될 때까지 신규 진입 계획을 보류",
                "weight": 0,
            }
        ]
        plan_message = "현재는 신규 매수 계획을 만들기보다 관망이 우선입니다."
    elif overheated:
        plan = [
            {"step": "1차", "condition": "현재가 추격보다 눌림 후 지지 확인", "weight": 30},
            {"step": "2차", "condition": "MA20 근처에서 반등 흐름 확인", "weight": 40},
            {"step": "3차", "condition": "1차 목표가 돌파와 거래량 증가 확인", "weight": 30},
        ]
        plan_message = "일부 과열 신호가 있어 눌림 확인 후 분할 접근이 더 안정적일 수 있습니다."
    elif trend_bullish:
        plan = [
            {"step": "1차", "condition": "진입 기준가 근처에서 지지될 때", "weight": 50},
            {"step": "2차", "condition": "MA20 근처 눌림 후 반등 확인", "weight": 30},
            {"step": "3차", "condition": "1차 목표가 돌파 후 거래량 증가 확인", "weight": 20},
        ]
        plan_message = "추세 조건은 비교적 양호하지만 손절 기준을 먼저 정하고 분할 접근하는 편이 안정적입니다."
    else:
        plan = [
            {"step": "1차", "condition": "진입 기준가 부근에서 거래량과 지지를 확인", "weight": 40},
            {"step": "2차", "condition": "MA20 위에서 종가가 유지될 때", "weight": 35},
            {"step": "3차", "condition": "MACD 개선과 목표가 돌파 확인", "weight": 25},
        ]
        plan_message = "방향성이 완전히 강하지 않으므로 확인 후 나눠 접근하는 편이 더 적절할 수 있습니다."

    return {
        "entryPrice": safe_float(entry_price, 4),
        "firstBuyZone": safe_float(first_buy_zone, 4),
        "secondBuyZone": safe_float(second_buy_zone, 4),
        "firstTarget": safe_float(first_target, 4),
        "secondTarget": safe_float(second_target, 4),
        "stopLoss": safe_float(max(stop_loss, 0.01), 4),
        "invalidationCondition": "종가 기준 MA20 이탈, MACD 약세 전환, 손절가 이탈, 또는 거래량 증가를 동반한 장대 음봉이 동시에 확인되면 전략 무효로 봅니다.",
        "plan": plan,
        "message": plan_message,
    }


def calculate_reward_risk(strategy: dict) -> dict:
    entry = strategy.get("entryPrice") or 0
    stop = strategy.get("stopLoss") or 0
    first = strategy.get("firstTarget") or 0
    second = strategy.get("secondTarget") or 0
    risk = entry - stop
    reward1 = first - entry
    reward2 = second - entry
    ratio1 = reward1 / risk if risk > 0 else None
    ratio2 = reward2 / risk if risk > 0 else None

    if ratio2 is None:
        label = "계산 불가"
        description = "손절 기준 또는 목표가 계산이 충분하지 않아 손익비를 계산하기 어렵습니다."
    elif ratio2 >= 2.0:
        label = "양호"
        description = "2차 목표 기준 손익비가 비교적 양호합니다. 다만 손절 기준을 먼저 지키는 전제가 필요합니다."
    elif ratio2 >= 1.5:
        label = "보통 이상"
        description = "2차 목표 기준 손익비는 보통 이상이나, 1차 목표 기준 매력은 함께 확인해야 합니다."
    elif ratio2 >= 1.0:
        label = "애매함"
        description = "손익비가 충분히 크지 않아 신규 진입 매력은 제한적일 수 있습니다."
    else:
        label = "불리함"
        description = "기대 보상보다 손실 위험이 커질 수 있어 신규 진입 매력 낮음으로 봅니다."

    return {
        "ratioToFirstTarget": safe_float(ratio1, 2),
        "ratioToSecondTarget": safe_float(ratio2, 2),
        "label": label,
        "description": description,
    }


def calculate_position_sizing(
    capital_krw: float,
    risk_profile: str,
    strategy: dict,
    exchange_rate: float,
) -> dict:
    risk_percent = RISK_PROFILE_MAP.get(risk_profile, RISK_PROFILE_MAP["balanced"])
    entry = strategy.get("entryPrice") or 0
    stop = strategy.get("stopLoss") or 0
    risk_amount = capital_krw * (risk_percent / 100)
    risk_per_share = max(entry - stop, 0)
    risk_per_share_krw = risk_per_share * exchange_rate
    price_krw = entry * exchange_rate

    if risk_per_share_krw <= 0 or price_krw <= 0:
        return {
            "capitalKRW": round(capital_krw),
            "riskPercent": risk_percent,
            "riskAmountKRW": round(risk_amount),
            "riskPerShareKRW": None,
            "quantity": 0,
            "referenceQuantity": 0,
            "estimatedCapitalKRW": 0,
            "remainingCashKRW": round(capital_krw),
            "warning": "손절 기준이 충분하지 않아 수량 계산이 어렵습니다.",
        }

    risk_based_quantity = math.floor(risk_amount / risk_per_share_krw)
    capital_based_quantity = math.floor(capital_krw / price_krw)
    quantity = max(0, min(risk_based_quantity, capital_based_quantity))
    reference_quantity = max(1, min(max(1, risk_based_quantity), max(1, capital_based_quantity))) if capital_based_quantity > 0 else 0
    estimated = quantity * price_krw
    warning = None
    if quantity == 0:
        warning = "입력한 투자금과 리스크 기준으로는 1주 매수도 부담이 클 수 있습니다. 최소 1주 기준 참고값만 확인하세요."
    elif risk_based_quantity < capital_based_quantity:
        warning = "리스크 기준 수량이 투자금 기준보다 작아 일부 현금이 남습니다."
    elif quantity * risk_per_share_krw > risk_amount * 1.05:
        warning = "손절 시 예상 손실이 설정한 리스크 한도를 넘을 수 있습니다."

    return {
        "capitalKRW": round(capital_krw),
        "riskPercent": risk_percent,
        "riskAmountKRW": round(risk_amount),
        "riskPerShareKRW": round(risk_per_share_krw),
        "quantity": quantity,
        "referenceQuantity": reference_quantity,
        "estimatedCapitalKRW": round(estimated),
        "remainingCashKRW": round(capital_krw - estimated),
        "warning": warning,
    }


def calculate_profit_loss(strategy: dict, quantity: int, exchange_rate: float) -> dict:
    entry = strategy.get("entryPrice") or 0
    first = strategy.get("firstTarget") or 0
    second = strategy.get("secondTarget") or 0
    stop = strategy.get("stopLoss") or 0
    q = max(quantity, 0)
    invested = entry * exchange_rate * q

    first_profit = (first - entry) * exchange_rate * q
    second_profit = (second - entry) * exchange_rate * q
    stop_loss = (stop - entry) * exchange_rate * q

    return {
        "firstTargetProfitKRW": round(first_profit),
        "secondTargetProfitKRW": round(second_profit),
        "stopLossLossKRW": round(stop_loss),
        "firstTargetReturnPercent": safe_float((first_profit / invested) * 100 if invested else 0, 2),
        "secondTargetReturnPercent": safe_float((second_profit / invested) * 100 if invested else 0, 2),
        "stopLossReturnPercent": safe_float((stop_loss / invested) * 100 if invested else 0, 2),
    }
