"""Experimental Val Town snapshot collector. Not approved for trading signals."""
import datetime as dt
import json
import sys
import urllib.error
import urllib.request
from pathlib import Path

URL = "https://fc27-market.val.run/latest"
GROUPS = ("icons", "heroes", "bronze", "silver", "gold", "special")

def transform(data, now=None):
    now = now or dt.datetime.now(dt.timezone.utc)
    if not isinstance(data, dict) or not isinstance(data.get("groups"), dict):
        raise ValueError("missing groups")
    stamp = data.get("updated")
    if not isinstance(stamp, str):
        raise ValueError("missing updated timestamp")
    at = dt.datetime.fromisoformat(stamp.replace("Z", "+00:00"))
    if at.tzinfo is None:
        raise ValueError("timezone required")
    age = (now - at).total_seconds() / 60
    if not -5 <= age <= 90:
        raise ValueError("stale or future timestamp")
    seen = set()
    cards = []
    for group in GROUPS:
        rows = data["groups"].get(group, [])
        if not isinstance(rows, list):
            raise ValueError("invalid group")
        for row in rows:
            if not isinstance(row, dict):
                continue
            identifier, price, name = row.get("eaId"), row.get("price"), row.get("name")
            if type(identifier) is not int or identifier <= 0 or type(price) is not int or not 0 < price <= 15000000 or not isinstance(name, str) or not name.strip():
                continue
            # EA ID alone may not uniquely identify a card version.
            key = (group, identifier)
            if key in seen:
                raise ValueError("duplicate group and EA ID")
            seen.add(key)
            cards.append({"group": group, "ea_id": identifier, "name": name.strip(), "price": price, "observed_at": stamp})
    if not cards:
        raise ValueError("no valid prices")
    return {"schema": "fut27-experimental-feed-v1", "source": URL, "game": "FC27",
            "platform_claim": "PlayStation", "verified": False, "tradeable_verified": False,
            "production_signals_enabled": False, "updated_at": stamp, "count": len(cards), "cards": cards}

def main():
    if len(sys.argv) != 2:
        raise SystemExit("Usage: python valtown_snapshot.py OUTPUT.json")
    req = urllib.request.Request(URL, headers={"Accept": "application/json", "User-Agent": "FUT-Trader-27-diagnostic/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=15) as res:
            if res.status != 200:
                raise ValueError("non-200 response")
            data = json.load(res)
        result = transform(data)
        path = Path(sys.argv[1])
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print("Experimental snapshot:", result["count"], "cards; source updated:", result["updated_at"])
        print("Unverified feed: NO production signals")
    except (urllib.error.URLError, ValueError, TimeoutError) as exc:
        print("Snapshot rejected:", type(exc).__name__, str(exc) if isinstance(exc, ValueError) else "")
        raise SystemExit(1)

if __name__ == "__main__":
    main()
