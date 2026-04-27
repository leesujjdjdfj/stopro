from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class NewsArticle(BaseModel):
    title: str
    description: Optional[str] = None
    url: str
    source: Optional[str] = None
    publishedAt: Optional[str] = None


class NewsResponse(BaseModel):
    ticker: str
    companyName: str
    query: str
    source: str
    articles: list[NewsArticle]
    cacheHit: bool = False
    message: Optional[str] = None


class NewsAnalysisRequest(BaseModel):
    ticker: str = Field(min_length=1)
    companyName: Optional[str] = None
    currentPrice: Optional[float] = None
    dailyChangePercent: Optional[float] = None


class NewsAnalysisResponse(BaseModel):
    ticker: str
    companyName: str
    newsSource: str
    aiProvider: str
    sentiment: str
    sentimentScore: int
    oneLine: str
    summary: str
    keyIssues: list[str]
    positiveFactors: list[str]
    negativeFactors: list[str]
    riskFactors: list[str]
    watchPoints: list[str]
    newsItems: list[NewsArticle]
    confidence: str
    cacheHit: bool = False
    disclaimer: str
