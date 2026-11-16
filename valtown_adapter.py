"""Val Town FC27 schema adapter for offline, non-persistent diagnostics.

This module NEVER fetches the endpoint, authorizes reuse, writes files, or
promotes feed data into production signals. It requires an explicit market
attestation because the feed itself has no per-card platform/tradeability fields.
"""
from datetime import datetime, timezone

GROUPS = ("icons", "heroes", "bronze", "silver", "gold", "special")

def inspect(payload, now=None):
    now = now or datetime.now(timezone.utc)
    if not isinstance(payload, dict) or not isinstance(payload.get("groups"), dict):
        raise ValueError("expected groups object")
    from market_engine import stamp
    updated = stamp(payload.get("updated"))
    if updated > now:
        raise ValueError("future feed timestamp")
    groups = payload["groups"]
    if set(groups) - set(GROUPS):
        raise ValueError("unexpected group")
    report = {"schema": "valtown-fc27-v1", "updated": updated.isoformat(),
              "age_minutes": round((now - updated).total_seconds() / 60, 1),
              "counts": {}, "cards": 0, "valid_prices": 0,
              "invalid_prices": 0, "missing_ids": 0, "duplicate_pairs": 0,
              "per_card_timestamps": 0, "unique_ea_ids": 0, "duplicate_ea_ids": 0,
              "invalid_ea_ids": 0, "freshness_verified": False, "platform_attested": False,
              "tradeability_attested": False, "authorized_for_reuse": False,
              "can_generate_buy_signals": False}
    seen = set()
    ea_ids = set()
    for group, cards in groups.items():
        if not isinstance(cards, list):
            raise ValueError("group is not an array")
        report["counts"][group] = len(cards)
        for card in cards:
            if not isinstance(card, dict):
                raise ValueError("card is not an object")
            report["cards"] += 1
            value = card.get("price")
            if type(value) is int and 0 < value <= 15000000:
                report["valid_prices"] += 1
            else:
                report["invalid_prices"] += 1
            ea_id, rarity_id = card.get("eaId"), card.get("rarityId")
            canonical = str(ea_id)
            if type(ea_id) not in (int, str) or not canonical.isascii() or not canonical.isdigit() or int(canonical)<=0 or canonical!=str(int(canonical)):
                report["invalid_ea_ids"] += 1
            elif canonical in ea_ids:
                report["duplicate_ea_ids"] += 1
            else:
                ea_ids.add(canonical)
            if ea_id is None or rarity_id is None:
                report["missing_ids"] += 1
            else:
                pair = (str(ea_id), str(rarity_id))
                if pair in seen:
                    report["duplicate_pairs"] += 1
                seen.add(pair)
            if any(card.get(k) is not None for k in ("timestamp", "updated_at", "observed_at", "lastUpdated")):
                report["per_card_timestamps"] += 1
    report["unique_ea_ids"] = len(ea_ids)
    return report

def normalize_for_review(payload, now=None):
    """Return only a metadata-only quality report, not price records."""
    return inspect(payload, now)
