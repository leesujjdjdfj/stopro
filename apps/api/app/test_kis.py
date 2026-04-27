import os
import sys
from pathlib import Path

from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.data.providers.kis_provider import KisProvider


load_dotenv()
for proxy_key in ["HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY", "http_proxy", "https_proxy", "all_proxy"]:
    os.environ.pop(proxy_key, None)

def require_env():
    missing = [
        name
        for name, value in {
            "KIS_APP_KEY": os.getenv("KIS_APP_KEY"),
            "KIS_APP_SECRET": os.getenv("KIS_APP_SECRET"),
            "KIS_BASE_URL": os.getenv("KIS_BASE_URL"),
        }.items()
        if not value
    ]
    if missing:
        raise RuntimeError(f"Missing environment values: {', '.join(missing)}")


def get_token(provider):
    require_env()
    token = provider._get_access_token()
    print("TOKEN OK:", {"access_token": mask_token(token)})
    return token


def get_price(provider, ticker="005930"):
    quote = provider.get_quote(ticker)
    print("PRICE OK:", {
        "ticker": quote.get("ticker"),
        "name": quote.get("name"),
        "price": quote.get("price"),
        "change": quote.get("dailyChange"),
        "change_rate": quote.get("dailyChangePercent"),
        "volume": quote.get("volume"),
        "source": quote.get("source"),
    })
    return quote


def mask_token(value):
    if not value:
        return None
    return f"{value[:8]}...{value[-6:]}"


if __name__ == "__main__":
    ticker_arg = sys.argv[1] if len(sys.argv) > 1 else "005930"
    kis = KisProvider()
    get_token(kis)
    get_price(kis, ticker_arg)
