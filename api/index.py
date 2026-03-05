"""
TRMNL Crypto Tracker — Vercel Serverless Function

Returns crypto price data formatted for TRMNL's polling strategy.
Uses the free CoinGecko API (no API key required).

Configure which coins to track via the COINS query parameter:
  ?coins=bitcoin,ethereum,solana
"""

from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import json
import urllib.request

COINGECKO_API = "https://api.coingecko.com/api/v3/simple/price"

DEFAULT_COINS = "bitcoin,ethereum,solana,dogecoin,cardano"


def fetch_prices(coin_ids: str) -> dict:
    params = (
        f"?ids={coin_ids}"
        "&vs_currencies=usd"
        "&include_24hr_change=true"
        "&include_market_cap=true"
        "&include_24hr_vol=true"
    )
    url = COINGECKO_API + params
    req = urllib.request.Request(url, headers={"Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=10) as resp:
        return json.loads(resp.read().decode())


def format_price(price: float) -> str:
    if price >= 1:
        return f"${price:,.2f}"
    return f"${price:.4f}"


def format_market_cap(mc: float) -> str:
    if mc >= 1_000_000_000:
        return f"${mc / 1_000_000_000:.1f}B"
    if mc >= 1_000_000:
        return f"${mc / 1_000_000:.1f}M"
    return f"${mc:,.0f}"


def format_volume(vol: float) -> str:
    if vol >= 1_000_000_000:
        return f"${vol / 1_000_000_000:.1f}B"
    if vol >= 1_000_000:
        return f"${vol / 1_000_000:.1f}M"
    return f"${vol:,.0f}"


COIN_SYMBOLS = {
    "bitcoin": "BTC",
    "ethereum": "ETH",
    "solana": "SOL",
    "dogecoin": "DOGE",
    "cardano": "ADA",
    "ripple": "XRP",
    "polkadot": "DOT",
    "avalanche-2": "AVAX",
    "chainlink": "LINK",
    "polygon-ecosystem-token": "POL",
    "litecoin": "LTC",
    "uniswap": "UNI",
}


def build_response(coin_ids: str) -> dict:
    raw = fetch_prices(coin_ids)

    coins = []
    for coin_id, data in raw.items():
        price = data.get("usd", 0)
        change = data.get("usd_24h_change", 0) or 0
        market_cap = data.get("usd_market_cap", 0) or 0
        volume = data.get("usd_24h_vol", 0) or 0

        coins.append({
            "id": coin_id,
            "symbol": COIN_SYMBOLS.get(coin_id, coin_id[:4].upper()),
            "name": coin_id.replace("-", " ").title(),
            "price": format_price(price),
            "price_raw": price,
            "change_24h": round(change, 2),
            "change_direction": "up" if change >= 0 else "down",
            "change_display": f"{'+' if change >= 0 else ''}{change:.2f}%",
            "market_cap": format_market_cap(market_cap),
            "volume_24h": format_volume(volume),
        })

    # Sort by market cap descending
    coins.sort(key=lambda c: c.get("price_raw", 0), reverse=True)

    return {
        "coins": coins,
        "count": len(coins),
        "top_coin": coins[0] if coins else None,
    }


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            query = parse_qs(urlparse(self.path).query)
            coin_ids = query.get("coins", [DEFAULT_COINS])[0]

            data = build_response(coin_ids)

            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Cache-Control", "s-maxage=300, stale-while-revalidate=60")
            self.end_headers()
            self.wfile.write(json.dumps(data).encode())
        except Exception as e:
            self.send_response(500)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode())
