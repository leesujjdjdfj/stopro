from __future__ import annotations

from datetime import datetime, timedelta, timezone

import requests

from app.news.news_provider import NewsProviderError, dedupe_articles, normalize_article


class GNewsProvider:
    name = "GNEWS"

    def __init__(self, api_key: str | None) -> None:
        self.api_key = api_key

    def fetch_news(self, query: str, max_results: int = 10) -> list[dict]:
        if not self.api_key:
            raise NewsProviderError("GNews API 키가 설정되지 않았습니다.")

        since = datetime.now(timezone.utc) - timedelta(days=7)
        response = requests.get(
            "https://gnews.io/api/v4/search",
            params={
                "q": query,
                "max": min(max_results, 10),
                "from": since.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "sortby": "publishedAt",
                "apikey": self.api_key,
            },
            timeout=8,
        )
        if response.status_code >= 400:
            raise NewsProviderError(f"GNews 요청 실패: {response.status_code}")

        data = response.json()
        articles: list[dict] = []
        for item in data.get("articles", []):
            source = item.get("source") or {}
            shaped = normalize_article(
                title=item.get("title"),
                description=item.get("description"),
                url=item.get("url"),
                source=source.get("name") if isinstance(source, dict) else None,
                published_at=item.get("publishedAt"),
            )
            if shaped:
                articles.append(shaped)
        return dedupe_articles(articles, max_results)
