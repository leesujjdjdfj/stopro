from __future__ import annotations

from fastapi import APIRouter

from app.ai.market_news_analyzer import MarketNewsAnalyzer
from app.news.news_service import NewsService
from app.schemas.news_analysis import NewsAnalysisRequest

router = APIRouter(prefix="/api", tags=["news-analysis"])
news_service = NewsService()
market_news_analyzer = MarketNewsAnalyzer(news_service)


@router.get("/news/{ticker}")
def get_news(ticker: str) -> dict:
    return news_service.get_news(ticker)


@router.post("/news-analysis")
def analyze_news(payload: NewsAnalysisRequest) -> dict:
    return market_news_analyzer.analyze(
        ticker=payload.ticker,
        company_name=payload.companyName,
        current_price=payload.currentPrice,
        daily_change_percent=payload.dailyChangePercent,
    )
