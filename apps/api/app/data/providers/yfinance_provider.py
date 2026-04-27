from __future__ import annotations

import os
from datetime import datetime, timezone
from typing import Any

import numpy as np
import pandas as pd
import yfinance as yf

from app.core.cache import cache
from app.core.config import get_settings
from app.core.errors import StockDataError
from app.core.utils import normalize_ticker, safe_float, safe_int
from app.data.symbol_search import lookup_symbol


PERIOD_MAP = {
    "1m": "1mo",
    "3m": "3mo",
    "6m": "6mo",
    "1y": "1y",
    "2y": "2y",
    "5y": "5y",
}


class YFinanceProvider:
    source = "yfinance"

    def __init__(self) -> None:
        self.settings = get_settings()
        self._disable_bad_proxy_env()

    def get_history(self, ticker: str, period: str = "1y") -> tuple[pd.DataFrame, bool, str]:
        ticker = normalize_ticker(ticker)
        yf_period = PERIOD_MAP.get(period.lower(), period)
        key = f"history:{ticker}:{yf_period}"
        cached, hit = cache.get(key)
        if hit:
            return cached.copy(), True, self.source

        last_error: Exception | None = None
        try:
            for yf_ticker in self._yf_ticker_candidates(ticker):
                try:
                    frame = yf.Ticker(yf_ticker).history(period=yf_period, interval="1d", auto_adjust=False, actions=False)
                except Exception as exc:
                    last_error = exc
                    continue
                if frame is None or frame.empty:
                    continue
                frame = self._normalize_history(frame)
                if frame.empty:
                    continue
                frame.attrs["resolvedTicker"] = yf_ticker
                cache.set(key, frame, self.settings.cache_ttl_seconds)
                return frame.copy(), False, self.source
        except Exception as exc:
            fallback = self._fallback_history(ticker, yf_period)
            fallback.attrs["resolvedTicker"] = ticker
            cache.set(key, fallback, self.settings.cache_ttl_seconds)
            return fallback.copy(), False, "mock-fallback"

        if last_error is not None:
            fallback = self._fallback_history(ticker, yf_period)
            fallback.attrs["resolvedTicker"] = ticker
            cache.set(key, fallback, self.settings.cache_ttl_seconds)
            return fallback.copy(), False, "mock-fallback"

        if self._is_domestic_ticker(ticker):
            raise StockDataError("국내 종목 데이터를 찾을 수 없습니다. 6자리 종목코드나 시장 구분을 확인해 주세요.", 404)
        else:
            raise StockDataError("종목 데이터를 찾을 수 없습니다. 티커를 다시 확인해 주세요.", 404)

    def get_quote(self, ticker: str) -> dict:
        ticker = normalize_ticker(ticker)
        key = f"quote:{ticker}"
        cached, hit = cache.get(key)
        if hit:
            return {**cached, "cacheHit": True}

        history, history_hit, source = self.get_history(ticker, "1y")
        latest = history.iloc[-1]
        previous = history.iloc[-2] if len(history) > 1 else latest
        info: dict[str, Any] = {}
        fast_info: dict[str, Any] = {}

        if source == self.source:
            try:
                ticker_obj = yf.Ticker(history.attrs.get("resolvedTicker") or self._yf_ticker_candidates(ticker)[0])
                info = ticker_obj.info or {}
                fast = ticker_obj.fast_info
                fast_info = dict(fast) if fast else {}
            except Exception:
                info = {}
                fast_info = {}

        symbol = lookup_symbol(ticker) or {}
        market = symbol.get("market") or info.get("exchange") or fast_info.get("exchange") or ("KRX" if self._is_domestic_ticker(ticker) else "US")
        exchange = "KRX" if self._is_domestic_ticker(ticker) else market
        display_ticker = ticker.replace(".KS", "").replace(".KQ", "") if self._is_domestic_ticker(ticker) else ticker
        close = safe_float(latest.get("Close"), 4)
        previous_close = safe_float(previous.get("Close"), 4)
        daily_change = safe_float((close or 0) - (previous_close or close or 0), 4)
        daily_change_percent = safe_float((daily_change / previous_close) * 100 if previous_close else 0, 2)
        volume = safe_int(latest.get("Volume"))
        average_volume = safe_int(info.get("averageVolume") or info.get("averageDailyVolume10Day") or history["Volume"].tail(20).mean())
        quote = {
            "ticker": display_ticker,
            "displayTicker": display_ticker,
            "name": info.get("longName") or info.get("shortName") or symbol.get("name") or display_ticker,
            "market": market,
            "currency": info.get("currency") or fast_info.get("currency") or symbol.get("currency") or ("KRW" if self._is_domestic_ticker(ticker) else "USD"),
            "exchange": exchange,
            "price": close,
            "previousClose": previous_close,
            "dailyChange": daily_change,
            "dailyChangePercent": daily_change_percent,
            "volume": volume,
            "averageVolume": average_volume,
            "fiftyTwoWeekHigh": safe_float(info.get("fiftyTwoWeekHigh") or history["High"].tail(252).max(), 4),
            "fiftyTwoWeekLow": safe_float(info.get("fiftyTwoWeekLow") or history["Low"].tail(252).min(), 4),
            "dataTimestamp": latest.name.isoformat() if hasattr(latest.name, "isoformat") else datetime.now(timezone.utc).isoformat(),
            "isDelayed": True,
            "cacheHit": history_hit,
            "source": source,
        }
        cache.set(key, quote, self.settings.cache_ttl_seconds)
        return {**quote, "cacheHit": False}

    def get_fundamentals(self, ticker: str) -> dict:
        ticker = normalize_ticker(ticker)
        key = f"fundamentals:{ticker}"
        cached, hit = cache.get(key)
        if hit:
            return {**cached, "cacheHit": True}

        info: dict[str, Any] = {}
        try:
            info = yf.Ticker(self._yf_ticker_candidates(ticker)[0]).info or {}
        except Exception:
            info = {}

        result = {
            "marketCap": safe_int(info.get("marketCap")),
            "trailingPE": safe_float(info.get("trailingPE"), 2),
            "forwardPE": safe_float(info.get("forwardPE"), 2),
            "eps": safe_float(info.get("trailingEps"), 2),
            "profitMargin": safe_float(info.get("profitMargins"), 4),
            "revenueGrowth": safe_float(info.get("revenueGrowth"), 4),
            "debtToEquity": safe_float(info.get("debtToEquity"), 2),
            "cacheHit": False,
        }
        cache.set(key, result, self.settings.cache_ttl_seconds)
        return result

    def get_exchange_rate(self) -> tuple[float, bool]:
        key = "exchange:USD_KRW"
        cached, hit = cache.get(key)
        if hit:
            return float(cached), True
        try:
            frame = yf.Ticker("KRW=X").history(period="5d", interval="1d", auto_adjust=False, actions=False)
            if frame is not None and not frame.empty:
                rate = safe_float(frame["Close"].dropna().iloc[-1], 4)
                if rate:
                    cache.set(key, rate, self.settings.exchange_rate_cache_ttl_seconds)
                    return rate, False
        except Exception:
            pass
        rate = float(self.settings.usd_krw)
        cache.set(key, rate, self.settings.exchange_rate_cache_ttl_seconds)
        return rate, False

    def _normalize_history(self, frame: pd.DataFrame) -> pd.DataFrame:
        if isinstance(frame.columns, pd.MultiIndex):
            frame.columns = frame.columns.get_level_values(0)
        required = ["Open", "High", "Low", "Close", "Volume"]
        for column in required:
            if column not in frame.columns:
                frame[column] = np.nan
        frame = frame[required].copy()
        frame = frame.dropna(subset=["Close"])
        frame["Volume"] = frame["Volume"].fillna(0)
        return frame

    def _is_domestic_ticker(self, ticker: str) -> bool:
        return (ticker.isdigit() and len(ticker) == 6) or ticker.endswith((".KS", ".KQ"))

    def _yf_ticker_candidates(self, ticker: str) -> list[str]:
        if ticker.endswith((".KS", ".KQ")):
            return [ticker]
        if ticker.isdigit() and len(ticker) == 6:
            return [f"{ticker}.KS", f"{ticker}.KQ"]
        return [ticker]

    def _disable_bad_proxy_env(self) -> None:
        for key in ["HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY", "http_proxy", "https_proxy", "all_proxy"]:
            value = os.environ.get(key)
            if value and "127.0.0.1:9" in value:
                os.environ.pop(key, None)

    def _fallback_history(self, ticker: str, period: str) -> pd.DataFrame:
        days = {"1mo": 30, "3mo": 90, "6mo": 180, "1y": 365, "2y": 730, "5y": 1260}.get(period, 365)
        business_days = max(45, int(days * 5 / 7))
        dates = pd.bdate_range(end=pd.Timestamp.utcnow().normalize(), periods=business_days)
        seed = abs(hash(ticker)) % 10000
        rng = np.random.default_rng(seed)
        base = 80 + (seed % 120)
        drift = rng.normal(0.0008, 0.018, business_days).cumsum()
        close = base * (1 + drift)
        close = np.maximum(close, 1)
        high = close * (1 + rng.uniform(0.002, 0.025, business_days))
        low = close * (1 - rng.uniform(0.002, 0.025, business_days))
        open_ = close * (1 + rng.normal(0, 0.008, business_days))
        volume = rng.integers(1_000_000, 25_000_000, business_days)
        return pd.DataFrame({"Open": open_, "High": high, "Low": low, "Close": close, "Volume": volume}, index=dates)
