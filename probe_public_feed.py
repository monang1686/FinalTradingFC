"""One-time, non-persistent reachability check of publicly documented endpoints.

Does not invoke cron, bypass protections, collect card prices, or store data.
"""
import json
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError
from valtown_adapter import normalize_for_review

ENDPOINTS={
    "bowli-health":"https://fc27-market.val.run/debug",
    "bowli-latest":"https://fc27-market.val.run/latest",
}
def probe(url):
    req=Request(url,headers={"Accept":"application/json","User-Agent":"FUTTrader27-ConnectivityCheck/1.0"})
    try:
        with urlopen(req,timeout=8) as response:
            status=response.status
            mime=response.headers.get_content_type()
            raw=response.read(8_000_001)
            if len(raw)>8_000_000:
                return {"status":status,"result":"response_too_large"}
            if mime!="application/json":
                return {"status":status,"result":"not_json"}
            payload=json.loads(raw)
            diagnostics=normalize_for_review(payload) if url.endswith("/latest") else None
            return {"status":status,"result":"json_received",
                    "diagnostics":diagnostics,
                    "top_level_keys":sorted(payload.keys()) if isinstance(payload,dict) else [],
                    "has_updated":isinstance(payload,dict) and isinstance(payload.get("updated"),str)}
    except HTTPError as e:
        return {"status":e.code,"result":"http_error"}
    except (URLError,TimeoutError,ValueError,OSError) as e:
        return {"status":None,"result":type(e).__name__}

if __name__=="__main__":
    print(json.dumps({name:probe(url) for name,url in ENDPOINTS.items()},indent=2))
