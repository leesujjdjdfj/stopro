from __future__ import annotations

import time
from datetime import datetime, timedelta
from typing import Optional

import pandas as pd
import requests

from app.core.cache import cache
from app.core.config import get_settings
from app.core.errors import StockDataError
from app.core.utils import normalize_ticker, now_iso, safe_float, safe_int
from app.data.providers.kis_token_manager import clean_kis_env_value, kis_token_manager
from app.data.symbol_search import lookup_symbol


class KisProvider:
    source = "KIS_REST"

    def __init__(self) -> None:
        self.settings = get_settings()

    def is_enabled(self) -> bool:
        return kis_token_manager.is_configured()

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

        params = {
            "FID_COND_MRKT_DIV_CODE": "J",
            "FID_INPUT_ISCD": code,
        }
        data = self._request_kis_json(
            path="/uapi/domestic-stock/v1/quotations/inquire-price",
            tr_id="FHKST01010100",
            params=params,
            error_message="KIS 현재가 조회에 실패했습니다.",
        )

        output = data.get("output") or {}
        current_price = self._to_float(output.get("stck_prpr"))
        daily_change = self._to_float(output.get("prdy_vrss"))
        previous_close = self._to_float(output.get("stck_sdpr"))
        if previous_close is None and current_price is not None and daily_change is not None:
            previous_close = current_price - daily_change

        symbol = lookup_symbol(code) or {}
        market = symbol.get("market") or "KRX"
        quote = {
            "ticker": code,
            "displayTicker": code,
            "name": symbol.get("name") or output.get("hts_kor_isnm") or code,
            "market": market,
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
        rows: list[dict] = []
        seen_dates: set[str] = set()

        max_pages = max(1, min(8, int(days / 90) + 1))
        for page in range(max_pages):
            if page > 0:
                time.sleep(0.65)
            try:
                batch = self._request_daily_chart(code, start, end)
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

    def _request_daily_chart(self, code: str, start: datetime, end: datetime) -> list[dict]:
        params = {
            "FID_COND_MRKT_DIV_CODE": "J",
            "FID_INPUT_ISCD": code,
            "FID_INPUT_DATE_1": start.strftime("%Y%m%d"),
            "FID_INPUT_DATE_2": end.strftime("%Y%m%d"),
            "FID_PERIOD_DIV_CODE": "D",
            "FID_ORG_ADJ_PRC": "0",
        }
        data = self._request_kis_json(
            path="/uapi/domestic-stock/v1/quotations/inquire-daily-itemchartprice",
            tr_id="FHKST03010100",
            params=params,
            error_message="KIS 일봉 조회에 실패했습니다.",
        )
        return data.get("output2") or []

    def _request_kis_json(self, path: str, tr_id: str, params: dict, error_message: str) -> dict:
        url = f"{self.settings.kis_base_url}{path}"
        last_message = error_message
        for attempt in range(2):
            token = kis_token_manager.get_token()
            headers = {
                "content-type": "application/json",
                "authorization": f"Bearer {token}",
                "appkey": clean_kis_env_value(self.settings.kis_app_key),
                "appsecret": clean_kis_env_value(self.settings.kis_app_secret),
                "tr_id": tr_id,
                "custtype": "P",
            }
            try:
                response = self._session().get(url, headers=headers, params=params, timeout=8)
                try:
                    data = response.json()
                except ValueError:
                    data = {}
            except Exception as exc:
                raise StockDataError(error_message, 502) from exc

            if self._is_token_error(response.status_code, data) and attempt == 0:
                kis_token_manager.invalidate_token()
                continue

            if response.status_code == 200 and data.get("rt_cd") == "0":
                return data

            last_message = str(data.get("msg1") or error_message)
            break

        raise StockDataError(last_message, 502)

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

    def _is_token_error(self, status_code: int, data: dict) -> bool:
        if status_code == 401:
            return True
        message = str(data.get("msg1") or data.get("msg_cd") or "").lower()
        return "token" in message and any(keyword in message for keyword in ("만료", "expire", "invalid", "인증", "unauthorized"))
