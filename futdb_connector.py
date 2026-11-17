"""FUT-DB free metadata connector for FC27. No prices or premium endpoints.

Requires FUTDB_API_KEY environment variable. No network requests at import.
Only explicit calls fetch; never commit API credentials or fetched content.
"""
import json
import os
from urllib.request import Request, urlopen
from urllib.error import HTTPError
from card_catalog import build_catalog, enrich_market

BASE="https://api.fut-db.com"
PROVENANCE="https://api.fut-db.com/api/doc/index.html"
FREE_PATHS={"players","clubs","leagues","nations","rarities"}

def request_page(kind, page=1, *, key=None, transport=None):
    if kind not in FREE_PATHS or type(page) is not int or page<1 or page>1000:
        raise ValueError("unsupported free metadata endpoint or page")
    key=key if key is not None else os.environ.get("FUTDB_API_KEY")
    if not isinstance(key,str) or not key.strip():
        raise ValueError("FUTDB_API_KEY missing; obtain a free key from FUT-DB")
    url=f"{BASE}/api/{kind}?page={page}"
    if transport is None:
        def transport(url, headers):
            with urlopen(Request(url,headers=headers),timeout=15) as response:
                if response.status!=200 or response.headers.get_content_type()!="application/json":
                    raise ValueError("unexpected FUT-DB response")
                data=response.read(4_000_001)
                if len(data)>4_000_000:
                    raise ValueError("FUT-DB response too large")
                return json.loads(data)
    try:
        payload=transport(url,{"Accept":"application/json","X-AUTH-TOKEN":key})
    except HTTPError as exc:
        if exc.code in (401,403):
            raise PermissionError("FUT-DB key rejected or free tier not entitled") from None
        if exc.code==429:
            raise RuntimeError("FUT-DB request limit reached") from None
        raise
    if not isinstance(payload,dict) or not isinstance(payload.get("items"),list):
        raise ValueError("unexpected FUT-DB items schema")
    pagination=payload.get("pagination")
    if not isinstance(pagination,dict) or type(pagination.get("pageTotal")) is not int:
        raise ValueError("FUT-DB pagination missing")
    if not 1<=pagination["pageTotal"]<=1000:
        raise ValueError("invalid FUT-DB page count")
    return payload

def normalize_players(payload):
    if not isinstance(payload,dict) or not isinstance(payload.get("items"),list):
        raise ValueError("invalid FUT-DB player page")
    records=[]
    for p in payload["items"]:
        if not isinstance(p,dict) or type(p.get("id")) is not int or p["id"]<=0:
            raise ValueError("invalid FUT-DB card-version ID")
        # Only map when FUT-DB id and EA resourceId explicitly agree.\n        # Different IDs require a reviewed mapping; never guess or join by base ID.\n        if type(p.get("resourceId")) is not int or p["resourceId"]!=p["id"]:\n            continue
        name=p.get("commonName") or p.get("name")
        if not name:
            parts=[p.get("firstName"),p.get("lastName")]
            name=" ".join(x for x in parts if isinstance(x,str) and x.strip())
        item={"ea_id":p["id"]}
        if isinstance(name,str) and name.strip(): item["name"]=name.strip()
        if type(p.get("rating")) is int: item["rating"]=p["rating"]
        if isinstance(p.get("position"),str) and p["position"].strip(): item["position"]=p["position"]
        for field in ("club","league","nation","rarity"):
            v=p.get(field)
            if type(v) is int and v>0:
                item[field]=str(v)  # references resolved by other free endpoints
        records.append(item)
    return records

def catalog_from_pages(pages, *, approved_for_reuse=False):
    """Approval must reflect provider terms for the intended use, not a guessed flag."""
    if not approved_for_reuse:
        raise PermissionError("Confirm metadata reuse terms before persistence/enrichment")
    records=[]
    for page in pages:
        records.extend(normalize_players(page))
    return build_catalog(records,provenance=PROVENANCE,authorized=True)

def enrich_with_futdb(snapshot,pages,*,approved_for_reuse=False):
    return enrich_market(snapshot,catalog_from_pages(pages,approved_for_reuse=approved_for_reuse))
