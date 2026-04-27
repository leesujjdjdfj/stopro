from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.errors import StockDataError
from app.db.database import init_db
from app.routers import alerts, analysis, dashboard, health, memos, news_analysis, positions, search, settings, stocks, watchlist


app = FastAPI(
    title="StoPro API",
    description="개인 투자 분석을 위한 yfinance 기반 FastAPI 서버",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup() -> None:
    init_db()


@app.exception_handler(StockDataError)
async def stock_data_exception_handler(_: Request, exc: StockDataError) -> JSONResponse:
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.message})


app.include_router(health.router)
app.include_router(stocks.router)
app.include_router(analysis.router)
app.include_router(dashboard.router)
app.include_router(watchlist.router)
app.include_router(positions.router)
app.include_router(alerts.router)
app.include_router(memos.router)
app.include_router(news_analysis.router)
app.include_router(search.router)
app.include_router(settings.router)
