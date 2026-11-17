"""Combine independently authorized card metadata catalogs without guessing IDs.

A conflicting field is withheld rather than selecting an arbitrary source.
Prices and trading permissions are never created or modified.
"""
from card_catalog import card_id, FIELDS

def merge_catalogs(catalogs):
    if not isinstance(catalogs,list) or not catalogs:
        raise ValueError("at least one metadata catalog required")
    merged={}
    origins={}
    conflicts={}
    seen_sources=set()
    for catalog in catalogs:
        if not isinstance(catalog,dict) or catalog.get("authorized") is not True:
            raise PermissionError("every catalog must be authorized")
        source=catalog.get("provenance")
        if not isinstance(source,str) or not source.strip() or source in seen_sources:
            raise ValueError("unique metadata provenance required")
        seen_sources.add(source)
        cards=catalog.get("cards")
        if not isinstance(cards,dict):
            raise ValueError("invalid catalog")
        for raw_id, record in cards.items():
            key=card_id(raw_id)
            if not key or not isinstance(record,dict):
                raise ValueError("invalid EA card-version entry")
            fields=merged.setdefault(key,{})
            field_sources=origins.setdefault(key,{})
            for field,value in record.items():
                if field not in FIELDS:
                    continue
                if field in conflicts.get(key,{}):
                    continue
                if field not in fields:
                    fields[field]=value
                    field_sources[field]=[source]
                elif fields[field]==value:
                    field_sources[field].append(source)
                else:
                    conflicts.setdefault(key,{})[field]=sorted(set(field_sources[field]+[source]))
                    del fields[field]
                    del field_sources[field]
    return {"authorized":True,"provenance":"multi-source-authorized-metadata",
            "cards":merged,"field_sources":origins,"conflicts":conflicts,
            "sources":sorted(seen_sources)}

def enrich_rows(snapshot, merged):
    if merged.get("authorized") is not True:
        raise PermissionError("metadata not authorized")
    rows=snapshot.get("rows")
    if not isinstance(rows,list):
        raise ValueError("snapshot rows required")
    result=[]
    matched=0
    for original in rows:
        if not isinstance(original,dict):
            raise ValueError("invalid market row")
        row=dict(original)
        key=card_id(row.get("id"))
        metadata=merged["cards"].get(key) if key else None
        if metadata:
            matched+=1
        row["metadata"]=dict(metadata) if metadata else None
        row["metadata_field_sources"]={k:list(v) for k,v in merged["field_sources"].get(key,{}).items()} if metadata else {}
        row["metadata_conflicts"]=dict(merged["conflicts"].get(key,{})) if key else {}
        result.append(row)
    out=dict(snapshot)
    out["rows"]=result
    out["metadata_coverage"]={"matched":matched,"total":len(result)}
    return out
