"""Parse a user-authorized DataFluxor FUT price API response, offline only.

No HTTP calls, credentials, polling or paid subscription. A sandbox example is
not a real quote. All imported prices are non-actionable observations.
"""
from datetime import datetime,timezone

def parse_prices(payload, *, now=None, max_age_seconds=5400):
    now=now or datetime.now(timezone.utc)
    if not isinstance(payload,dict) or payload.get("success") is not True:
        raise ValueError("successful API envelope required")
    data=payload.get("data")
    if not isinstance(data,dict) or not isinstance(data.get("items"),list):
        raise ValueError("items array required")
    if len(data["items"])>500:
        raise ValueError("maximum 500 items per response")
    quotes=[]
    seen=set()
    for item in data["items"]:
        if not isinstance(item,dict) or item.get("game")!="fc27":
            raise ValueError("FC27 item required")
        ident=item.get("ea_id")
        if type(ident) is not int or ident<=0 or ident in seen:
            raise ValueError("unique exact EA item ID required")
        seen.add(ident)
        if item.get("platform") not in ("ps","xbox") or item.get("market")!="console":
            raise ValueError("console market required")
        amount=item.get("price")
        if type(amount) is not int or not 1<=amount<=15000000:
            raise ValueError("valid positive buy-now price required")
        raw_time=item.get("observed_at")
        if not isinstance(raw_time,str):
            raise ValueError("per-card observation timestamp required")
        try:
            at=datetime.fromisoformat(raw_time.replace("Z","+00:00"))
        except ValueError:
            raise ValueError("invalid observation timestamp") from None
        if at.tzinfo is None or now.tzinfo is None or at>now:
            raise ValueError("timezone-aware non-future observation required")
        age=int((now-at).total_seconds())
        quotes.append({"id":str(ident),"price":amount,"observed_at":at.isoformat(),
                       "age_seconds":age,"stale":age>max_age_seconds,
                       "platform":"console","exact":item.get("exact") is True,
                       "source":"datafluxor","actionable":False})
    return {"source_id":"datafluxor","data_kind":"observed_unverified",
            "quotes":quotes,"count":len(quotes),"production_signals":[],
            "automatic_polling_enabled":False}
