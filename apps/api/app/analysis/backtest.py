from __future__ import annotations

import pandas as pd

from app.core.utils import safe_float


def run_backtest(frame: pd.DataFrame) -> dict:
    if len(frame) < 80:
        return {
            "period": "2y",
            "sampleCount": 0,
            "winRate": 0,
            "averageReturnPercent": 0,
            "maxLossPercent": 0,
            "averageHoldingDays": 0,
            "reliability": "매우 낮음",
            "warning": "표본 수가 부족해 신뢰도가 낮습니다.",
        }

    trades: list[dict] = []
    df = frame.tail(504).reset_index(drop=True)
    i = 60
    while i < len(df) - 16:
        row = df.iloc[i]
        close = row.get("Close")
        ma20 = row.get("MA20")
        macd = row.get("MACD")
        signal = row.get("MACDSignal")
        rsi = row.get("RSI")
        volume_ratio = row.get("VolumeRatio")
        atr = row.get("ATR") or close * 0.03
        if pd.notna(close) and pd.notna(ma20) and pd.notna(macd) and pd.notna(signal) and pd.notna(rsi):
            entry_signal = close > ma20 and macd > signal and 40 <= rsi <= 65 and (volume_ratio or 0) >= 1.0
            if entry_signal:
                entry = close
                target = entry + atr * 1.2
                stop = entry - atr * 1.2
                exit_price = df.iloc[min(i + 15, len(df) - 1)].get("Close")
                holding_days = 15
                outcome = "time"
                for j in range(i + 1, min(i + 16, len(df))):
                    next_row = df.iloc[j]
                    # Same-day ambiguity is treated conservatively by checking stop first.
                    if next_row.get("Low") <= stop:
                        exit_price = stop
                        holding_days = j - i
                        outcome = "loss"
                        break
                    if next_row.get("High") >= target:
                        exit_price = target
                        holding_days = j - i
                        outcome = "win"
                        break
                return_pct = ((exit_price - entry) / entry) * 100 if entry else 0
                trades.append({"return": return_pct, "holding": holding_days, "outcome": outcome})
                i += holding_days
                continue
        i += 1

    sample_count = len(trades)
    wins = len([trade for trade in trades if trade["return"] > 0])
    win_rate = wins / sample_count * 100 if sample_count else 0
    average_return = sum(trade["return"] for trade in trades) / sample_count if sample_count else 0
    max_loss = min([trade["return"] for trade in trades], default=0)
    average_holding = sum(trade["holding"] for trade in trades) / sample_count if sample_count else 0

    if sample_count >= 30:
        reliability = "보통 이상"
        warning = None
    elif sample_count >= 20:
        reliability = "보통"
        warning = None
    elif sample_count >= 10:
        reliability = "낮음"
        warning = "표본 수가 부족해 신뢰도가 낮습니다."
    else:
        reliability = "매우 낮음"
        warning = "표본 수가 부족해 신뢰도가 낮습니다."

    return {
        "period": "2y",
        "sampleCount": sample_count,
        "winRate": safe_float(win_rate, 1),
        "averageReturnPercent": safe_float(average_return, 2),
        "maxLossPercent": safe_float(max_loss, 2),
        "averageHoldingDays": round(average_holding),
        "reliability": reliability,
        "warning": warning,
    }
