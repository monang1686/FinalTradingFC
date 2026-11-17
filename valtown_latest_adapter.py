"""Offline adapter for the documented Val Town /latest JSON shape.

Does not fetch endpoints, schedule jobs, grant reuse rights or emit signals.
All prices are unverified observations; forecast and provider signals ignored.
"""
from datetime import datetime,timezone

GROUPS=("icons","heroes","bronze","silver","gold","special")

def parse_latest(payload, *, now=None, max_age_seconds=5400):
    now=now or datetime.now(timezone.utc)
    if not isinstance(payload,dict) or not isinstance(payload.get("groups"),dict):
        raise ValueError("latest JSON must contain groups")
    if not isinstance(payload.get("updated"),str):
        raise ValueError("source updated timestamp required")
    try:
        at=datetime.fromisoformat(payload["updated"].replace("Z","+00:00"))
    except ValueError:
        raise ValueError("invalid updated timestamp") from None
    if at.tzinfo is None or now.tzinfo is None or at>now:
        raise ValueError("timezone-aware non-future timestamp required")
    age=int((now-at).total_seconds())
    groups=payload["groups"]
    if set(groups)!=set(GROUPS):
        raise ValueError("unexpected or missing groups")
    rows=[]
    seen=set()
    for group in GROUPS:
        cards=groups[group]
        if not isinstance(cards,list) or len(cards)>100:
            raise ValueError("invalid group length")
        for card in cards:
            if not isinstance(card,dict):
                raise ValueError("invalid card")
            ident=card.get("eaId")
            price=card.get("price")
            if type(ident) is not int or ident<=0 or type(price) is not int or not 1<=price<=15000000:
                raise ValueError("exact EA item ID and console price required")
            if ident in seen:
                raise ValueError("duplicate EA card-version ID")
            seen.add(ident)
            rows.append({"id":str(ident),"name":card.get("name") if isinstance(card.get("name"),str) else None,
                         "rating":card.get("rating") if type(card.get("rating")) is int and 1<=card["rating"]<=99 else None,
                         "group":group,"price":price,"platform":"playstation_claimed",
                         "feed_updated_at":at.isoformat(),"per_card_observed_at":None,"age_seconds":age,
                         "stale":age>max_age_seconds,"actionable":False,"price_verified":False})
    return {"source_id":"val-town-bowli","data_kind":"unverified_price_preview",
            "authorized":False,"source_updated":at.isoformat(),"age_seconds":age,
            "stale":age>max_age_seconds,"rows":rows,"count":len(rows),
            "per_card_timestamp_verified":False,"price_reuse_permission_verified":False,
            "production_signals":[],"automatic_polling_enabled":False}
