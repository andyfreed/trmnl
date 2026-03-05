# TRMNL Crypto Tracker

A custom TRMNL plugin that displays live cryptocurrency prices on your e-ink display. Uses the free CoinGecko API and deploys as a Vercel serverless function.

## What's in here

```
api/index.py          — Vercel serverless function (fetches crypto prices)
templates/full.liquid  — Full-screen layout (table with all coins)
templates/half_horizontal.liquid — Half-screen layout (top 3 coins)
templates/quadrant.liquid — Quadrant layout (top coin only)
settings.yml          — Plugin config reference
vercel.json           — Vercel routing config
```

## Setup (step by step)

### 1. Deploy to Vercel

Install the [Vercel CLI](https://vercel.com/docs/cli) if you haven't:

```bash
npm i -g vercel
```

Deploy:

```bash
cd trmnl
vercel
```

Follow the prompts. Once deployed, you'll get a URL like `https://your-app.vercel.app`.

Test it:

```bash
curl https://your-app.vercel.app/api
```

You should see JSON with crypto prices.

### 2. Configure your TRMNL plugin

1. Log into [usetrmnl.com](https://usetrmnl.com)
2. Go to **Plugins** → search for **Private Plugin** → install it
3. Configure the plugin:
   - **Strategy**: Polling
   - **Polling URL**: `https://your-app.vercel.app/api`
   - **Refresh**: 15 minutes (or your preference)
4. Click **Save**, then click **Edit Markup**
5. Paste the contents of one of the template files (e.g., `templates/full.liquid`) into the markup editor
6. Click **Save** and you're done!

### 3. Customize which coins to track

Add a `coins` query parameter to your polling URL:

```
https://your-app.vercel.app/api?coins=bitcoin,ethereum,solana
```

Supported coin IDs are from CoinGecko. Some common ones:

| Coin | ID |
|------|----|
| Bitcoin | `bitcoin` |
| Ethereum | `ethereum` |
| Solana | `solana` |
| Dogecoin | `dogecoin` |
| Cardano | `cardano` |
| XRP | `ripple` |
| Polkadot | `polkadot` |
| Avalanche | `avalanche-2` |
| Chainlink | `chainlink` |
| Litecoin | `litecoin` |

Find more IDs at [coingecko.com/en/all-cryptocurrencies](https://www.coingecko.com/en/all-cryptocurrencies).

## API Response Format

The serverless function returns JSON like this:

```json
{
  "coins": [
    {
      "symbol": "BTC",
      "name": "Bitcoin",
      "price": "$97,123.45",
      "change_24h": 2.34,
      "change_direction": "up",
      "change_display": "+2.34%",
      "market_cap": "$1.9T",
      "volume_24h": "$28.5B"
    }
  ],
  "count": 5,
  "top_coin": { ... }
}
```

## Notes

- The CoinGecko free API has a rate limit (~30 requests/minute). With TRMNL polling every 15 minutes, you'll be well within limits.
- Vercel caches responses for 5 minutes (`s-maxage=300`) to stay within rate limits.
- No API key is needed for CoinGecko's free tier.
- The TRMNL device is e-ink, so the templates use simple black/white layouts with up/down arrows (▲/▼) instead of colors.
