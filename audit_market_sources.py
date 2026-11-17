"""Offline provider verification gate: report only, never fetch external sites.

Network probes should be conducted separately, after confirming provider
permission. This script does not enable any provider.
"""
import json
from pathlib import Path
from market_sources import authorize, SourceBlocked

def audit(config_path="config/market-sources.json"):
    sources=json.loads(Path(config_path).read_text(encoding="utf-8"))["sources"]
    report=[]
    for s in sources:
        missing=[k for k in ("permission_url","verified_at","data_license","license_url") if not s.get(k)]
        reason=""
        try:
            authorize(s)
            status="approved_for_connector_review"
        except (SourceBlocked,ValueError,TypeError,KeyError) as exc:
            status="blocked"
            reason=str(exc)
        report.append({"id":s["id"],"endpoint":s["endpoint"],"status":status,
                       "missing_evidence":missing,
                       "block_reason":s.get("block_reason",reason if status=="blocked" else ""),
                       "automated_requests_started":False})
    return {"providers":report,"live_feed_enabled":False,
            "note":"No endpoint tested; config-only authorization audit."}

if __name__=="__main__":
    print(json.dumps(audit(),indent=2,ensure_ascii=False))
