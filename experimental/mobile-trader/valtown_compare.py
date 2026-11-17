"""Offline comparison of two unverified experimental FC27 snapshots."""
import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

def timestamp(value):
    t = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if t.tzinfo is None:
        raise ValueError("timestamp needs timezone")
    return t.astimezone(timezone.utc)

def index(snapshot):
    if snapshot.get("schema") != "fut27-experimental-feed-v1" or snapshot.get("verified") is not False or snapshot.get("production_signals_enabled") is not False:
        raise ValueError("not an experimental snapshot")
    cards = {}
    for card in snapshot["cards"]:
        key = (card["group"], card["ea_id"])
        if key in cards or type(card["price"]) is not int or card["price"] <= 0:
            raise ValueError("duplicate or invalid card")
        cards[key] = card
    return cards

def compare(previous, current):
    old, new = index(previous), index(current)
    if previous["source"] != current["source"] or previous["game"] != current["game"] or previous["platform_claim"] != current["platform_claim"]:
        raise ValueError("incompatible sources")
    t0, t1 = timestamp(previous["updated_at"]), timestamp(current["updated_at"])
    if t1 <= t0:
        raise ValueError("snapshot time must advance")
    rows = []
    for key in sorted(old.keys() & new.keys()):
        before, after = old[key], new[key]
        if before["name"] != after["name"]:
            continue
        change = after["price"] - before["price"]
        rows.append({"group": key[0], "ea_id": key[1], "name": after["name"],
                     "previous_price": before["price"], "current_price": after["price"],
                     "change": change, "change_percent": round(100 * change / before["price"], 2),
                     "break_even_sell_price": (after["price"] * 100 + 94) // 95})
    rows.sort(key=lambda x: (x["change_percent"], x["name"]))
    return {"schema": "fut27-experimental-comparison-v1", "verified": False,
            "signals_enabled": False, "previous_updated_at": previous["updated_at"],
            "current_updated_at": current["updated_at"], "matched": len(rows),
            "price_drops": sum(x["change"] < 0 for x in rows), "rows": rows,
            "warning": "Unverified third-party observations; not EA listing prices or trading signals."}

def main():
    p = argparse.ArgumentParser()
    p.add_argument("previous")
    p.add_argument("current")
    p.add_argument("output")
    args = p.parse_args()
    result = compare(json.loads(Path(args.previous).read_text()), json.loads(Path(args.current).read_text()))
    Path(args.output).write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    print("Comparable cards:", result["matched"], "price drops:", result["price_drops"])
    print("Experimental comparison only; no trading signals")

if __name__ == "__main__":
    main()
