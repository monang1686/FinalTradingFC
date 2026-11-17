"""Read-only diagnostic for a public FC27 PS market JSON feed. Never publishes."""
import argparse
import datetime as dt
import json
import sys
import urllib.error
import urllib.request

URL = "https://fc27-market.val.run/latest"
GROUPS = ("icons", "heroes", "bronze", "silver", "gold", "special")

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--url", default=URL)
    args = p.parse_args()
    if args.url != URL:
        p.error("Only the allowlisted public endpoint is supported")
    req = urllib.request.Request(args.url, headers={"Accept": "application/json", "User-Agent": "FUT-Trader-27-diagnostic/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=15) as res:
            data = json.load(res)
            print("HTTP:", res.status)
    except urllib.error.HTTPError as e:
        print("HTTP error:", e.code)
        return 2
    except (urllib.error.URLError, ValueError, TimeoutError) as e:
        print("Feed unavailable:", type(e).__name__)
        return 2
    groups = data.get("groups")
    if not isinstance(groups, dict):
        print("Invalid response: missing groups")
        return 3
    observations = []
    for group in GROUPS:
        rows = groups.get(group, [])
        if not isinstance(rows, list):
            print("Invalid group:", group)
            return 3
        for row in rows:
            if not isinstance(row, dict):
                continue
            ea_id, price = row.get("eaId"), row.get("price")
            if type(ea_id) is int and ea_id > 0 and type(price) is int and 0 < price <= 15000000:
                observations.append((group, ea_id, row.get("name"), price))
    print("Valid price observations:", len(observations))
    print("Sample (max 5):", json.dumps(observations[:5], ensure_ascii=False))
    stamp = data.get("updated")
    try:
        updated = dt.datetime.fromisoformat(stamp.replace("Z", "+00:00"))
        age = (dt.datetime.now(dt.timezone.utc) - updated).total_seconds() / 60
        fresh = -5 <= age <= 90
        print("Feed updated:", stamp, "age_minutes:", round(age, 1), "fresh_90m:", fresh)
    except (TypeError, ValueError, AttributeError):
        fresh = False
        print("Missing or invalid updated timestamp")
    print("Read-only diagnostic; no publishing, trading, or scheduling")
    return 0 if observations and fresh else 4

if __name__ == "__main__":
    sys.exit(main())
