from __future__ import annotations

from app.data.providers.kis_provider import KisProvider
from app.data.providers.yfinance_provider import YFinanceProvider


class MarketDataProvider:
    def __init__(self, yfinance_provider: YFinanceProvider | None = None, kis_provider: KisProvider | None = None) -> None:
        self.yfinance_provider = yfinance_provider or YFinanceProvider()
        self.kis_provider = kis_provider or KisProvider()

    def get_quote(self, ticker: str) -> dict:
        if self.kis_provider.is_enabled() and self.kis_provider.supports(ticker):
            try:
                return self.kis_provider.get_quote(ticker)
            except Exception:
                pass
        return self.yfinance_provider.get_quote(ticker)

    def get_history(self, ticker: str, period: str = "1y"):
        if self.kis_provider.is_enabled() and self.kis_provider.supports(ticker):
            try:
                return self.kis_provider.get_history(ticker, period)
            except Exception:
                pass
        return self.yfinance_provider.get_history(ticker, period)

