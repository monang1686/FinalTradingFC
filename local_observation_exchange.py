"""Portable local observation exchange contract for Safari and desktop browsers.

No EA credentials, cookies, requests, session capture, automation or scraping.
User-initiated export/import only. Never generates production signals.
"""
from datetime import datetime,timezone
from urllib.parse import urlsplit

def validate_bundle(payload, *, now=None):
    now=now or datetime.now(timezone.utc)
    if not isinstance(payload,dict) or payload.get("format")!="fut-trader-27-observations-v1":
        raise ValueError("unknown observation bundle")
    if payload.get("data_kind")!="manual_unverified" or payload.get("production_signals")!=[]:
        raise ValueError("manual unverified observations only")
    records=payload.get("records")
    if not isinstance(records,list) or len(records)>500:
        raise ValueError("invalid observation count")
    result=[]
    for r in records:
        if not isinstance(r,dict): raise ValueError("invalid observation")
        ident=r.get("id")
        if not isinstance(ident,str) or not ident.isascii() or not ident.isdigit() or str(int(ident))!=ident or int(ident)<=0:
            raise ValueError("exact EA card version ID required")
        if not isinstance(r.get("name"),str) or not 0<len(r["name"].strip())<=80:
            raise ValueError("invalid name")
        if r.get("strategy") not in ("fluctuation","fodder","sniping"):
            raise ValueError("invalid strategy")
        for field in ("buy","target"):
            if type(r.get(field)) is not int or not 0<r[field]<=15000000:
                raise ValueError("invalid price")
        if type(r.get("history")) is not int or not 0<=r["history"]<=10000:
            raise ValueError("invalid history")
        source=r.get("source")
        if not isinstance(source,str) or urlsplit(source).scheme!="https" or not urlsplit(source).netloc or "@" in urlsplit(source).netloc:
            raise ValueError("https source without credentials required")
        raw=r.get("observed")
        if not isinstance(raw,str): raise ValueError("timestamp required")
        try: at=datetime.fromisoformat(raw.replace("Z","+00:00"))
        except ValueError: raise ValueError("invalid timestamp") from None
        if at.tzinfo is None or at>now: raise ValueError("future or naive timestamp")
        result.append({k:r[k] for k in ("id","name","strategy","buy","target","history","source","observed")})
    return {"format":"fut-trader-27-observations-v1","data_kind":"manual_unverified",
            "records":result,"production_signals":[],"actionable":False}
