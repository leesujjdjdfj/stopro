from functools import lru_cache
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    usd_krw: float = 1350.0
    cache_ttl_seconds: int = 300
    exchange_rate_cache_ttl_seconds: int = 1800
    database_url: str = "sqlite:///./stopro.db"
    kis_enabled: bool = False
    kis_env: str = "paper"
    kis_app_key: Optional[str] = None
    kis_app_secret: Optional[str] = None
    kis_base_url: str = "https://openapivts.koreainvestment.com:29443"
    kis_ws_url: str = "ws://ops.koreainvestment.com:31000"
    kis_quote_cache_ttl_seconds: int = 5
    kis_token_cache_seconds: int = 82800
    gnews_api_key: Optional[str] = None
    news_api_key: Optional[str] = None
    news_provider: str = "gnews"
    groq_api_key: Optional[str] = None
    openrouter_api_key: Optional[str] = None
    ai_provider: str = "groq"
    ai_model: str = "llama-3.1-8b-instant"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()
