from __future__ import annotations

import math
from typing import Any

import pandas as pd

from app.core.utils import clean_json, safe_float, safe_int


DISCLAIMER = "본 분석은 참고용이며 투자 판단과 책임은 사용자 본인에게 있습니다."


LABEL_BY_SCORE = [
    (80, "매수 후보", "positive"),
    (65, "분할 접근", "cautious"),
    (45, "관망", "neutral"),
    (25, "주의", "warning"),
    (0, "회피", "danger"),
]


def build_investment_insight(
    *,
    ticker: str,
    name: str,
    currency: str,
    frame: pd.DataFrame,
    current_price: float,
    previous_close: float | None,
    indicators: dict,
    strategy: dict,
    reward_risk: dict,
    risk: dict,
    quality: dict,
    support_resistance: dict,
    quote: dict,
    news_analysis: dict | None,
) -> dict:
    prepared = _prepare_frame(frame)
    latest = prepared.iloc[-1] if not prepared.empty else {}
    support = (support_resistance or {}).get("support") or {}
    resistance = (support_resistance or {}).get("resistance") or {}
    support_price = _first_number(support.get("price"), indicators.get("support60"), indicators.get("support20"), strategy.get("stopLoss"))
    resistance_price = _first_number(resistance.get("price"), indicators.get("resistance60"), indicators.get("resistance20"), strategy.get("secondTarget"))
    stop_loss_guide = _stop_loss_guide(current_price, support_price, indicators, strategy)

    trend = _trend_score(prepared, current_price, indicators, currency)
    momentum = _momentum_score(prepared, indicators)
    reward = _reward_risk_score(current_price, support_price, resistance_price, stop_loss_guide, support, resistance, indicators, currency)
    risk_control = _risk_control_score(prepared, current_price, previous_close, indicators, quote, currency)
    volume_support = _volume_support_score(prepared, current_price, previous_close, indicators, support, resistance, currency)

    technical_score = _clamp(trend["score"] + momentum["score"] + reward["score"] + risk_control["score"] + volume_support["score"], 0, 100)
    news_section = _news_score(news_analysis)
    news_score = news_section["score"]
    if news_section["confidence"] == "low":
        news_score = round(news_score * 0.5)
    total_score = _clamp(technical_score + news_score, 0, 100)
    if quality.get("status") == "poor":
        total_score = min(total_score, 50)
    final_label, tone = _label_for_score(total_score)

    score_breakdown = [
        _breakdown("trend", "추세", trend, 25),
        _breakdown("momentum", "모멘텀", momentum, 20),
        _breakdown("rewardRisk", "손익비", reward, 20),
        _breakdown("risk", "리스크", risk_control, 20),
        _breakdown("volumeSupport", "수급/지지", volume_support, 15),
        {
            "key": "news",
            "name": "뉴스/이슈",
            "score": news_score,
            "maxScore": 20,
            "label": news_section["label"],
            "summary": news_section["summary"],
            "details": news_section["details"],
        },
    ]

    technical_vs_news = _technical_vs_news(technical_score, news_section)
    positive_points = _positive_points(trend, momentum, reward, risk_control, volume_support, news_section)
    negative_points = _negative_points(trend, momentum, reward, risk_control, volume_support, news_section)
    watch_points = _watch_points(current_price, support_price, resistance_price, indicators, reward, news_section, currency)
    scenarios = _build_scenarios(support_price, resistance_price, indicators, currency)
    summary = _summary(final_label, trend, momentum, reward, risk_control, volume_support, news_section, technical_vs_news)

    result = {
        "finalLabel": final_label,
        "score": safe_int(total_score),
        "tone": tone,
        "oneLine": _one_line(final_label, reward, news_section),
        "summary": summary,
        "technicalScore": safe_int(technical_score),
        "newsScore": safe_int(news_score),
        "totalScore": safe_int(total_score),
        "confidence": _overall_confidence(quality, news_section),
        "scoreBreakdown": score_breakdown,
        "positivePoints": positive_points,
        "negativePoints": negative_points,
        "watchPoints": watch_points,
        "riskManagement": {
            "supportPrice": safe_float(support_price, 4),
            "resistancePrice": safe_float(resistance_price, 4),
            "stopLossGuide": safe_float(stop_loss_guide, 4),
            "invalidationCondition": "종가 기준 주요 지지선 이탈, MA20 재이탈, MACD 약세 전환이 함께 확인되면 전략을 재검토합니다.",
            "supportDistancePercent": safe_float(_distance_percent(support_price, current_price), 2),
            "resistanceDistancePercent": safe_float(_distance_percent(resistance_price, current_price), 2),
        },
        "newsInsight": news_section["insight"],
        "technicalVsNews": technical_vs_news,
        "newsChartAlignment": technical_vs_news,
        "scenarios": scenarios,
        "disclaimer": DISCLAIMER,
        "meta": {
            "ticker": ticker,
            "name": name,
            "currency": currency,
        },
    }
    return clean_json(result)


def build_technical_context(
    *,
    current_price: float,
    daily_change_percent: float | None,
    indicators: dict,
    reward_risk: dict,
    risk: dict,
    support_resistance: dict,
) -> dict:
    support = (support_resistance or {}).get("support") or {}
    resistance = (support_resistance or {}).get("resistance") or {}
    macd = indicators.get("macd")
    macd_signal = indicators.get("macdSignal")
    return clean_json(
        {
            "currentPrice": safe_float(current_price, 4),
            "dailyChangePercent": safe_float(daily_change_percent, 2),
            "ma20": indicators.get("ma20"),
            "ma60": indicators.get("ma60"),
            "ma200": indicators.get("ma200"),
            "rsi": indicators.get("rsi"),
            "macdStatus": "bullish" if macd is not None and macd_signal is not None and macd > macd_signal else "bearish_or_neutral",
            "supportPrice": support.get("price"),
            "resistancePrice": resistance.get("price"),
            "rewardRiskRatio": reward_risk.get("ratioToSecondTarget"),
            "riskScore": risk.get("score"),
        }
    )


def _trend_score(frame: pd.DataFrame, close: float, indicators: dict, currency: str) -> dict:
    ma20 = indicators.get("ma20")
    ma60 = indicators.get("ma60")
    ma200 = indicators.get("ma200")
    recent_high = _rolling_value(frame, "High", 20, "max")
    five_day_return = _period_return(frame, 5)
    score = 0
    details = []

    score += _add_condition(details, "현재가 > MA20", close > ma20 if ma20 else False, f"{_price(close, currency)} > {_price(ma20, currency)}", "단기 추세는 유지", 6)
    score += _add_condition(details, "MA20 > MA60", ma20 > ma60 if ma20 and ma60 else False, f"{_price(ma20, currency)} > {_price(ma60, currency)}", "중기 추세 정렬", 6)
    score += _add_condition(details, "MA60 > MA200", ma60 > ma200 if ma60 and ma200 else False, f"{_price(ma60, currency)} > {_price(ma200, currency)}", "장기 추세 우호", 5)
    near_high = bool(recent_high and close >= recent_high * 0.95)
    score += _add_condition(details, "최근 20일 고점 5% 이내", near_high, f"20일 고점 {_price(recent_high, currency)}", "상단 회복 흐름", 4)
    score += _add_condition(details, "최근 5일 수익률 양수", five_day_return is not None and five_day_return > 0, _percent(five_day_return), "단기 가격 흐름 개선", 4)

    if ma20 and close < ma20:
        score -= 5
        details.append(_detail("현재가 < MA20", True, f"{_price(close, currency)} < {_price(ma20, currency)}", "단기 추세 약화"))
    if ma20 and ma60 and ma20 < ma60:
        score -= 5
        details.append(_detail("MA20 < MA60", True, f"{_price(ma20, currency)} < {_price(ma60, currency)}", "중기 추세 부담"))
    if ma60 and close < ma60:
        score -= 7
        details.append(_detail("현재가 < MA60", True, f"{_price(close, currency)} < {_price(ma60, currency)}", "중기 지지 확인 필요"))

    score = _clamp(score, 0, 25)
    return {"score": score, "label": _score_label(score, 25), "summary": _trend_summary(score, ma20, ma60, close), "details": details}


def _momentum_score(frame: pd.DataFrame, indicators: dict) -> dict:
    rsi = indicators.get("rsi")
    macd = indicators.get("macd")
    signal = indicators.get("macdSignal")
    stochastic_k = indicators.get("stochasticK")
    stochastic_d = indicators.get("stochasticD")
    prev = frame.iloc[-2] if len(frame) >= 2 else {}
    hist = (macd - signal) if macd is not None and signal is not None else None
    prev_hist = _number(prev.get("MACD")) - _number(prev.get("MACDSignal")) if _number(prev.get("MACD")) is not None and _number(prev.get("MACDSignal")) is not None else None
    prev_k = _number(prev.get("StochasticK"))
    prev_d = _number(prev.get("StochasticD"))
    score = 0
    details = []

    if rsi is not None:
        if 40 <= rsi <= 65:
            score += 7
            rsi_impact = "건전한 모멘텀 구간"
        elif 65 < rsi <= 75:
            score += 3
            rsi_impact = "상승 탄력은 있으나 추격 진입 주의"
        elif rsi > 75:
            score -= 5
            rsi_impact = "과열 신호가 강해 추격 진입 주의"
        elif rsi < 30:
            score += 2
            rsi_impact = "낙폭 과대 가능성이나 추세 확인 필요"
        else:
            rsi_impact = "중립 구간"
        details.append(_detail("RSI", 40 <= rsi <= 65, _percent_value(rsi), rsi_impact))

    score += _add_condition(details, "MACD > Signal", macd > signal if macd is not None and signal is not None else False, f"{safe_float(macd, 4)} / {safe_float(signal, 4)}", "단기 반등 신호", 6)
    score += _add_condition(details, "MACD Histogram 증가", hist is not None and prev_hist is not None and hist > prev_hist, f"{safe_float(prev_hist, 4)} → {safe_float(hist, 4)}", "모멘텀 개선", 4)
    cross = stochastic_k is not None and stochastic_d is not None and prev_k is not None and prev_d is not None and prev_k <= prev_d and stochastic_k > stochastic_d
    score += _add_condition(details, "Stochastic K/D 상향 돌파", cross, f"K {safe_float(stochastic_k, 2)} / D {safe_float(stochastic_d, 2)}", "단기 매수세 개선", 3)

    score = _clamp(score, 0, 20)
    label = "과열" if rsi is not None and rsi > 75 else "개선" if score >= 14 else "중립" if score >= 7 else "약함"
    summary = "MACD와 RSI 기준 모멘텀을 확인했습니다."
    if label == "과열":
        summary = "RSI가 높은 편이라 추격 진입은 주의가 필요합니다."
    elif label == "개선":
        summary = "MACD와 단기 모멘텀은 개선 흐름으로 볼 수 있습니다."
    elif label == "약함":
        summary = "모멘텀이 약해 가격 확인이 더 필요합니다."
    return {"score": score, "label": label, "summary": summary, "details": details}


def _reward_risk_score(current: float, support: float | None, resistance: float | None, stop_loss: float | None, support_level: dict, resistance_level: dict, indicators: dict, currency: str) -> dict:
    downside = current - support if support is not None else None
    upside = resistance - current if resistance is not None else None
    ratio = upside / downside if downside and downside > 0 and upside is not None else None
    score = 4
    if support is not None and current < support:
        score = 0
    elif ratio is not None:
        if ratio >= 2:
            score = 20
        elif ratio >= 1.5:
            score = 16
        elif ratio >= 1.2:
            score = 10
        elif ratio >= 1.0:
            score = 6
        else:
            score = 2

    support_distance = _distance_percent(support, current)
    resistance_distance = _distance_percent(resistance, current)
    if resistance_distance is not None and 0 <= resistance_distance < 3:
        score -= 5
    if support_distance is not None and -3 <= support_distance < 0 and indicators.get("ma20") and current >= indicators.get("ma20"):
        score += 3
    score = _clamp(score, 0, 20)
    details = [
        _detail("지지까지 거리", support is not None, _percent(support_distance), "지지선 근접 여부 확인"),
        _detail("저항까지 거리", resistance is not None, _percent(resistance_distance), "상방 여력 확인"),
        _detail("손익비", ratio is not None and ratio >= 1.5, f"{safe_float(ratio, 2)}", "손익비 양호/부족 판단"),
        _detail("손절 기준", stop_loss is not None, _price(stop_loss, currency), "리스크 관리 기준"),
    ]
    label = "양호" if score >= 16 else "보통" if score >= 10 else "애매함" if score >= 6 else "불리함"
    summary = "저항선까지의 기대 여력과 지지선 이탈 리스크를 비교했습니다."
    if resistance_distance is not None and 0 <= resistance_distance < 3:
        summary = "현재가가 저항선에 가까워 신규 진입 매력은 제한적입니다."
    elif ratio is not None and ratio >= 1.5:
        summary = "저항선까지의 기대 여력이 지지선 이탈 리스크보다 큰 편입니다."
    return {"score": score, "label": label, "summary": summary, "details": details, "ratio": safe_float(ratio, 2)}


def _risk_control_score(frame: pd.DataFrame, current: float, previous_close: float | None, indicators: dict, quote: dict, currency: str) -> dict:
    atr = indicators.get("atr") or current * 0.01
    ma20 = indicators.get("ma20")
    distance_high = indicators.get("distanceFrom52WeekHighPercent")
    five_day_return = _period_return(frame, 5)
    latest = frame.iloc[-1] if not frame.empty else {}
    open_price = _number(latest.get("Open"))
    close = _number(latest.get("Close")) or current
    low = _number(latest.get("Low")) or current
    volume_ratio = indicators.get("volumeRatio") or 1
    atr_ratio = (atr / current) * 100 if current else None
    ma20_distance = abs((current - ma20) / ma20 * 100) if ma20 else None
    long_bearish = open_price is not None and close < open_price and ((open_price - close) / max(open_price, 1)) > 0.035 and volume_ratio > 1.8

    score = 0
    if atr_ratio is not None:
        if atr_ratio < 3:
            score += 6
        elif atr_ratio <= 6:
            score += 3
    if ma20_distance is not None:
        if ma20_distance <= 5:
            score += 5
        elif ma20_distance <= 10:
            score += 2
        else:
            score -= 3
    if distance_high is not None and abs(distance_high) <= 5:
        score -= 5
    if five_day_return is not None and five_day_return >= 20:
        score -= 5
    if long_bearish:
        score -= 7
    if current >= low and previous_close is not None and abs((current - previous_close) / previous_close * 100) < 8:
        score += 5
    score = _clamp(score, 0, 20)

    details = [
        _detail("ATR/현재가", atr_ratio is not None and atr_ratio < 6, _percent(atr_ratio), "변동성 보통 여부"),
        _detail("MA20 이격도", ma20_distance is not None and ma20_distance <= 10, _percent(ma20_distance), "단기 과열/이격 확인"),
        _detail("52주 고점 거리", distance_high is not None and abs(distance_high) > 5, _percent(distance_high), "고점 근접 리스크"),
        _detail("최근 5일 수익률", five_day_return is not None and five_day_return < 20, _percent(five_day_return), "단기 급등 여부"),
        _detail("장대음봉+거래량", not long_bearish, f"거래량 {safe_float(volume_ratio, 2)}배", "리스크 관리 우선 신호"),
    ]
    label = "낮음" if score >= 15 else "보통" if score >= 9 else "높음"
    summary = "변동성, 이격도, 고점 근접도를 기준으로 리스크 관리 여지를 확인했습니다."
    if score < 8:
        summary = "변동성 또는 단기 과열 부담이 있어 리스크 관리가 우선입니다."
    return {"score": score, "label": label, "summary": summary, "details": details}


def _volume_support_score(frame: pd.DataFrame, current: float, previous_close: float | None, indicators: dict, support: dict, resistance: dict, currency: str) -> dict:
    latest = frame.iloc[-1] if not frame.empty else {}
    open_price = _number(latest.get("Open"))
    close = _number(latest.get("Close")) or current
    volume_ratio = indicators.get("volumeRatio") or 1
    support_price = support.get("price")
    resistance_price = resistance.get("price")
    support_distance = _distance_percent(support_price, current)
    resistance_distance = _distance_percent(resistance_price, current)
    bullish_candle = open_price is not None and close >= open_price
    bearish_candle = open_price is not None and close < open_price
    score = 0
    details = []
    if 1.0 <= volume_ratio <= 1.8 and bullish_candle:
        score += 5
        details.append(_detail("거래량 동반 상승", True, f"{safe_float(volume_ratio, 2)}배", "거래량이 동반된 상승"))
    else:
        details.append(_detail("거래량 동반 상승", False, f"{safe_float(volume_ratio, 2)}배", "거래량 확인 필요"))
    if volume_ratio > 2.0 and bearish_candle:
        score -= 5
        details.append(_detail("거래량 급증 음봉", True, f"{safe_float(volume_ratio, 2)}배", "거래량 급증에도 가격 하락"))
    if (support.get("touchCount") or 0) >= 3:
        score += 4
    if support_distance is not None and -5 <= support_distance < 0:
        score += 4
    if resistance_distance is not None and 0 <= resistance_distance < 3:
        score -= 4
    details.extend(
        [
            _detail("지지선 touch", (support.get("touchCount") or 0) >= 3, f"{support.get('touchCount') or 0}회", "지지 가격대 신뢰도"),
            _detail("지지선 근처", support_distance is not None and -5 <= support_distance < 0, _percent(support_distance), "지지선 근처"),
            _detail("저항선 근접", resistance_distance is not None and 0 <= resistance_distance < 3, _percent(resistance_distance), "저항선 근접"),
        ]
    )
    score = _clamp(score, 0, 15)
    label = "양호" if score >= 11 else "보통" if score >= 6 else "주의"
    summary = "거래량과 지지/저항 위치를 함께 확인했습니다."
    if resistance_distance is not None and 0 <= resistance_distance < 3:
        summary = "저항선에 가까워 돌파 확인 전에는 보수적 접근이 필요합니다."
    elif support_distance is not None and -5 <= support_distance < 0:
        summary = "지지선 근처라 반등 가능성은 있으나 거래량 확인이 필요합니다."
    return {"score": score, "label": label, "summary": summary, "details": details}


def _news_score(news_analysis: dict | None) -> dict:
    if not news_analysis:
        return {
            "score": 0,
            "label": "데이터 부족",
            "summary": "뉴스 분석을 불러오지 못해 기술적 분석 중심으로 판단했습니다.",
            "confidence": "low",
            "details": [_detail("뉴스 분석", False, "-", "뉴스 API 또는 AI 분석 실패")],
            "insight": _empty_news_insight(),
        }
    sentiment_score = news_analysis.get("sentimentScore")
    score = _clamp(round((sentiment_score or 0) / 5), -20, 20)
    articles_used = len(news_analysis.get("newsItems") or [])
    confidence = news_analysis.get("confidence") or "low"
    if articles_used < 3:
        confidence = "low"
    sentiment = news_analysis.get("sentiment") or "mixed"
    label = {"positive": "긍정", "neutral": "중립", "negative": "부정", "mixed": "혼재"}.get(sentiment, "혼재")
    summary = news_analysis.get("oneLine") or "최근 뉴스 흐름을 보수적으로 확인해야 합니다."
    insight = {
        "sentiment": sentiment,
        "sentimentScore": safe_int(sentiment_score or 0),
        "oneLine": summary,
        "keyIssues": _list(news_analysis.get("keyIssues")),
        "positiveFactors": _list(news_analysis.get("positiveFactors")),
        "negativeFactors": _list(news_analysis.get("negativeFactors")),
        "riskFactors": _list(news_analysis.get("riskFactors")),
        "watchPoints": _list(news_analysis.get("watchPoints")),
        "articlesUsed": articles_used,
        "confidence": confidence,
    }
    details = [
        _detail("뉴스 분위기", sentiment in {"positive", "neutral"}, label, "최근 뉴스의 방향성"),
        _detail("감정 점수", score > 0, str(score), "뉴스 점수를 -20~20으로 환산"),
        _detail("사용 기사 수", articles_used >= 3, f"{articles_used}개", "기사 수가 적으면 신뢰도 낮음"),
    ]
    return {"score": score, "label": label, "summary": summary, "confidence": confidence, "details": details, "insight": insight}


def _technical_vs_news(technical_score: int, news: dict) -> dict:
    score = news.get("score") or 0
    confidence = news.get("confidence")
    sentiment = (news.get("insight") or {}).get("sentiment") or "mixed"
    news_direction = _news_direction(sentiment, score, confidence)
    chart_direction = _chart_direction(technical_score)

    if news_direction == "insufficient" or chart_direction == "insufficient":
        alignment = "insufficient"
        message = "뉴스와 차트 방향성을 판단하기에는 데이터가 부족합니다."
        summary = "뉴스 데이터 신뢰도나 차트 조건이 충분하지 않아 방향성을 단정하기 어렵습니다."
    elif news_direction == "positive" and chart_direction == "bullish":
        alignment = "aligned"
        message = "뉴스와 차트가 같은 방향입니다."
        summary = "뉴스 흐름은 긍정적이고 차트 조건도 상승 조건을 비교적 충족하고 있습니다."
    elif news_direction == "positive" and chart_direction == "weak":
        alignment = "diverged"
        message = "뉴스는 긍정적이지만 차트는 아직 확인이 필요합니다."
        summary = "뉴스는 우호적이지만 가격과 지표가 아직 충분히 따라오지 않아 추가 확인이 필요합니다."
    elif news_direction == "negative" and chart_direction == "bullish":
        alignment = "diverged"
        message = "차트는 반등 중이지만 뉴스 리스크가 남아 있습니다."
        summary = "기술적으로는 개선 신호가 있으나 최근 뉴스 리스크가 남아 보수적 해석이 필요합니다."
    elif news_direction == "negative" and chart_direction == "weak":
        alignment = "aligned"
        message = "뉴스와 차트가 모두 보수적 확인을 요구합니다."
        summary = "뉴스와 차트 모두 리스크 관리가 우선인 방향을 가리킵니다."
    elif news_direction == "mixed" and chart_direction == "mixed":
        alignment = "mixed"
        message = "뉴스와 차트가 모두 혼재되어 있습니다."
        summary = "뉴스와 차트가 모두 뚜렷한 방향을 보이지 않아 지지/저항과 후속 흐름 확인이 필요합니다."
    else:
        alignment = "mixed"
        message = "뉴스와 차트 신호가 혼재되어 있습니다."
        summary = "뉴스와 차트 흐름이 한쪽으로 뚜렷하게 정렬되지 않아 추가 확인이 필요합니다."

    return {
        "alignment": alignment,
        "label": {"aligned": "일치", "diverged": "엇갈림", "mixed": "혼재", "insufficient": "판단 부족"}[alignment],
        "message": message,
        "summary": summary,
        "newsDirection": news_direction,
        "chartDirection": chart_direction,
    }


def _news_direction(sentiment: str, score: int, confidence: str | None) -> str:
    if confidence == "low" and abs(score) < 5:
        return "insufficient"
    if sentiment == "positive" or score >= 8:
        return "positive"
    if sentiment == "negative" or score <= -8:
        return "negative"
    return "mixed"


def _chart_direction(technical_score: int) -> str:
    if technical_score >= 65:
        return "bullish"
    if technical_score <= 44:
        return "weak"
    return "mixed"


def _positive_points(*sections: dict) -> list[str]:
    points = [section["summary"] for section in sections if section.get("score", 0) >= (section.get("maxScore", 20) if "maxScore" in section else 12)]
    if not points:
        points = [section["summary"] for section in sections if section.get("score", 0) >= 10]
    return points[:5] or ["명확한 긍정 요인은 제한적이며, 조건 확인이 우선입니다."]


def _negative_points(*sections: dict) -> list[str]:
    points = [section["summary"] for section in sections if section.get("score", 0) <= 6]
    return points[:5] or ["뚜렷한 위험 신호는 제한적이지만, 손절 기준은 먼저 정해야 합니다."]


def _watch_points(current: float, support: float | None, resistance: float | None, indicators: dict, reward: dict, news: dict, currency: str) -> list[str]:
    points = []
    if resistance:
        points.append(f"저항선 {_price(resistance, currency)} 돌파 후 거래량 유지 여부")
    if support:
        points.append(f"지지선 {_price(support, currency)} 이탈 여부")
    if indicators.get("rsi") is not None and indicators.get("rsi") > 65:
        points.append("RSI 과열 해소 또는 추가 상승 탄력 확인")
    if reward.get("ratio") is not None and reward.get("ratio") < 1.5:
        points.append("손익비 1.5 이상으로 개선되는 가격대 확인")
    points.extend(_list(news.get("insight", {}).get("watchPoints"))[:2])
    return points[:6] or ["가격 반응, 거래량, 후속 뉴스를 함께 확인하세요."]


def _build_scenarios(support: float | None, resistance: float | None, indicators: dict, currency: str) -> list[dict]:
    ma20 = indicators.get("ma20")
    return [
        {
            "name": "상승 시나리오",
            "condition": f"{_price(resistance, currency)} 저항 돌파 + 거래량 유지",
            "interpretation": "단기 추세 개선 가능성",
            "actionGuide": "돌파 확인 전 추격 진입은 주의하고 손절 기준을 먼저 확인합니다.",
        },
        {
            "name": "횡보 시나리오",
            "condition": f"{_price(support, currency)} 지지와 {_price(resistance, currency)} 저항 사이 박스권 유지",
            "interpretation": "방향성 확인 필요",
            "actionGuide": "저항 근처에서는 보수적으로 접근하고 지지선 반응을 확인합니다.",
        },
        {
            "name": "하락 시나리오",
            "condition": f"주요 지지선 또는 MA20({_price(ma20, currency)}) 이탈",
            "interpretation": "리스크 확대 가능성",
            "actionGuide": "손실 확대 방지를 위해 전략을 재검토합니다.",
        },
    ]


def _summary(label: str, trend: dict, momentum: dict, reward: dict, risk_control: dict, volume: dict, news: dict, alignment: dict) -> str:
    return (
        f"현재 조건은 {label}으로 분류됩니다. "
        f"{trend['summary']} {momentum['summary']} {reward['summary']} "
        f"{risk_control['summary']} {volume['summary']} "
        f"뉴스 흐름은 {news['label']}이며, {alignment['summary']} "
        "확정적인 매수/매도 신호가 아니라 가격, 거래량, 뉴스 조건 충족도를 보수적으로 환산한 결과입니다."
    )


def _one_line(label: str, reward: dict, news: dict) -> str:
    if label in {"주의", "회피"}:
        return "위험 신호와 확인 조건이 남아 있어 신규 진입보다 리스크 관리가 우선입니다."
    if label == "관망":
        return "조건이 혼재되어 지지/저항과 뉴스 후속 흐름 확인이 더 필요합니다."
    if reward.get("ratio") is not None and reward.get("ratio") < 1.5:
        return "일부 조건은 양호하지만 손익비가 충분하지 않아 보수적 접근이 필요합니다."
    if news.get("score", 0) < 0:
        return "차트 조건은 일부 개선됐지만 뉴스 리스크가 남아 확인이 필요합니다."
    return "기술 조건과 뉴스 흐름을 함께 보면 후보 검토는 가능하지만 분할 접근과 손절 기준이 전제입니다."


def _breakdown(key: str, name: str, section: dict, max_score: int) -> dict:
    return {
        "key": key,
        "name": name,
        "score": safe_int(section.get("score")),
        "maxScore": max_score,
        "label": section.get("label"),
        "summary": section.get("summary"),
        "details": section.get("details", []),
    }


def _overall_confidence(quality: dict, news: dict) -> str:
    if quality.get("status") == "poor" or news.get("confidence") == "low":
        return "low"
    if quality.get("status") == "partial":
        return "medium"
    return "high" if news.get("confidence") == "high" else "medium"


def _label_for_score(score: int) -> tuple[str, str]:
    for threshold, label, tone in LABEL_BY_SCORE:
        if score >= threshold:
            return label, tone
    return "회피", "danger"


def _prepare_frame(frame: pd.DataFrame) -> pd.DataFrame:
    if frame is None or frame.empty:
        return pd.DataFrame()
    return frame.copy()


def _period_return(frame: pd.DataFrame, days: int) -> float | None:
    if frame.empty or len(frame) <= days:
        return None
    start = _number(frame["Close"].iloc[-days - 1])
    end = _number(frame["Close"].iloc[-1])
    if not start or end is None:
        return None
    return ((end - start) / start) * 100


def _rolling_value(frame: pd.DataFrame, column: str, days: int, method: str) -> float | None:
    if frame.empty or column not in frame:
        return None
    series = pd.to_numeric(frame[column], errors="coerce").dropna().tail(days)
    if series.empty:
        return None
    value = series.max() if method == "max" else series.min()
    return _number(value)


def _stop_loss_guide(current: float, support: float | None, indicators: dict, strategy: dict) -> float | None:
    atr = indicators.get("atr") or current * 0.01
    candidates = [strategy.get("stopLoss")]
    if support:
        candidates.append(support - atr * 0.25)
    values = [value for value in candidates if value is not None and value > 0]
    return max(min(values), 0.01) if values else None


def _distance_percent(level: float | None, current: float) -> float | None:
    if level is None or not current:
        return None
    return ((level - current) / current) * 100


def _first_number(*values: Any) -> float | None:
    for value in values:
        number = _number(value)
        if number is not None and number > 0:
            return number
    return None


def _number(value: Any) -> float | None:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if math.isnan(number) or math.isinf(number):
        return None
    return number


def _add_condition(details: list[dict], condition: str, passed: bool, value: str, impact: str, points: int) -> int:
    details.append(_detail(condition, passed, value, impact))
    return points if passed else 0


def _detail(condition: str, passed: bool, value: str, impact: str) -> dict:
    return {"condition": condition, "passed": bool(passed), "value": value, "impact": impact}


def _score_label(score: int, max_score: int) -> str:
    ratio = score / max(max_score, 1)
    if ratio >= 0.75:
        return "양호"
    if ratio >= 0.5:
        return "보통"
    if ratio >= 0.3:
        return "주의"
    return "약함"


def _trend_summary(score: int, ma20: float | None, ma60: float | None, close: float) -> str:
    if ma20 and close < ma20:
        return "현재가가 MA20 아래라 단기 추세 회복 확인이 필요합니다."
    if score >= 18:
        return "이동평균 배열과 최근 가격 흐름은 비교적 양호합니다."
    if ma20 and ma60 and ma20 < ma60:
        return "MA20과 MA60 정렬이 약해 추세 확인이 필요합니다."
    return "추세 조건은 일부만 충족되어 관망 요소가 남아 있습니다."


def _price(value: float | None, currency: str) -> str:
    if value is None:
        return "-"
    if currency == "KRW":
        return f"{value:,.0f}원"
    return f"${value:,.2f}"


def _percent(value: float | None) -> str:
    if value is None:
        return "-"
    return f"{value:+.2f}%"


def _percent_value(value: float | None) -> str:
    if value is None:
        return "-"
    return f"{value:.2f}"


def _clamp(value: float, low: int, high: int) -> int:
    return int(max(low, min(high, round(value))))


def _list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item).strip() for item in value if str(item).strip()]


def _empty_news_insight() -> dict:
    return {
        "sentiment": "neutral",
        "sentimentScore": 0,
        "oneLine": "뉴스 기반 분석을 사용할 수 없습니다.",
        "keyIssues": [],
        "positiveFactors": [],
        "negativeFactors": [],
        "riskFactors": ["뉴스 데이터 부족"],
        "watchPoints": ["가격과 거래량 중심으로 확인하세요."],
        "articlesUsed": 0,
        "confidence": "low",
    }
