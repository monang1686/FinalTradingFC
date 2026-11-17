"""Safe FC27 multi-source feature readiness, with no unlicensed collection.

Providers contribute only independently licensed capabilities. A public URL or
a permissive client-library license is not proof of price-data reuse rights.
"""
CAPABILITIES={
    "val-town":{"price_preview":True,"history_preview":True,"card_metadata":True,
                "licensed_reuse":False,"per_card_timestamp":False,
                "platform_attested":False,"source_family":"bowli-fut-market"},
    "fut-db-free":{"price_preview":False,"history_preview":False,"card_metadata":True,
                   "licensed_reuse":True,"requires_api_key":True,
                   "source_family":"fut-db"},
    "datafluxor-sandbox":{"price_preview":False,"history_preview":False,"card_metadata":True,
                          "licensed_reuse":True,"sandbox_only":True,
                          "source_family":"datafluxor"},
}
def readiness(providers=CAPABILITIES):
    candidates=[]
    for name,features in providers.items():
        candidates.append({"provider":name,"capabilities":features,
                           "usable_for_live_signals":bool(features.get("licensed_reuse") and
                               features.get("price_preview") and features.get("per_card_timestamp") and
                               features.get("platform_attested"))})
    return {"providers":candidates,"live_signals_enabled":False,
            "free_live_price_source_verified":False,
            "note":"Val Town retained as disabled preview; no automatic polling."}

if __name__=="__main__":
    import json
    print(json.dumps(readiness(),indent=2))
