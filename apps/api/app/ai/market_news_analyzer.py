from __future__ import annotations

from datetime import datetime, timezone

from app.ai.groq_provider import GroqProvider
from app.ai.openrouter_provider import OpenRouterProvider
from app.core.cache import cache
from app.core.config import get_settings
from app.core.utils import clean_json, normalize_ticker, safe_float
from app.news.news_service import NewsService


AI_NEWS_CACHE_TTL_SECONDS = 1800
NEWS_AI_DISCLAIMER = "뉴스 기반 AI 분석은 참고용이며, 투자 판단과 책임은 사용자 본인에게 있습니다."


class MarketNewsAnalyzer:
    def __init__(self, news_service: NewsService | None = None) -> None:
        self.settings = get_settings()
        self.news_service = news_service or NewsService()

    def analyze(
        self,
        ticker: str,
        company_name: str | None = None,
        current_price: float | None = None,
        daily_change_percent: float | None = None,
    ) -> dict:
        display_ticker = normalize_ticker(ticker).replace(".KS", "").replace(".KQ", "")
        today = datetime.now(timezone.utc).date().isoformat()
        provider_key = self.settings.ai_provider.lower()
        cache_key = f"news-ai:{provider_key}:{self.settings.ai_model}:{display_ticker}:{today}"
        cached, hit = cache.get(cache_key)
        if hit:
            return {**cached, "cacheHit": True}

        news = self.news_service.get_news(display_ticker, company_name)
        articles = news.get("articles", [])
        company = news.get("companyName") or company_name or display_ticker

        if not articles:
            result = self._fallback_result(display_ticker, company, news, provider="RULE_BASED", reason=news.get("message"))
            cache.set(cache_key, result, AI_NEWS_CACHE_TTL_SECONDS)
            return result

        system_prompt = self._system_prompt()
        user_prompt = self._user_prompt(company, display_ticker, current_price, daily_change_percent, articles)
        for provider in self._ordered_providers():
            try:
                ai_result = provider.analyze(system_prompt, user_prompt)
                result = self._shape_ai_result(display_ticker, company, news, ai_result, provider.name)
                cache.set(cache_key, result, AI_NEWS_CACHE_TTL_SECONDS)
                return result
            except Exception:
                continue

        result = self._fallback_result(display_ticker, company, news, provider="RULE_BASED", reason="AI API 호출에 실패해 규칙 기반으로 요약했습니다.")
        cache.set(cache_key, result, AI_NEWS_CACHE_TTL_SECONDS)
        return result

    def _ordered_providers(self) -> list:
        providers = {
            "groq": GroqProvider(self.settings.groq_api_key, self.settings.ai_model),
            "openrouter": OpenRouterProvider(self.settings.openrouter_api_key, self.settings.ai_model),
        }
        preferred = self.settings.ai_provider.lower()
        ordered = []
        if preferred in providers:
            ordered.append(providers[preferred])
        ordered.extend(provider for key, provider in providers.items() if key != preferred)
        return ordered

    def _system_prompt(self) -> str:
        return (
            "너는 개인 투자자를 위한 보수적인 시장 뉴스 분석 보조 도구다. "
            "제공된 뉴스 제목과 요약만 기반으로 분석한다. 기사에 없는 내용을 추측하지 않는다. "
            "매수/매도 확정 권유를 하지 않는다. 투자 판단에 도움이 되도록 핵심 이슈, 긍정 요인, "
            "부정 요인, 리스크, 확인할 포인트를 정리한다. 출력은 반드시 JSON으로 한다."
        )

    def _user_prompt(
        self,
        company: str,
        ticker: str,
        current_price: float | None,
        daily_change_percent: float | None,
        articles: list[dict],
    ) -> str:
        news_lines = []
        for index, article in enumerate(articles[:10], start=1):
            news_lines.append(
                f"{index}. 제목: {article.get('title')}\n"
                f"   요약: {article.get('description') or article.get('title')}\n"
                f"   출처: {article.get('source')}\n"
                f"   날짜: {article.get('publishedAt')}"
            )
        return (
            f"종목명: {company}\n"
            f"티커: {ticker}\n"
            f"현재가: {current_price if current_price is not None else '알 수 없음'}\n"
            f"당일 등락률: {daily_change_percent if daily_change_percent is not None else '알 수 없음'}%\n\n"
            "최근 뉴스 목록:\n"
            + "\n".join(news_lines)
            + "\n\nJSON 형식:\n"
            "{\n"
            '  "sentiment": "positive|neutral|negative|mixed",\n'
            '  "sentimentScore": -100,\n'
            '  "oneLine": "한 줄 요약",\n'
            '  "summary": "종합 분석",\n'
            '  "keyIssues": ["핵심 이슈"],\n'
            '  "positiveFactors": ["긍정 요인"],\n'
            '  "negativeFactors": ["부정 요인"],\n'
            '  "riskFactors": ["리스크"],\n'
            '  "watchPoints": ["확인할 포인트"],\n'
            '  "confidence": "high|medium|low"\n'
            "}"
        )

    def _shape_ai_result(self, ticker: str, company: str, news: dict, ai_result: dict, provider: str) -> dict:
        article_count = len(news.get("articles", []))
        confidence = self._safe_confidence(ai_result.get("confidence"))
        if article_count < 3:
            confidence = "low"
        result = {
            "ticker": ticker,
            "companyName": company,
            "newsSource": news.get("source", "FALLBACK"),
            "aiProvider": provider,
            "sentiment": self._safe_sentiment(ai_result.get("sentiment")),
            "sentimentScore": self._clamp_score(ai_result.get("sentimentScore")),
            "oneLine": self._safe_text(ai_result.get("oneLine"), "최근 뉴스 흐름을 보수적으로 확인해야 합니다."),
            "summary": self._safe_text(ai_result.get("summary"), "제공된 뉴스 범위 안에서만 참고용으로 해석했습니다."),
            "keyIssues": self._safe_list(ai_result.get("keyIssues"), ["최근 뉴스 흐름 확인"]),
            "positiveFactors": self._safe_list(ai_result.get("positiveFactors"), ["명확한 긍정 요인은 추가 확인이 필요합니다."]),
            "negativeFactors": self._safe_list(ai_result.get("negativeFactors"), ["뉴스 수가 제한적이면 부정 요인을 과소평가할 수 있습니다."]),
            "riskFactors": self._safe_list(ai_result.get("riskFactors"), ["무료 뉴스 API 기반이라 누락과 지연 가능성이 있습니다."]),
            "watchPoints": self._safe_list(ai_result.get("watchPoints"), ["추가 뉴스와 가격 반응을 함께 확인하세요."]),
            "newsItems": self._news_items(news.get("articles", [])),
            "confidence": confidence,
            "cacheHit": False,
            "disclaimer": NEWS_AI_DISCLAIMER,
        }
        return clean_json(result)

    def _fallback_result(self, ticker: str, company: str, news: dict, provider: str, reason: str | None) -> dict:
        articles = news.get("articles", [])
        score = self._keyword_score(articles)
        sentiment = "positive" if score >= 25 else "negative" if score <= -25 else "mixed" if articles else "neutral"
        if not articles:
            one_line = reason or "최근 뉴스를 불러오지 못해 뉴스 기반 분석을 제한적으로 표시합니다."
            summary = "뉴스 API 키가 없거나 외부 API 응답이 없어 기술적 분석과 가격 흐름을 우선 확인해야 합니다."
        else:
            one_line = "최근 뉴스 제목 기준으로는 긍정과 부정 요인을 함께 확인해야 합니다."
            summary = "AI API 호출이 실패해 뉴스 제목과 요약의 키워드만 기반으로 보수적으로 분류했습니다."
        result = {
            "ticker": ticker,
            "companyName": company,
            "newsSource": news.get("source", "FALLBACK"),
            "aiProvider": provider,
            "sentiment": sentiment,
            "sentimentScore": score,
            "oneLine": one_line,
            "summary": summary,
            "keyIssues": self._keyword_issues(articles),
            "positiveFactors": self._keyword_positive(articles),
            "negativeFactors": self._keyword_negative(articles),
            "riskFactors": ["뉴스 수가 부족하거나 AI API 호출이 실패해 해석 신뢰도가 낮습니다."],
            "watchPoints": ["원문 기사, 공시, 실적 일정, 가격 반응을 함께 확인하세요."],
            "newsItems": self._news_items(articles),
            "confidence": "low" if len(articles) < 3 else "medium",
            "cacheHit": False,
            "disclaimer": NEWS_AI_DISCLAIMER,
        }
        return clean_json(result)

    def _keyword_score(self, articles: list[dict]) -> int:
        positive = ["beat", "growth", "surge", "record", "upgrade", "strong", "ai", "수요", "호실적", "성장", "상향", "강세", "계약"]
        negative = ["miss", "drop", "cut", "probe", "lawsuit", "weak", "delay", "부진", "하락", "소송", "규제", "리콜", "둔화"]
        text = " ".join(f"{item.get('title', '')} {item.get('description', '')}" for item in articles).lower()
        score = sum(12 for word in positive if word.lower() in text) - sum(14 for word in negative if word.lower() in text)
        return max(-100, min(100, score))

    def _keyword_issues(self, articles: list[dict]) -> list[str]:
        if not articles:
            return ["최근 뉴스 데이터 부족"]
        return [item.get("title", "최근 뉴스 확인")[:80] for item in articles[:3]]

    def _keyword_positive(self, articles: list[dict]) -> list[str]:
        score = self._keyword_score(articles)
        if score > 0:
            return ["일부 뉴스에서 성장, 수요, 실적 관련 긍정 키워드가 확인됩니다."]
        return ["명확한 긍정 요인은 원문 기사 확인이 필요합니다."]

    def _keyword_negative(self, articles: list[dict]) -> list[str]:
        score = self._keyword_score(articles)
        if score < 0:
            return ["일부 뉴스에서 규제, 부진, 하락 관련 부담 키워드가 확인됩니다."]
        return ["부정 요인은 제한적으로 감지되지만, 뉴스 누락 가능성은 있습니다."]

    def _news_items(self, articles: list[dict]) -> list[dict]:
        return [
            {
                "title": item.get("title"),
                "description": item.get("description") or item.get("title"),
                "url": item.get("url"),
                "source": item.get("source"),
                "publishedAt": item.get("publishedAt"),
            }
            for item in articles[:10]
        ]

    def _safe_sentiment(self, value: object) -> str:
        text = str(value or "mixed").lower()
        return text if text in {"positive", "neutral", "negative", "mixed"} else "mixed"

    def _safe_confidence(self, value: object) -> str:
        text = str(value or "low").lower()
        return text if text in {"high", "medium", "low"} else "low"

    def _safe_text(self, value: object, fallback: str) -> str:
        text = str(value or "").strip()
        return text or fallback

    def _safe_list(self, value: object, fallback: list[str]) -> list[str]:
        if isinstance(value, list):
            items = [str(item).strip() for item in value if str(item).strip()]
            return items or fallback
        return fallback

    def _clamp_score(self, value: object) -> int:
        score = safe_float(value, 0) or 0
        return int(max(-100, min(100, round(score))))
