from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from app.core.cache import cache
from app.core.utils import safe_float, safe_int


SUPPORT_RESISTANCE_TTL_SECONDS = 600
LOOKBACK_DAYS = 120
FALLBACK_DAYS = 60
PIVOT_WINDOW = 2
VOLUME_FILTER_RATIO = 0.8


@dataclass
class Pivot:
    price: float
    volume: float
    index: int


@dataclass
class Cluster:
    price_avg: float
    touch_count: int
    last_touch_index: int
    avg_volume: float


def calculate_support_resistance(frame: pd.DataFrame, current_price: float, ticker: str | None = None) -> dict:
    prepared = _prepare_frame(frame).tail(LOOKBACK_DAYS).reset_index(drop=True)
    if prepared.empty or current_price <= 0:
        return {"support": None, "resistance": None}

    cache_key = _cache_key(prepared, current_price, ticker)
    cached, hit = cache.get(cache_key)
    if hit:
        return cached

    average_volume = _average_volume(prepared)
    atr = _calculate_atr(prepared, current_price)
    tolerance = max(atr * 0.5, current_price * 0.001)
    support_pivots, resistance_pivots = _extract_pivots(prepared, average_volume)

    support = _select_level(
        clusters=_cluster_pivots(support_pivots, tolerance),
        current_price=current_price,
        total_length=len(prepared),
        average_volume=average_volume,
        side="support",
    )
    resistance = _select_level(
        clusters=_cluster_pivots(resistance_pivots, tolerance),
        current_price=current_price,
        total_length=len(prepared),
        average_volume=average_volume,
        side="resistance",
    )

    if support is None:
        support = _fallback_level(prepared.tail(FALLBACK_DAYS).reset_index(drop=True), current_price, average_volume, "support")
    if resistance is None:
        resistance = _fallback_level(prepared.tail(FALLBACK_DAYS).reset_index(drop=True), current_price, average_volume, "resistance")

    result = {
        "support": support,
        "resistance": resistance,
        "atr": safe_float(atr, 4),
        "tolerance": safe_float(tolerance, 4),
        "method": "volume_recency_cluster",
        "lookbackDays": min(len(prepared), LOOKBACK_DAYS),
    }
    cache.set(cache_key, result, SUPPORT_RESISTANCE_TTL_SECONDS)
    return result


def _prepare_frame(frame: pd.DataFrame) -> pd.DataFrame:
    required = ["High", "Low", "Close", "Volume"]
    available = [column for column in required if column in frame.columns]
    if len(available) < len(required):
        return pd.DataFrame(columns=required)
    prepared = frame[required].copy()
    for column in required:
        prepared[column] = pd.to_numeric(prepared[column], errors="coerce")
    return prepared.dropna(subset=["High", "Low", "Close"])


def _cache_key(frame: pd.DataFrame, current_price: float, ticker: str | None) -> str:
    last_index = len(frame) - 1
    last_close = safe_float(frame["Close"].iloc[-1], 4)
    return f"support_resistance:{ticker or 'unknown'}:{last_index}:{last_close}:{safe_float(current_price, 4)}"


def _average_volume(frame: pd.DataFrame) -> float:
    volume = frame["Volume"].replace(0, pd.NA).dropna()
    if volume.empty:
        return 1.0
    return float(volume.tail(60).mean() or 1.0)


def _calculate_atr(frame: pd.DataFrame, current_price: float) -> float:
    ranges = (frame["High"] - frame["Low"]).dropna().tail(14)
    atr = float(ranges.mean()) if not ranges.empty else 0.0
    if atr <= 0:
        return current_price * 0.01
    return atr


def _extract_pivots(frame: pd.DataFrame, average_volume: float) -> tuple[list[Pivot], list[Pivot]]:
    supports: list[Pivot] = []
    resistances: list[Pivot] = []
    min_volume = average_volume * VOLUME_FILTER_RATIO

    for index in range(PIVOT_WINDOW, len(frame) - PIVOT_WINDOW):
        row = frame.iloc[index]
        volume = float(row.get("Volume") or 0)
        if volume < min_volume:
            continue

        high = float(row["High"])
        low = float(row["Low"])
        prev_rows = frame.iloc[index - PIVOT_WINDOW:index]
        next_rows = frame.iloc[index + 1:index + PIVOT_WINDOW + 1]

        if high > float(prev_rows["High"].max()) and high > float(next_rows["High"].max()):
            resistances.append(Pivot(price=high, volume=volume, index=index))
        if low < float(prev_rows["Low"].min()) and low < float(next_rows["Low"].min()):
            supports.append(Pivot(price=low, volume=volume, index=index))

    return supports, resistances


def _cluster_pivots(pivots: list[Pivot], tolerance: float) -> list[Cluster]:
    clusters: list[Cluster] = []
    for pivot in sorted(pivots, key=lambda item: item.price):
        cluster = next((item for item in clusters if abs(pivot.price - item.price_avg) <= tolerance), None)
        if cluster is None:
            clusters.append(
                Cluster(
                    price_avg=pivot.price,
                    touch_count=1,
                    last_touch_index=pivot.index,
                    avg_volume=pivot.volume,
                )
            )
            continue

        cluster.price_avg = ((cluster.price_avg * cluster.touch_count) + pivot.price) / (cluster.touch_count + 1)
        cluster.avg_volume = ((cluster.avg_volume * cluster.touch_count) + pivot.volume) / (cluster.touch_count + 1)
        cluster.touch_count += 1
        cluster.last_touch_index = max(cluster.last_touch_index, pivot.index)
    return clusters


def _select_level(
    clusters: list[Cluster],
    current_price: float,
    total_length: int,
    average_volume: float,
    side: str,
) -> dict | None:
    candidates = [
        cluster for cluster in clusters
        if (cluster.price_avg < current_price if side == "support" else cluster.price_avg > current_price)
    ]
    if not candidates:
        return None

    scored = [(cluster, _score_cluster(cluster, current_price, total_length, average_volume)) for cluster in candidates]
    cluster, score = max(scored, key=lambda item: item[1])
    return _level_payload(cluster.price_avg, current_price, cluster.touch_count, score)


def _score_cluster(cluster: Cluster, current_price: float, total_length: int, average_volume: float) -> float:
    touch_score = cluster.touch_count * 3
    recency_score = cluster.last_touch_index / max(total_length - 1, 1)
    volume_score = cluster.avg_volume / max(average_volume, 1)
    distance_penalty = abs(cluster.price_avg - current_price) / current_price
    return touch_score + (recency_score * 2) + (volume_score * 2) - (distance_penalty * 3)


def _fallback_level(frame: pd.DataFrame, current_price: float, average_volume: float, side: str) -> dict | None:
    if frame.empty:
        return None

    price_column = "Low" if side == "support" else "High"
    candidates = []
    for index, row in frame.iterrows():
        price = float(row[price_column])
        if side == "support" and price >= current_price:
            continue
        if side == "resistance" and price <= current_price:
            continue
        volume = float(row.get("Volume") or 0)
        recency_score = index / max(len(frame) - 1, 1)
        volume_score = volume / max(average_volume, 1)
        distance_penalty = abs(price - current_price) / current_price
        score = 3 + (recency_score * 2) + (volume_score * 2) - (distance_penalty * 3)
        candidates.append((price, score))

    if not candidates:
        fallback_price = frame[price_column].min() if side == "support" else frame[price_column].max()
        if pd.isna(fallback_price):
            return None
        return _level_payload(float(fallback_price), current_price, 1, 4)

    price, score = max(candidates, key=lambda item: item[1])
    return _level_payload(price, current_price, 1, score)


def _level_payload(price: float, current_price: float, touch_count: int, score: float) -> dict:
    return {
        "price": safe_float(price, 4),
        "strength": _strength(score),
        "touchCount": safe_int(touch_count),
        "distancePercent": safe_float(((price - current_price) / current_price) * 100, 2),
        "score": safe_float(score, 2),
    }


def _strength(score: float) -> str:
    if score >= 10:
        return "strong"
    if score >= 6:
        return "normal"
    return "weak"
