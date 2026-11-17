"""Offline import of a user-provided FC27 console CSV price export.

No network, scraping, API calls or implicit reuse rights. Exact EA item IDs only.
Rows are observations, never executable trade signals.
"""
import csv
import io
from datetime import datetime, timezone

ID_KEYS=("ea_item_id","ea_id","resource_id","resourceid")
PRICE_KEYS=("console_price","price_console","ps_price","console")
TIME_KEYS=("observed_at","price_updated_at","updated_at","timestamp")
def _field(row, keys):
    normalized={k.strip().lower().replace(" ","_"):v for k,v in row.items() if isinstance(k,str)}
    for key in keys:
        if key in normalized and normalized[key] not in (None,""):
            return normalized[key]
    return None

def import_console_csv(content, *, source_url, permission_confirmed=False):
    if permission_confirmed is not True:
        raise PermissionError("Confirm the export's reuse terms before importing")
    if not isinstance(source_url,str) or not source_url.startswith("https://"):
        raise ValueError("HTTPS provenance required")
    if not isinstance(content,str) or len(content)>5_000_000:
        raise ValueError("CSV must be UTF-8 text, max 5 MB")
    reader=csv.DictReader(io.StringIO(content))
    if not reader.fieldnames:
        raise ValueError("CSV header required")
    quotes=[]
    seen=set()
    for row in reader:
        if len(quotes)>=30000:
            raise ValueError("too many rows")
        raw_id=_field(row,ID_KEYS)
        if not isinstance(raw_id,str) or not raw_id.isascii() or not raw_id.isdigit() or int(raw_id)<=0 or str(int(raw_id))!=raw_id:
            raise ValueError("exact EA item ID required")
        if raw_id in seen:
            raise ValueError("duplicate EA card-version ID")
        seen.add(raw_id)
        raw_price=_field(row,PRICE_KEYS)
        if not isinstance(raw_price,str) or not raw_price.isascii() or not raw_price.isdigit() or not 1<=int(raw_price)<=15000000:
            raise ValueError("valid console price in credits required")
        observed=_field(row,TIME_KEYS)
        if not observed:
            raise ValueError("source observation timestamp required")
        try:
            at=datetime.fromisoformat(observed.replace("Z","+00:00"))
            if at.tzinfo is None or at>datetime.now(timezone.utc):
                raise ValueError("timestamp must be timezone-aware and not future")
        except (TypeError,ValueError) as error:
            raise ValueError("invalid observation timestamp") from None
        quotes.append({"id":raw_id,"price":int(raw_price),"observed_at":at.isoformat(),
                       "source_url":source_url,"platform":"console","actionable":False})
    return {"game":"EA Sports FC 27","data_kind":"observed_unverified",
            "authorized":False,"production_signals":[],"quotes":quotes,
            "source_url":source_url,"count":len(quotes)}
