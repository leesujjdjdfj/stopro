from __future__ import annotations

import numpy as np
import pandas as pd

from app.core.utils import safe_float


def add_indicators(history: pd.DataFrame) -> pd.DataFrame:
    df = history.copy()
    close = df["Close"]
    high = df["High"]
    low = df["Low"]
    volume = df["Volume"].replace(0, np.nan)

    delta = close.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.ewm(alpha=1 / 14, min_periods=14, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1 / 14, min_periods=14, adjust=False).mean()
    rs = avg_gain / avg_loss.replace(0, np.nan)
    df["RSI"] = 100 - (100 / (1 + rs))

    ema12 = close.ewm(span=12, adjust=False).mean()
    ema26 = close.ewm(span=26, adjust=False).mean()
    df["MACD"] = ema12 - ema26
    df["MACDSignal"] = df["MACD"].ewm(span=9, adjust=False).mean()

    lowest_low = low.rolling(14, min_periods=14).min()
    highest_high = high.rolling(14, min_periods=14).max()
    df["StochasticK"] = ((close - lowest_low) / (highest_high - lowest_low).replace(0, np.nan)) * 100
    df["StochasticD"] = df["StochasticK"].rolling(3, min_periods=3).mean()

    df["MA20"] = close.rolling(20, min_periods=20).mean()
    df["MA60"] = close.rolling(60, min_periods=60).mean()
    df["MA200"] = close.rolling(200, min_periods=200).mean()

    previous_close = close.shift(1)
    true_range = pd.concat(
        [(high - low), (high - previous_close).abs(), (low - previous_close).abs()],
        axis=1,
    ).max(axis=1)
    df["ATR"] = true_range.ewm(alpha=1 / 14, min_periods=14, adjust=False).mean()

    rolling_mean = close.rolling(20, min_periods=20).mean()
    rolling_std = close.rolling(20, min_periods=20).std()
    df["BollingerUpper"] = rolling_mean + rolling_std * 2
    df["BollingerLower"] = rolling_mean - rolling_std * 2

    df["AverageVolume20"] = volume.rolling(20, min_periods=5).mean()
    df["VolumeRatio"] = df["Volume"] / df["AverageVolume20"].replace(0, np.nan)

    up_move = high.diff()
    down_move = -low.diff()
    plus_dm = np.where((up_move > down_move) & (up_move > 0), up_move, 0.0)
    minus_dm = np.where((down_move > up_move) & (down_move > 0), down_move, 0.0)
    plus_di = 100 * pd.Series(plus_dm, index=df.index).ewm(alpha=1 / 14, min_periods=14, adjust=False).mean() / df["ATR"].replace(0, np.nan)
    minus_di = 100 * pd.Series(minus_dm, index=df.index).ewm(alpha=1 / 14, min_periods=14, adjust=False).mean() / df["ATR"].replace(0, np.nan)
    dx = ((plus_di - minus_di).abs() / (plus_di + minus_di).replace(0, np.nan)) * 100
    df["PlusDI"] = plus_di
    df["MinusDI"] = minus_di
    df["ADX"] = dx.ewm(alpha=1 / 14, min_periods=14, adjust=False).mean()

    typical_price = (high + low + close) / 3
    raw_money_flow = typical_price * df["Volume"].fillna(0)
    positive_flow = raw_money_flow.where(typical_price.diff() > 0, 0)
    negative_flow = raw_money_flow.where(typical_price.diff() < 0, 0)
    money_ratio = positive_flow.rolling(14, min_periods=14).sum() / negative_flow.rolling(14, min_periods=14).sum().replace(0, np.nan)
    df["MFI"] = 100 - (100 / (1 + money_ratio))

    obv_delta = np.where(close.diff() > 0, df["Volume"].fillna(0), np.where(close.diff() < 0, -df["Volume"].fillna(0), 0))
    df["OBV"] = pd.Series(obv_delta, index=df.index).cumsum()
    df["OBVTrend"] = (df["OBV"] - df["OBV"].shift(20)) / df["AverageVolume20"].replace(0, np.nan)

    df["Support20"] = low.rolling(20, min_periods=10).min()
    df["Resistance20"] = high.rolling(20, min_periods=10).max()
    df["Support60"] = low.rolling(60, min_periods=20).min()
    df["Resistance60"] = high.rolling(60, min_periods=20).max()

    high_52w = high.rolling(252, min_periods=min(60, len(df))).max()
    df["DistanceFrom52WeekHighPercent"] = ((close - high_52w) / high_52w.replace(0, np.nan)) * 100
    return df


def latest_indicators(frame: pd.DataFrame) -> dict:
    row = frame.iloc[-1]
    return {
        "rsi": safe_float(row.get("RSI"), 2),
        "macd": safe_float(row.get("MACD"), 4),
        "macdSignal": safe_float(row.get("MACDSignal"), 4),
        "stochasticK": safe_float(row.get("StochasticK"), 2),
        "stochasticD": safe_float(row.get("StochasticD"), 2),
        "ma20": safe_float(row.get("MA20"), 4),
        "ma60": safe_float(row.get("MA60"), 4),
        "ma200": safe_float(row.get("MA200"), 4),
        "atr": safe_float(row.get("ATR"), 4),
        "bollingerUpper": safe_float(row.get("BollingerUpper"), 4),
        "bollingerLower": safe_float(row.get("BollingerLower"), 4),
        "volumeRatio": safe_float(row.get("VolumeRatio"), 2),
        "adx": safe_float(row.get("ADX"), 2),
        "plusDI": safe_float(row.get("PlusDI"), 2),
        "minusDI": safe_float(row.get("MinusDI"), 2),
        "mfi": safe_float(row.get("MFI"), 2),
        "obvTrend": safe_float(row.get("OBVTrend"), 2),
        "support20": safe_float(row.get("Support20"), 4),
        "resistance20": safe_float(row.get("Resistance20"), 4),
        "support60": safe_float(row.get("Support60"), 4),
        "resistance60": safe_float(row.get("Resistance60"), 4),
        "distanceFrom52WeekHighPercent": safe_float(row.get("DistanceFrom52WeekHighPercent"), 2),
    }
