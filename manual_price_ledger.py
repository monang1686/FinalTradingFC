"""Offline FC27 console quote ledger for manually observed public prices.

Never scrapes, invents missing observations or emits trading signals.
Only explicit timestamped quotes with exact card-version IDs are accepted.
"""
from datetime import datetime, timezone
from urllib.parse import urlparse

def _parse_time(value):
    if not isinstance(value,str):
        raise ValueError("observation time required")
    try:
        dt=datetime.fromisoformat(value.replace("Z","+00:00"))
    except ValueError:
        raise ValueError("invalid observation time") from None
    if dt.tzinfo is None or dt>datetime.now(timezone.utc):
        raise ValueError("timezone-aware past observation required")
    return dt

def validate_observation(record):
    if not isinstance(record,dict):
        raise ValueError("observation object required")
    item_id=record.get("ea_item_id")
    if not isinstance(item_id,str) or not item_id.isascii() or not item_id.isdigit() or str(int(item_id))!=item_id or int(item_id)<=0:
        raise ValueError("exact EA card-version ID required")
    price=record.get("console_price")
    if type(price) is not int or not 1<=price<=15000000:
        raise ValueError("console price must be integer credits")
    url=record.get("source_url")
    parsed=urlparse(url) if isinstance(url,str) else None
    if not parsed or parsed.scheme!="https" or not parsed.hostname or parsed.username or parsed.password:
        raise ValueError("valid HTTPS source URL required")
    at=_parse_time(record.get("observed_at"))
    return {"id":item_id,"price":price,"observed_at":at.isoformat(),
            "source_url":url,"platform":"console","actionable":False}

def summarize_observations(records, *, now=None, max_age_seconds=5400):
    if not isinstance(records,list) or len(records)>30000:
        raise ValueError("invalid observation list")
    now=now or datetime.now(timezone.utc)
    if now.tzinfo is None:
        raise ValueError("aware clock required")
    grouped={}
    seen=set()
    for raw in records:
        quote=validate_observation(raw)
        dt=_parse_time(quote["observed_at"])
        if dt>now:
            raise ValueError("observation later than evaluation time")
        unique=(quote["id"],quote["source_url"],quote["observed_at"])
        if unique in seen:
            raise ValueError("duplicate source observation")
        seen.add(unique)
        grouped.setdefault(quote["id"],[]).append(quote)
    cards=[]
    for item_id,quotes in sorted(grouped.items()):
        quotes.sort(key=lambda q:q["observed_at"])
        latest=quotes[-1]
        age=int((now-_parse_time(latest["observed_at"])).total_seconds())
        cards.append({"id":item_id,"latest_quote":latest,"observations":len(quotes),
                      "age_seconds":age,"stale":age>max_age_seconds,
                      "actionable":False,"trend_percent":None})
    return {"data_kind":"observed_unverified","authorized":False,
            "production_signals":[],"cards":cards,"total_observations":len(records)}
