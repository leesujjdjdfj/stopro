from __future__ import annotations


def interpret_fundamentals(raw: dict) -> dict:
    fields = ["marketCap", "trailingPE", "forwardPE", "eps", "profitMargin", "revenueGrowth", "debtToEquity"]
    data_available = any(raw.get(field) is not None for field in fields)
    notes: list[str] = []

    trailing_pe = raw.get("trailingPE")
    eps = raw.get("eps")
    debt_to_equity = raw.get("debtToEquity")
    profit_margin = raw.get("profitMargin")

    if not data_available:
        notes.append("기본적 지표 데이터가 부족합니다.")
    else:
        if trailing_pe is not None and trailing_pe > 45:
            notes.append("PER이 높은 편이라 밸류에이션 부담을 확인해야 합니다.")
        if eps is not None and eps < 0:
            notes.append("적자 구간일 수 있어 이익 안정성 확인이 필요합니다.")
        if debt_to_equity is not None and debt_to_equity > 120:
            notes.append("부채비율이 높아 재무 리스크 확인이 필요합니다.")
        if profit_margin is not None and profit_margin < 0:
            notes.append("수익성이 낮거나 적자 가능성이 있어 보조지표로만 활용해야 합니다.")
        if not notes:
            notes.append("무료 데이터 기준으로 확인 가능한 기본 지표에는 극단적인 경고가 많지 않습니다.")

    return {**raw, "dataAvailable": data_available, "notes": notes}
