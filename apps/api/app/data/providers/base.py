from __future__ import annotations

from typing import Protocol

import pandas as pd


class MarketDataProvider(Protocol):
    def get_quote(self, ticker: str) -> dict:
        ...

    def get_history(self, ticker: str, period: str = "1y") -> tuple[pd.DataFrame, bool, str]:
        ...

    def get_fundamentals(self, ticker: str) -> dict:
        ...

    def get_exchange_rate(self) -> tuple[float, bool]:
        ...
