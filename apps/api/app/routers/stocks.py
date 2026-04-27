from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from app.core.errors import StockDataError
from app.core.utils import clean_json, normalize_ticker, safe_float, safe_int
from app.data.market_data import MarketDataProvider
from app.schemas.stock import HistoryResponse

router = APIRouter(prefix="/api/stocks", tags=["stocks"])
provider = MarketDataProvider()


@router.get("/{ticker}/quote")
def quote(ticker: str) -> dict:
    try:
        return clean_json(provider.get_quote(ticker))
    except StockDataError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc


@router.get("/{ticker}/history", response_model=HistoryResponse)
def history(ticker: str, period: str = Query("1y")) -> dict:
    try:
        frame, cache_hit, source = provider.get_history(ticker, period)
    except StockDataError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc
    rows = []
    for index, row in frame.iterrows():
        rows.append(
            {
                "date": index.strftime("%Y-%m-%d") if hasattr(index, "strftime") else str(index),
                "open": safe_float(row.get("Open"), 4),
                "high": safe_float(row.get("High"), 4),
                "low": safe_float(row.get("Low"), 4),
                "close": safe_float(row.get("Close"), 4),
                "volume": safe_int(row.get("Volume")),
            }
        )
    return {"ticker": normalize_ticker(ticker), "period": period, "cacheHit": cache_hit, "source": source, "rows": rows}
