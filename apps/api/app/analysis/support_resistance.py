from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from app.core.cache import cache
from app.core.utils import safe_float, safe_int


SUPPORT_RESISTANCE_TTL_SECONDS = 600
LOOKBACK_DAYS = 120
FALLBACK_DAYS = 60
REACTION_DAYS = 45
PIVOT_WINDOW = 2
VOLUME_FILTER_RATIO = 0.8
REACTION_VOLUME_FILTER_RATIO = 0.45
PRACTICAL_DISTANCE_RATIO = 0.15
FAR_DISTANCE_RATIO = 0.22
EXTREME_DISTANCE_RATIO = 0.30


@dataclass
class Pivot:
    price: float
    volume: float
    index: int
    weight: float = 1.0


@dataclass
class Cluster:
    price_avg: float
    touch_count: int
    weighted_touch_count: float
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
    reaction_supports, reaction_resistances = _extract_reaction_points(prepared, average_volume)

    support = _select_level(
        clusters=_cluster_pivots([*support_pivots, *reaction_supports], tolerance),
        current_price=current_price,
        total_length=len(prepared),
        average_volume=average_volume,
        side="support",
    )
    resistance = _select_level(
        clusters=_cluster_pivots([*resistance_pivots, *reaction_resistances], tolerance),
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
        "method": "volume_recency_proximity_cluster",
        "lookbackDays": min(len(prepared), LOOKBACK_DAYS),
    }
    cache.set(cache_key, result, SUPPORT_RESISTANCE_TTL_SECONDS)
    return result


def _prepare_frame(frame: pd.DataFrame) -> pd.DataFrame:
    required = ["High", "Low", "Close", "Volume"]
    optional = ["Open"]
    available = [column for column in required if column in frame.columns]
    if len(available) < len(required):
        return pd.DataFrame(columns=[*required, *optional])
    columns = [*required, *[column for column in optional if column in frame.columns]]
    prepared = frame[columns].copy()
    for column in columns:
        prepared[column] = pd.to_numeric(prepared[column], errors="coerce")
    if "Open" not in prepared.columns:
        prepared["Open"] = prepared["Close"]
    return prepared.dropna(subset=["High", "Low", "Close"])


def _cache_key(frame: pd.DataFrame, current_price: float, ticker: str | None) -> str:
    last_index = len(frame) - 1
    last_close = safe_float(frame["Close"].iloc[-1], 4)
    return f"support_resistance:v2:{ticker or 'unknown'}:{last_index}:{last_close}:{safe_float(current_price, 4)}"


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


def _extract_reaction_points(frame: pd.DataFrame, average_volume: float) -> tuple[list[Pivot], list[Pivot]]:
    supports: list[Pivot] = []
    resistances: list[Pivot] = []
    recent = frame.tail(REACTION_DAYS)
    min_volume = average_volume * REACTION_VOLUME_FILTER_RATIO

    for index, row in recent.iterrows():
        volume = float(row.get("Volume") or 0)
        if volume < min_volume:
            continue

        high = float(row["High"])
        low = float(row["Low"])
        close = float(row["Close"])
        open_price = float(row.get("Open") or close)
        candle_range = max(high - low, 1.0)
        lower_wick_ratio = (min(open_price, close) - low) / candle_range
        upper_wick_ratio = (high - max(open_price, close)) / candle_range

        recent_boost = 1.0 if index >= len(frame) - 20 else 0.85
        support_weight = (0.55 + min(max(lower_wick_ratio, 0), 0.45)) * recent_boost
        resistance_weight = (0.55 + min(max(upper_wick_ratio, 0), 0.45)) * recent_boost

        supports.append(Pivot(price=low, volume=volume, index=int(index), weight=support_weight))
        resistances.append(Pivot(price=high, volume=volume, index=int(index), weight=resistance_weight))

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
                    weighted_touch_count=pivot.weight,
                    last_touch_index=pivot.index,
                    avg_volume=pivot.volume,
                )
            )
            continue

        next_weighted_count = cluster.weighted_touch_count + pivot.weight
        cluster.price_avg = ((cluster.price_avg * cluster.weighted_touch_count) + (pivot.price * pivot.weight)) / max(next_weighted_count, 1)
        cluster.avg_volume = ((cluster.avg_volume * cluster.touch_count) + pivot.volume) / (cluster.touch_count + 1)
        cluster.touch_count += 1
        cluster.weighted_touch_count = next_weighted_count
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

    practical_candidates = [
        cluster for cluster in candidates
        if abs(cluster.price_avg - current_price) / current_price <= PRACTICAL_DISTANCE_RATIO
    ]
    if practical_candidates:
        candidates = practical_candidates

    scored = [(cluster, _score_cluster(cluster, current_price, total_length, average_volume)) for cluster in candidates]
    cluster, score = max(scored, key=lambda item: item[1])
    return _level_payload(cluster.price_avg, current_price, cluster.touch_count, score)


def _score_cluster(cluster: Cluster, current_price: float, total_length: int, average_volume: float) -> float:
    distance_ratio = abs(cluster.price_avg - current_price) / current_price
    touch_score = cluster.weighted_touch_count * 3
    recency_score = cluster.last_touch_index / max(total_length - 1, 1)
    volume_score = cluster.avg_volume / max(average_volume, 1)
    distance_penalty = distance_ratio * 25
    far_penalty = _far_distance_penalty(distance_ratio)
    proximity_bonus = _proximity_bonus(distance_ratio)
    return touch_score + (recency_score * 3) + (volume_score * 1.5) + proximity_bonus - distance_penalty - far_penalty


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
        distance_ratio = abs(price - current_price) / current_price
        recency_score = index / max(len(frame) - 1, 1)
        volume_score = volume / max(average_volume, 1)
        distance_penalty = distance_ratio * 25
        score = 3 + (recency_score * 3) + (volume_score * 1.5) + _proximity_bonus(distance_ratio) - distance_penalty - _far_distance_penalty(distance_ratio)
        candidates.append((price, score, distance_ratio))

    if not candidates:
        fallback_price = frame[price_column].min() if side == "support" else frame[price_column].max()
        if pd.isna(fallback_price):
            return None
        return _level_payload(float(fallback_price), current_price, 1, 4)

    practical_candidates = [item for item in candidates if item[2] <= PRACTICAL_DISTANCE_RATIO]
    price, score, _ = max(practical_candidates or candidates, key=lambda item: item[1])
    return _level_payload(price, current_price, 1, score)


def _proximity_bonus(distance_ratio: float) -> float:
    if distance_ratio <= 0.03:
        return 5.0
    if distance_ratio <= 0.08:
        return 4.0
    if distance_ratio <= PRACTICAL_DISTANCE_RATIO:
        return 2.0
    return 0.0


def _far_distance_penalty(distance_ratio: float) -> float:
    if distance_ratio >= EXTREME_DISTANCE_RATIO:
        return 12.0
    if distance_ratio >= FAR_DISTANCE_RATIO:
        return 6.0
    return 0.0


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
