"""Fail-closed readiness checks for candidate FC27 price feeds.

No network activity. A public website, advertised update cadence or source
client's open-source license never implies permission to republish its prices.
"""
from datetime import datetime, timezone

def evaluate_feed(candidate, *, now=None, max_age_seconds=5400):
    now=now or datetime.now(timezone.utc)
    if not isinstance(candidate,dict):
        raise ValueError("candidate must be a mapping")
    required=("exact_ea_card_id","console_market","per_card_observed_at",
              "documented_reuse_permission","sample_schema_verified")
    checks={key:candidate.get(key) is True for key in required}
    observed=candidate.get("sample_observed_at")
    age=None
    if isinstance(observed,str):
        try:
            timestamp=datetime.fromisoformat(observed.replace("Z","+00:00"))
            if timestamp.tzinfo is not None:
                age=int((now-timestamp).total_seconds())
        except ValueError:
            pass
    checks["sample_fresh"]=age is not None and 0<=age<=max_age_seconds
    checks["no_auth_bypass"]=candidate.get("requires_bypass") is not True
    return {"source_id":candidate.get("source_id","unknown"),
            "checks":checks,"age_seconds":age,
            "ready_for_live_quotes":all(checks.values()),
            "automatic_polling_enabled":False,
            "production_signals_enabled":False}

CANDIDATES={
    "nokafut": {"source_id":"nokafut","exact_ea_card_id":False,
                "console_market":True,"per_card_observed_at":False,
                "documented_reuse_permission":False,"sample_schema_verified":False},
    "ezzcoins": {"source_id":"ezzcoins","exact_ea_card_id":True,
                 "console_market":True,"per_card_observed_at":False,
                 "documented_reuse_permission":False,"sample_schema_verified":False},
    "val-town-bowli": {"source_id":"val-town-bowli","exact_ea_card_id":True,
                       "console_market":True,"per_card_observed_at":False,
                       "documented_reuse_permission":False,"sample_schema_verified":False},
}

def candidate_report():
    return {"candidates":[evaluate_feed(c) for c in CANDIDATES.values()],
            "live_collection_enabled":False}

if __name__=="__main__":
    import json
    print(json.dumps(candidate_report(),indent=2))
