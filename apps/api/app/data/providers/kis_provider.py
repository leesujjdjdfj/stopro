from __future__ import annotations

import hashlib
import json
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

import pandas as pd
import requests

from app.core.cache import cache
from app.core.config import get_settings
from app.core.errors import StockDataError
from app.core.utils import normalize_ticker, now_iso, safe_float, safe_int
from app.data.symbol_search import lookup_symbol


class KisProvider:
    source = "KIS"

    def __init__(self) -> None:
        self.settings = get_settings()

    def is_enabled(self) -> bool:
        return bool(self.settings.kis_enabled and self.settings.kis_app_key and self.settings.kis_app_secret and self.settings.kis_base_url)

    def supports(self, ticker: str) -> bool:
        normalized = normalize_ticker(ticker)
        return (normalized.isdigit() and len(normalized) == 6) or normalized.endswith((".KS", ".KQ"))

    def get_quote(self, ticker: str) -> dict:
        if not self.is_enabled():
            raise StockDataError("KIS API 설정이 비활성화되어 있습니다.", 503)
        code = self._to_domestic_code(ticker)
        key = f"kis:quote:{code}"
        cached, hit = cache.get(key)
        if hit:
            return {**cached, "cacheHit": True}

        token = self._get_access_token()
        session = self._session()
        url = f"{self.settings.kis_base_url}/uapi/domestic-stock/v1/quotations/inquire-price"
        headers = {
            "content-type": "application/json",
            "authorization": f"Bearer {token}",
            "appkey": self.settings.kis_app_key or "",
            "appsecret": self.settings.kis_app_secret or "",
            "tr_id": "FHKST01010100",
            "custtype": "P",
        }
        params = {
            "FID_COND_MRKT_DIV_CODE": "J",
            "FID_INPUT_ISCD": code,
        }
        try:
            response = session.get(url, headers=headers, params=params, timeout=8)
            data = response.json()
        except Exception as exc:
            raise StockDataError(f"KIS 현재가 조회에 실패했습니다: {exc}", 502) from exc

        if response.status_code != 200 or data.get("rt_cd") != "0":
            message = data.get("msg1") or "KIS 현재가 조회에 실패했습니다."
            raise StockDataError(message, 502)

        output = data.get("output") or {}
        current_price = self._to_float(output.get("stck_prpr"))
        daily_change = self._to_float(output.get("prdy_vrss"))
        previous_close = self._to_float(output.get("stck_sdpr"))
        if previous_close is None and current_price is not None and daily_change is not None:
            previous_close = current_price - daily_change

        symbol = lookup_symbol(code) or {}
        quote = {
            "ticker": code,
            "name": output.get("hts_kor_isnm") or symbol.get("name") or code,
            "currency": "KRW",
            "exchange": "KRX",
            "price": safe_float(current_price, 4),
            "previousClose": safe_float(previous_close, 4),
            "dailyChange": safe_float(daily_change, 4),
            "dailyChangePercent": safe_float(self._to_float(output.get("prdy_ctrt")), 2),
            "volume": safe_int(self._to_float(output.get("acml_vol"))),
            "averageVolume": None,
            "fiftyTwoWeekHigh": safe_float(self._to_float(output.get("w52_hgpr")), 4),
            "fiftyTwoWeekLow": safe_float(self._to_float(output.get("w52_lwpr")), 4),
            "dataTimestamp": now_iso(),
            "isDelayed": False,
            "isRealtime": True,
            "cacheHit": False,
            "source": self.source,
        }
        cache.set(key, quote, self.settings.kis_quote_cache_ttl_seconds)
        return quote

    def get_history(self, ticker: str, period: str = "2y") -> tuple[pd.DataFrame, bool, str]:
        if not self.is_enabled():
            raise StockDataError("KIS API 설정이 비활성화되어 있습니다.", 503)
        code = self._to_domestic_code(ticker)
        blocked, block_hit = cache.get(f"kis:history:block:{code}")
        if block_hit and blocked:
            raise StockDataError("KIS 일봉 API 호출 제한 중입니다. 잠시 후 다시 조회해 주세요.", 429)
        key = f"kis:history:{code}:{period}"
        cached, hit = cache.get(key)
        if hit:
            return cached.copy(), True, self.source

        days = {"1m": 45, "3m": 120, "6m": 220, "1y": 420, "2y": 780, "5y": 1900}.get(period.lower(), 780)
        start = datetime.now() - timedelta(days=days)
        end = datetime.now()
        token = self._get_access_token()
        rows: list[dict] = []
        seen_dates: set[str] = set()

        max_pages = max(1, min(8, int(days / 90) + 1))
        for page in range(max_pages):
            if page > 0:
                time.sleep(0.65)
            try:
                batch = self._request_daily_chart(code, token, start, end)
            except StockDataError as exc:
                if self._is_rate_limited(exc.message):
                    cache.set(f"kis:history:block:{code}", True, 10)
                    if rows:
                        break
                raise
            if not batch:
                break
            oldest: Optional[datetime] = None
            new_count = 0
            for item in batch:
                date_text = str(item.get("stck_bsop_date") or "")
                if not date_text or date_text in seen_dates:
                    continue
                seen_dates.add(date_text)
                parsed_date = datetime.strptime(date_text, "%Y%m%d")
                oldest = parsed_date if oldest is None or parsed_date < oldest else oldest
                rows.append(
                    {
                        "Date": parsed_date,
                        "Open": self._to_float(item.get("stck_oprc")),
                        "High": self._to_float(item.get("stck_hgpr")),
                        "Low": self._to_float(item.get("stck_lwpr")),
                        "Close": self._to_float(item.get("stck_clpr")),
                        "Volume": self._to_float(item.get("acml_vol")),
                    }
                )
                new_count += 1
            if new_count == 0 or oldest is None or oldest <= start or len(batch) < 100:
                break
            end = oldest - timedelta(days=1)

        if not rows:
            raise StockDataError("KIS 일봉 데이터를 찾을 수 없습니다.", 404)

        frame = pd.DataFrame(rows)
        frame = frame.dropna(subset=["Close"])
        frame = frame.sort_values("Date").drop_duplicates(subset=["Date"])
        frame = frame.set_index("Date")
        frame = frame[["Open", "High", "Low", "Close", "Volume"]]
        frame["Volume"] = frame["Volume"].fillna(0)
        frame.attrs["resolvedTicker"] = code
        cache.set(key, frame, self.settings.cache_ttl_seconds)
        return frame.copy(), False, self.source

    def _get_access_token(self) -> str:
        cached, hit = cache.get("kis:access_token")
        if hit and cached:
            return str(cached)
        file_token = self._read_token_file()
        if file_token:
            return file_token

        session = self._session()
        url = f"{self.settings.kis_base_url}/oauth2/tokenP"
        headers = {"content-type": "application/json"}
        body = {
            "grant_type": "client_credentials",
            "appkey": self.settings.kis_app_key,
            "appsecret": self.settings.kis_app_secret,
        }
        try:
            response = session.post(url, headers=headers, json=body, timeout=8)
            data = response.json()
        except Exception as exc:
            raise StockDataError(f"KIS 토큰 발급에 실패했습니다: {exc}", 502) from exc

        if response.status_code != 200 or "access_token" not in data:
            message = data.get("msg1") or "KIS 토큰 발급에 실패했습니다."
            raise StockDataError(message, 502)

        token = data["access_token"]
        ttl = max(60, int(data.get("expires_in") or 86400) - 60)
        cache.set("kis:access_token", token, ttl)
        self._write_token_file(token, ttl)
        return token

    def _request_daily_chart(self, code: str, token: str, start: datetime, end: datetime) -> list[dict]:
        session = self._session()
        url = f"{self.settings.kis_base_url}/uapi/domestic-stock/v1/quotations/inquire-daily-itemchartprice"
        headers = {
            "content-type": "application/json",
            "authorization": f"Bearer {token}",
            "appkey": self.settings.kis_app_key or "",
            "appsecret": self.settings.kis_app_secret or "",
            "tr_id": "FHKST03010100",
            "custtype": "P",
        }
        params = {
            "FID_COND_MRKT_DIV_CODE": "J",
            "FID_INPUT_ISCD": code,
            "FID_INPUT_DATE_1": start.strftime("%Y%m%d"),
            "FID_INPUT_DATE_2": end.strftime("%Y%m%d"),
            "FID_PERIOD_DIV_CODE": "D",
            "FID_ORG_ADJ_PRC": "0",
        }
        try:
            response = session.get(url, headers=headers, params=params, timeout=8)
            data = response.json()
        except Exception as exc:
            raise StockDataError(f"KIS 일봉 조회에 실패했습니다: {exc}", 502) from exc
        if response.status_code != 200 or data.get("rt_cd") != "0":
            message = data.get("msg1") or "KIS 일봉 조회에 실패했습니다."
            raise StockDataError(message, 502)
        return data.get("output2") or []

    def _session(self) -> requests.Session:
        session = requests.Session()
        session.trust_env = False
        return session

    def _to_domestic_code(self, ticker: str) -> str:
        normalized = normalize_ticker(ticker)
        return normalized.replace(".KS", "").replace(".KQ", "")

    def _to_float(self, value: Optional[str]) -> Optional[float]:
        if value is None:
            return None
        text = str(value).replace(",", "").strip()
        if not text:
            return None
        try:
            return float(text)
        except ValueError:
            return None

    def _is_rate_limited(self, message: str) -> bool:
        return any(keyword in message for keyword in ("초당 거래건수", "호출 제한", "rate", "Rate"))

    def _token_cache_path(self) -> Path:
        return Path.cwd() / ".kis_token_cache.json"

    def _token_fingerprint(self) -> str:
        source = f"{self.settings.kis_base_url}:{self.settings.kis_app_key or ''}"
        return hashlib.sha256(source.encode("utf-8")).hexdigest()

    def _read_token_file(self) -> Optional[str]:
        path = self._token_cache_path()
        if not path.exists():
            return None
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            return None
        token = payload.get("access_token")
        expires_at = float(payload.get("expires_at") or 0)
        if not token or payload.get("fingerprint") != self._token_fingerprint() or expires_at <= time.time() + 60:
            return None
        cache.set("kis:access_token", token, max(60, int(expires_at - time.time())))
        return str(token)

    def _write_token_file(self, token: str, ttl: int) -> None:
        payload = {
            "access_token": token,
            "expires_at": time.time() + ttl,
            "fingerprint": self._token_fingerprint(),
        }
        try:
            self._token_cache_path().write_text(json.dumps(payload), encoding="utf-8")
        except Exception:
            pass
