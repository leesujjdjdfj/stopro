from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.data.providers.kis_provider import KisProvider  # noqa: E402
from app.data.providers.kis_token_manager import kis_token_manager  # noqa: E402


def main() -> int:
    ticker = sys.argv[1] if len(sys.argv) > 1 else "005930"
    status_before = kis_token_manager.status()
    print("configured:", status_before["configured"])

    if not status_before["configured"]:
        print("KIS API 설정이 비활성화되어 있습니다.")
        return 0

    try:
        kis_token_manager.get_token()
        status_after = kis_token_manager.status()
        print("tokenIssued:", status_after["hasToken"])
        print("expiresInSeconds:", status_after["expiresInSeconds"])

        quote = KisProvider().get_quote(ticker)
        safe_quote = {
            "ticker": quote.get("ticker"),
            "name": quote.get("name"),
            "source": quote.get("source"),
            "price": quote.get("price"),
            "dailyChangePercent": quote.get("dailyChangePercent"),
        }
        print("quote:")
        print(json.dumps(safe_quote, ensure_ascii=False, indent=2))
        return 0
    except Exception as exc:
        print("KIS token test failed:", str(exc))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
