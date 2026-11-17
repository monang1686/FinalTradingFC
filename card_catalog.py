"""Fail-closed FC27 card metadata join by exact EA card-version ID.

Accepts only explicitly licensed/approved metadata snapshots supplied by caller.
Does not fetch FUT-DB, guess base-card IDs, or alter price provenance.
"""
from datetime import datetime, timezone
from market_engine import stamp

FIELDS=("name","rating","position","club","league","nation","rarity","image_url")
def card_id(value):
    if type(value) is int:
        return str(value) if value>0 else None
    if isinstance(value,str) and value.isascii() and value.isdigit() and value==str(int(value)) and int(value)>0:
        return value
    return None

def build_catalog(records, *, provenance, authorized=False):
    if authorized is not True or not isinstance(provenance,str) or not provenance.strip():
        raise ValueError("metadata reuse must be explicitly authorized with provenance")
    if not isinstance(records,list):
        raise ValueError("metadata records must be an array")
    catalog={}
    for record in records:
        if not isinstance(record,dict):
            raise ValueError("invalid metadata record")
        key=card_id(record.get("ea_id"))
        if not key or key in catalog:
            raise ValueError("invalid or duplicate EA card-version id")
        entry={}
        for field in FIELDS:
            value=record.get(field)
            if value is None:
                continue
            if field=="rating":
                if type(value) is not int or not 1<=value<=99:
                    raise ValueError("invalid rating")
            elif not isinstance(value,str) or not value.strip():
                raise ValueError("invalid metadata field "+field)
            entry[field]=value
        catalog[key]=entry
    return {"provenance":provenance,"authorized":True,"cards":catalog}

def enrich_market(snapshot,catalog):
    if catalog.get("authorized") is not True:
        raise ValueError("metadata catalog not authorized")
    players=snapshot.get("players")
    if not isinstance(players,list):
        raise ValueError("market players must be an array")
    result=[]
    for card in players:
        if not isinstance(card,dict):
            raise ValueError("invalid market card")
        key=card_id(card.get("id"))
        row=dict(card)
        metadata=catalog["cards"].get(key) if key else None
        row["metadata"]=dict(metadata) if metadata else None
        row["metadata_source"]=catalog["provenance"] if metadata else None
        row["metadata_match"]="exact_ea_card_version" if metadata else "unmatched"
        result.append(row)
    output=dict(snapshot)
    output["players"]=result
    output["metadata_coverage"]={"matched":sum(r["metadata"] is not None for r in result),
                                  "total":len(result)}
    # Never change source authorization, quote timestamp, or trade signals.
    return output
