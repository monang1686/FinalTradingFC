"""Opt-in, one-shot quick-fut-price bridge for FUT Trader 27.

Requires installed WilgotM/quick-fut-price SDK and permitted use of FUTBIN data.
No schedule, no proxies, no CAPTCHA bypass, no credentials, no EA trading.
Writes to an explicit output file; NEVER publishes to production automatically.
Usage:
  python quick_fut_price_bridge.py --ids 8 --output prices-live.json
FUTBIN IDs are not EA resource IDs. Verify mapping before interpreting cards.
"""
import argparse
import asyncio
import json
from datetime import datetime, timezone
from pathlib import Path


async def collect(ids):
    from futbin_sdk import FutbinClient, Platform
    items = []
    async with FutbinClient(year=27, timeout=10) as client:
        for player_id in ids:
            try:
                quote = await client.get_player_price(player_id, Platform.PS, year=27)
                price = quote.price
                if type(price) is not int or not 1 <= price <= 15_000_000:
                    continue
                items.append({
                    "game": "fc27", "futbin_id": player_id, "platform": "ps",
                    "market": "console", "price": price,
                    "observed_at": datetime.now(timezone.utc).isoformat(),
                    "source_updated": str(quote.updated or ""),
                    "exact": False,
                    "source": "quick-fut-price/futbin_unofficial",
                })
            except Exception as exc:
                print(f"FUTBIN ID {player_id}: unavailable ({type(exc).__name__})")
            # One-shot and deliberately slow. No automatic retries.
            await asyncio.sleep(3)
    return {"format": "fut27-quick-fut-price-v1", "success": True,
            "data_kind": "unverified_third_party_quote", "production_signals": [],
            "data": {"items": items}}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--ids", required=True, help="Comma-separated FUTBIN IDs, max 10")
    parser.add_argument("--output", required=True, help="Explicit local JSON output path")
    args = parser.parse_args()
    raw = args.ids.split(",")
    if not 1 <= len(raw) <= 10 or any(not x.strip().isdigit() or not 0 < int(x) < 10_000_000 for x in raw):
        parser.error("Provide 1–10 valid FUTBIN IDs")
    ids = list(dict.fromkeys(int(x) for x in raw))
    payload = asyncio.run(collect(ids))
    path = Path(args.output)
    if path.exists():
        parser.error("Output already exists; choose a new filename to avoid overwriting")
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Saved {len(payload['data']['items'])} unverified quotes to {path}")


if __name__ == "__main__":
    main()
