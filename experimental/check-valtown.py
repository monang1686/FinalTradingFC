#!/usr/bin/env python3
"""Read-only Val Town FC27 endpoint diagnostic. No prices are stored or published."""
import json
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone

URL = "https://fc27-market.val.run/latest"

def main():
    req = urllib.request.Request(URL, headers={"Accept": "application/json", "User-Agent": "FUT-Trader-27-Diagnostic/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=20) as response:
            if response.status != 200:
                print("HTTP status:", response.status)
                return 1
            raw = response.read(2_000_001)
            if len(raw) > 2_000_000:
                print("FAIL: response exceeds 2 MB")
                return 1
            data = json.loads(raw)
    except (urllib.error.URLError, TimeoutError, ValueError) as exc:
        print("UNAVAILABLE:", type(exc).__name__, str(exc)[:200])
        return 2
    if not isinstance(data, dict) or not isinstance(data.get("groups"), dict):
        print("FAIL: unexpected JSON schema")
        return 1
    groups = data["groups"]
    allowed = ("icons", "heroes", "bronze", "silver", "gold", "special")
    counts = {}
    invalid = 0
    for group in allowed:
        rows = groups.get(group, [])
        if not isinstance(rows, list):
            print("FAIL: group", group, "is not an array")
            return 1
        counts[group] = len(rows)
        for row in rows:
            if not isinstance(row, dict) or not isinstance(row.get("eaId"), int) or not isinstance(row.get("price"), int) or row["price"] <= 0:
                invalid += 1
    updated = data.get("updated")
    age_minutes = None
    try:
        parsed = datetime.fromisoformat(updated.replace("Z", "+00:00"))
        age_minutes = round((datetime.now(timezone.utc) - parsed.astimezone(timezone.utc)).total_seconds() / 60, 1)
    except (AttributeError, ValueError):
        pass
    print(json.dumps({"endpoint": URL, "source_updated": updated, "age_minutes": age_minutes,
                      "group_counts": counts, "total": sum(counts.values()),
                      "invalid_rows": invalid, "has_listing_ids": False,
                      "source_license_verified": False,
                      "safe_for_live_signals": False}, ensure_ascii=False, indent=2))
    return 0 if invalid == 0 and age_minutes is not None and 0 <= age_minutes <= 60 else 1

if __name__ == "__main__":
    sys.exit(main())
