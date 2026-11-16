"""Read-only, ephemeral comparison of two Val Town responses.

No raw prices, identifiers or names are printed or stored. No automatic schedule.
This diagnostic does not authorize ingestion or reuse.
"""
import json
import sys
import time
import urllib.request
from datetime import datetime, timezone
from valtown_adapter import inspect
from market_engine import stamp

URL = "https://fc27-market.val.run/latest"
MAX_BYTES = 4_000_000
DELAY_SECONDS = 60

def fetch():
    request = urllib.request.Request(URL, headers={
        "User-Agent": "FUTTrader27-Diagnostic/1.0",
        "Accept": "application/json",
    })
    with urllib.request.urlopen(request, timeout=20) as response:
        if response.status != 200 or response.headers.get_content_type() != "application/json":
            raise ValueError("unexpected response")
        raw = response.read(MAX_BYTES + 1)
    if len(raw) > MAX_BYTES:
        raise ValueError("oversized response")
    payload = json.loads(raw)
    quality = inspect(payload)
    if quality["invalid_prices"] or quality["missing_ids"] or quality["duplicate_pairs"] or quality["duplicate_ea_ids"] or quality["invalid_ea_ids"]:
        raise ValueError("feed quality failed")
    return payload, quality

def rows(payload):
    return {
        (str(card["eaId"]), str(card["rarityId"])): card["price"]
        for cards in payload["groups"].values()
        for card in cards
    }

def compare(first, second, q1, q2, interval_seconds=None):
    a, b = rows(first), rows(second)
    shared = a.keys() & b.keys()
    changed = sum(a[k] != b[k] for k in shared)
    return {
        "first_feed_updated": q1["updated"],
        "second_feed_updated": q2["updated"],
        "first_cards": len(a),
        "second_cards": len(b),
        "shared_cards": len(shared),
        "new_cards": len(b.keys() - a.keys()),
        "removed_cards": len(a.keys() - b.keys()),
        "price_changes": changed,
        "unchanged_prices": len(shared) - changed,
        "feed_timestamp_advanced": stamp(q2["updated"]) > stamp(q1["updated"]),
        "feed_timestamp_regressed": stamp(q2["updated"]) < stamp(q1["updated"]),
        "observation_interval_seconds": interval_seconds,
        "conclusion": "Two samples cannot establish update frequency or accuracy",
        "data_reuse_authorized": False,
        "collection_enabled": False,
    }

def main():
    started = time.monotonic()
    first, q1 = fetch()
    time.sleep(DELAY_SECONDS)
    second, q2 = fetch()
    print(json.dumps(compare(first, second, q1, q2, time.monotonic()-started), indent=2))
    return 0

if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:
        print(json.dumps({"status": "diagnostic_failed", "error_type": type(exc).__name__}))
        sys.exit(1)
