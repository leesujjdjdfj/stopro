from __future__ import annotations

import threading
import time
from typing import Optional

import requests

from app.core.config import get_settings
from app.core.errors import StockDataError


class KISProviderError(StockDataError):
    pass


def clean_kis_env_value(value: str | None) -> str:
    return (value or "").strip().lstrip("\ufeff")


class KISTokenManager:
    def __init__(self) -> None:
        self._access_token: Optional[str] = None
        self._expires_at: float = 0.0
        self._last_issued_at: float = 0.0
        self._lock = threading.Lock()

    def is_configured(self) -> bool:
        settings = get_settings()
        return bool(
            settings.kis_enabled
            and clean_kis_env_value(settings.kis_app_key)
            and clean_kis_env_value(settings.kis_app_secret)
            and clean_kis_env_value(settings.kis_base_url)
        )

    def has_valid_token(self) -> bool:
        return bool(self._access_token and time.time() < self._expires_at)

    def get_token(self) -> str:
        if self.has_valid_token():
            return self._access_token or ""

        with self._lock:
            if self.has_valid_token():
                return self._access_token or ""
            return self.issue_token()

    def issue_token(self) -> str:
        settings = get_settings()
        if not self.is_configured():
            raise KISProviderError("KIS API 설정이 비활성화되어 있습니다.", 503)

        session = requests.Session()
        session.trust_env = False
        url = f"{settings.kis_base_url}/oauth2/tokenP"
        body = {
            "grant_type": "client_credentials",
            "appkey": clean_kis_env_value(settings.kis_app_key),
            "appsecret": clean_kis_env_value(settings.kis_app_secret),
        }
        try:
            response = session.post(url, headers={"content-type": "application/json"}, json=body, timeout=8)
            data = response.json()
        except Exception as exc:
            raise KISProviderError("KIS 토큰 발급에 실패했습니다.", 502) from exc

        token = data.get("access_token") if isinstance(data, dict) else None
        if response.status_code != 200 or not token:
            raise KISProviderError("KIS 토큰 발급에 실패했습니다.", 502)

        now = time.time()
        ttl = self._token_ttl_seconds(data.get("expires_in"))
        self._access_token = str(token)
        self._expires_at = now + ttl
        self._last_issued_at = now
        return self._access_token

    def invalidate_token(self) -> None:
        with self._lock:
            self._access_token = None
            self._expires_at = 0.0

    def status(self) -> dict:
        now = time.time()
        expires_in = max(0, int(self._expires_at - now)) if self._access_token else 0
        return {
            "configured": self.is_configured(),
            "hasToken": self.has_valid_token(),
            "expiresInSeconds": expires_in,
            "lastIssuedAt": int(self._last_issued_at) if self._last_issued_at else None,
            "message": "KIS token manager is ready" if self.is_configured() else "KIS API 설정이 비활성화되어 있습니다.",
        }

    def _token_ttl_seconds(self, expires_in: object) -> int:
        settings = get_settings()
        max_ttl = int(getattr(settings, "kis_token_cache_seconds", 23 * 60 * 60) or 23 * 60 * 60)
        try:
            official_ttl = int(expires_in)
        except (TypeError, ValueError):
            official_ttl = 24 * 60 * 60

        safe_ttl = official_ttl - 60 * 60 if official_ttl > 60 * 60 else official_ttl - 60
        return max(60, min(max_ttl, safe_ttl))


kis_token_manager = KISTokenManager()
