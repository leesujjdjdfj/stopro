from __future__ import annotations

from datetime import datetime, timezone

from app.core.cache import cache
from app.core.config import get_settings
from app.core.utils import normalize_ticker
from app.data.providers.yfinance_provider import YFinanceProvider
from app.data.symbol_search import lookup_symbol
from app.news.gnews_provider import GNewsProvider
from app.news.news_provider import NewsProvider
from app.news.newsapi_provider import NewsApiProvider


NEWS_CACHE_TTL_SECONDS = 600


class NewsService:
    def __init__(self, quote_provider: YFinanceProvider | None = None) -> None:
        self.settings = get_settings()
        self.quote_provider = quote_provider or YFinanceProvider()

    def get_news(self, ticker: str, company_name: str | None = None) -> dict:
        display_ticker = self._display_ticker(ticker)
        company = (company_name or self._resolve_company_name(display_ticker)).strip() or display_ticker
        query = self._build_query(display_ticker, company)
        provider_key = self.settings.news_provider.lower()
        today = datetime.now(timezone.utc).date().isoformat()
        cache_key = f"news:{provider_key}:{display_ticker}:{today}:{company.lower()}"
        cached, hit = cache.get(cache_key)
        if hit:
            return {**cached, "cacheHit": True}

        errors: list[str] = []
        for provider in self._ordered_providers():
            try:
                articles = provider.fetch_news(query, 10)
            except Exception as exc:
                errors.append(str(exc))
                continue
            if articles:
                result = {
                    "ticker": display_ticker,
                    "companyName": company,
                    "query": query,
                    "source": provider.name,
                    "articles": articles,
                    "cacheHit": False,
                    "message": None if len(articles) >= 3 else "분석에 사용할 뉴스 수가 부족합니다.",
                }
                cache.set(cache_key, result, NEWS_CACHE_TTL_SECONDS)
                return result

        message = "최근 뉴스를 불러오지 못했습니다."
        if errors:
            message = f"{message} API 키 또는 외부 뉴스 API 상태를 확인해 주세요."
        result = {
            "ticker": display_ticker,
            "companyName": company,
            "query": query,
            "source": "FALLBACK",
            "articles": [],
            "cacheHit": False,
            "message": message,
        }
        cache.set(cache_key, result, NEWS_CACHE_TTL_SECONDS)
        return result

    def _ordered_providers(self) -> list[NewsProvider]:
        providers = {
            "gnews": GNewsProvider(self.settings.gnews_api_key),
            "newsapi": NewsApiProvider(self.settings.news_api_key),
        }
        preferred = self.settings.news_provider.lower()
        ordered: list[NewsProvider] = []
        if preferred in providers:
            ordered.append(providers[preferred])
        ordered.extend(provider for key, provider in providers.items() if key != preferred)
        return ordered

    def _resolve_company_name(self, ticker: str) -> str:
        symbol = lookup_symbol(ticker)
        if symbol and symbol.get("name"):
            return str(symbol["name"])
        try:
            quote = self.quote_provider.get_quote(ticker)
            return str(quote.get("name") or ticker)
        except Exception:
            return ticker

    def _build_query(self, ticker: str, company_name: str) -> str:
        clean_ticker = self._display_ticker(ticker)
        if company_name and company_name.upper() != clean_ticker.upper():
            return f"{company_name} OR {clean_ticker}"
        return clean_ticker

    def _display_ticker(self, ticker: str) -> str:
        return normalize_ticker(ticker).replace(".KS", "").replace(".KQ", "")
