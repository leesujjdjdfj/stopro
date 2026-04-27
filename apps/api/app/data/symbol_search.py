from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import requests

from app.core.cache import cache
from app.core.utils import normalize_ticker


SYMBOL_DIR = Path(__file__).resolve().parent / "symbols"
SEARCH_CACHE_TTL_SECONDS = 60


def search_symbols(query: str, limit: int = 10) -> list[dict]:
    q = query.strip()
    if len(q) < 1:
        return []
    cache_key = f"symbol-search:{q.lower()}:{limit}"
    cached, hit = cache.get(cache_key)
    if hit:
        return cached

    static_results = _search_static(q, limit)
    if len(static_results) >= limit:
        cache.set(cache_key, static_results[:limit], SEARCH_CACHE_TTL_SECONDS)
        return static_results[:limit]

    combined = static_results + _search_yahoo(q, limit - len(static_results))
    if _looks_like_domestic_code(q):
        combined.append(_shape_direct_domestic(q))
    elif _looks_like_us_ticker(q):
        combined.append(_shape_direct_us(q))
    results = _dedupe_preserve_name(combined)[:limit]
    cache.set(cache_key, results, SEARCH_CACHE_TTL_SECONDS)
    return results


def lookup_symbol(ticker: str) -> dict | None:
    normalized = normalize_ticker(ticker).replace(".KS", "").replace(".KQ", "")
    for row in _load_symbols():
        row_ticker = normalize_ticker(str(row.get("ticker", ""))).replace(".KS", "").replace(".KQ", "")
        if row_ticker == normalized:
            return _shape_static(row)
    return None


def _search_static(query: str, limit: int) -> list[dict]:
    q = query.lower()
    rows = _load_symbols()
    ranked = []
    for index, row in enumerate(rows):
        name = str(row.get("name", ""))
        ticker = normalize_ticker(str(row.get("ticker", "")))
        haystacks = [name.lower(), ticker.lower()]
        if not any(q in value for value in haystacks):
            continue
        rank = _rank_match(q, name, ticker)
        ranked.append((rank, index, _shape_static(row), ticker))
    ranked.sort(key=lambda item: (item[0], item[1], item[3]))
    return [item[2] for item in ranked[:limit]]


def _load_symbols() -> list[dict]:
    rows: list[dict] = []
    for filename in ["krx.json", "us.json"]:
        path = SYMBOL_DIR / filename
        with path.open("r", encoding="utf-8") as file:
            rows.extend(json.load(file))
    return rows


def _rank_match(query: str, name: str, ticker: str) -> int:
    lower_name = name.lower()
    lower_ticker = ticker.lower()
    if query == lower_name or query == lower_ticker:
        return 0
    if lower_name.startswith(query) or lower_ticker.startswith(query):
        return 1
    return 2


def _shape_static(row: dict) -> dict:
    ticker = normalize_ticker(str(row.get("ticker", "")))
    market = str(row.get("market", "")).upper()
    is_krx = market in {"KOSPI", "KOSDAQ", "KONEX"}
    return {
        "name": str(row.get("name", ticker)),
        "ticker": ticker,
        "market": market,
        "exchange": "KRX" if is_krx else market,
        "currency": "KRW" if is_krx else "USD",
    }


def _shape_direct_domestic(query: str) -> dict:
    ticker = normalize_ticker(query)
    return {
        "name": f"KRX {ticker}",
        "ticker": ticker,
        "market": "KRX",
        "exchange": "KRX",
        "currency": "KRW",
    }


def _shape_direct_us(query: str) -> dict:
    ticker = normalize_ticker(query)
    return {
        "name": ticker,
        "ticker": ticker,
        "market": "US",
        "exchange": "US",
        "currency": "USD",
    }


def _looks_like_domestic_code(query: str) -> bool:
    normalized = normalize_ticker(query).replace(".KS", "").replace(".KQ", "")
    return normalized.isdigit() and len(normalized) == 6


def _looks_like_us_ticker(query: str) -> bool:
    normalized = normalize_ticker(query)
    return normalized.isascii() and 1 <= len(normalized) <= 8 and any(char.isalpha() for char in normalized)


def _search_yahoo(query: str, limit: int) -> list[dict]:
    if limit <= 0:
        return []
    try:
        response = requests.get(
            "https://query1.finance.yahoo.com/v1/finance/search",
            params={"q": query, "quotesCount": limit, "newsCount": 0, "enableFuzzyQuery": "true"},
            timeout=3,
        )
        response.raise_for_status()
        data: dict[str, Any] = response.json()
    except Exception:
        return []

    results = []
    for quote in data.get("quotes", []):
        symbol = quote.get("symbol")
        if not symbol:
            continue
        ticker = normalize_ticker(str(symbol))
        market = str(quote.get("exchange") or quote.get("exchDisp") or "US").upper()
        currency = "KRW" if ticker.endswith((".KS", ".KQ")) else "USD"
        clean_ticker = ticker.replace(".KS", "").replace(".KQ", "") if currency == "KRW" else ticker
        results.append(
            {
                "name": quote.get("shortname") or quote.get("longname") or clean_ticker,
                "ticker": clean_ticker,
                "market": "KOSPI" if ticker.endswith(".KS") else "KOSDAQ" if ticker.endswith(".KQ") else market,
                "exchange": "KRX" if currency == "KRW" else market,
                "currency": currency,
            }
        )
    return results[:limit]


def _dedupe_preserve_name(rows: list[dict]) -> list[dict]:
    seen: set[tuple[str, str]] = set()
    results = []
    for row in rows:
        key = (row["name"].lower(), row["ticker"])
        if key in seen:
            continue
        seen.add(key)
        results.append(row)
    return results
