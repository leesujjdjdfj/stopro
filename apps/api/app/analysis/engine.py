from __future__ import annotations

from app.analysis.backtest import run_backtest
from app.analysis.fundamentals import interpret_fundamentals
from app.analysis.indicators import add_indicators, latest_indicators
from app.analysis.quality import check_data_quality
from app.analysis.risk import calculate_risk
from app.analysis.scenario import build_scenarios
from app.analysis.strategy import (
    calculate_position_sizing,
    calculate_profit_loss,
    calculate_reward_risk,
    build_strategy,
)
from app.analysis.summary import make_decision, make_rule_based_summary
from app.core.utils import DISCLAIMER, clean_json, normalize_ticker, safe_float, safe_int
from app.data.providers.kis_provider import KisProvider
from app.data.providers.yfinance_provider import YFinanceProvider


class AnalysisEngine:
    def __init__(self, provider: YFinanceProvider | None = None, kis_provider: KisProvider | None = None) -> None:
        self.provider = provider or YFinanceProvider()
        self.kis_provider = kis_provider or KisProvider()

    def analyze(self, ticker: str, capital_krw: float, risk_profile: str = "balanced") -> dict:
        normalized = normalize_ticker(ticker)
        history, history_cache_hit, source = self._get_best_history(normalized, "2y")
        history_with_indicators = add_indicators(history)
        indicators = latest_indicators(history_with_indicators)
        quote = self._get_best_quote(normalized)

        current_price = quote.get("price") or safe_float(history_with_indicators["Close"].iloc[-1], 4) or 0
        previous_close = quote.get("previousClose") or safe_float(history_with_indicators["Close"].iloc[-2], 4)
        currency = quote.get("currency") or "USD"
        if currency.upper() == "KRW":
            fundamentals_raw = {}
            usd_krw = float(self.provider.settings.usd_krw)
            exchange_cache_hit = False
            price_exchange_rate = 1.0
        else:
            fundamentals_raw = self.provider.get_fundamentals(normalized)
            usd_krw, exchange_cache_hit = self.provider.get_exchange_rate()
            price_exchange_rate = usd_krw

        quote_source = quote.get("source")
        quality = check_data_quality(
            history_with_indicators,
            indicators,
            source,
            history_cache_hit or quote.get("cacheHit", False),
            bool(quote.get("isRealtime")),
            quote_source,
        )
        strategy = build_strategy(current_price, indicators)
        reward_risk = calculate_reward_risk(strategy)
        risk = calculate_risk(current_price, previous_close, indicators, reward_risk)
        decision = make_decision(current_price, indicators, risk, reward_risk, quality)
        summary = make_rule_based_summary(decision, current_price, indicators, reward_risk, quality)
        position_sizing = calculate_position_sizing(capital_krw, risk_profile, strategy, price_exchange_rate)
        profit_loss = calculate_profit_loss(strategy, position_sizing.get("quantity") or 0, price_exchange_rate)
        scenarios = build_scenarios(current_price, previous_close, indicators, strategy, risk, reward_risk)
        fundamentals = interpret_fundamentals(fundamentals_raw)
        backtest = run_backtest(history_with_indicators)
        chart = self._build_chart(history_with_indicators)

        display_ticker = quote.get("displayTicker") or quote.get("ticker") or normalized
        response_ticker = quote.get("ticker") or display_ticker
        market = quote.get("market") or quote.get("exchange")
        exchange = quote.get("exchange") or market

        response = {
            "ticker": response_ticker,
            "displayTicker": display_ticker,
            "name": quote.get("name") or display_ticker,
            "market": market,
            "exchange": exchange,
            "currency": currency,
            "exchangeRate": safe_float(price_exchange_rate, 4),
            "usdKrw": safe_float(usd_krw, 4),
            "currentPrice": current_price,
            "previousClose": previous_close,
            "dailyChange": quote.get("dailyChange"),
            "dailyChangePercent": quote.get("dailyChangePercent"),
            "dataTimestamp": quote.get("dataTimestamp"),
            "isDelayed": bool(quote.get("isDelayed", True)),
            "cacheHit": bool(history_cache_hit or quote.get("cacheHit") or exchange_cache_hit),
            "decision": decision,
            "summary": summary,
            "quote": {
                "price": current_price,
                "volume": quote.get("volume"),
                "averageVolume": quote.get("averageVolume"),
                "fiftyTwoWeekHigh": quote.get("fiftyTwoWeekHigh"),
                "fiftyTwoWeekLow": quote.get("fiftyTwoWeekLow"),
            },
            "indicators": indicators,
            "strategy": strategy,
            "positionSizing": position_sizing,
            "profitLoss": profit_loss,
            "rewardRisk": reward_risk,
            "risk": risk,
            "scenarios": scenarios,
            "fundamentals": fundamentals,
            "backtest": backtest,
            "dataQuality": quality,
            "chart": chart,
            "disclaimer": DISCLAIMER,
        }
        return clean_json(response)

    def _get_best_quote(self, ticker: str) -> dict:
        if self.kis_provider.is_enabled() and self.kis_provider.supports(ticker):
            try:
                return self.kis_provider.get_quote(ticker)
            except Exception:
                pass
        return self.provider.get_quote(ticker)

    def _get_best_history(self, ticker: str, period: str):
        if self.kis_provider.is_enabled() and self.kis_provider.supports(ticker):
            try:
                return self.kis_provider.get_history(ticker, period)
            except Exception:
                pass
        return self.provider.get_history(ticker, period)

    def _build_chart(self, frame) -> list[dict]:
        rows = []
        for index, row in frame.tail(504).iterrows():
            rows.append(
                {
                    "date": index.strftime("%Y-%m-%d") if hasattr(index, "strftime") else str(index),
                    "open": safe_float(row.get("Open"), 4),
                    "high": safe_float(row.get("High"), 4),
                    "low": safe_float(row.get("Low"), 4),
                    "close": safe_float(row.get("Close"), 4),
                    "volume": safe_int(row.get("Volume")),
                    "ma20": safe_float(row.get("MA20"), 4),
                    "ma60": safe_float(row.get("MA60"), 4),
                    "ma200": safe_float(row.get("MA200"), 4),
                }
            )
        return rows
