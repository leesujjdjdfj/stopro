from __future__ import annotations

from typing import Protocol


class NewsProviderError(Exception):
    pass


class NewsProvider(Protocol):
    name: str

    def fetch_news(self, query: str, max_results: int = 10) -> list[dict]:
        ...


def normalize_article(
    *,
    title: str | None,
    description: str | None,
    url: str | None,
    source: str | None,
    published_at: str | None,
) -> dict | None:
    clean_title = (title or "").strip()
    clean_url = (url or "").strip()
    if not clean_title or not clean_url:
        return None
    return {
        "title": clean_title,
        "description": (description or clean_title).strip(),
        "url": clean_url,
        "source": (source or "Unknown").strip(),
        "publishedAt": published_at,
    }


def dedupe_articles(articles: list[dict], limit: int = 10) -> list[dict]:
    seen: set[str] = set()
    results: list[dict] = []
    for article in articles:
        url = article.get("url")
        if not url or url in seen:
            continue
        seen.add(url)
        results.append(article)
        if len(results) >= limit:
            break
    return results
