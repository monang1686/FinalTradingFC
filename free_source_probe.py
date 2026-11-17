"""One-shot diagnostic for public FC27 price sources.

Run manually: python free_source_probe.py
No login, fingerprint spoofing, Cloudflare bypass, retries, proxies or scraping loops.
Never publishes or stores source content. A 200 status is not reuse permission.
"""
import json
from datetime import datetime, timezone
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

SOURCES = (
    ("futbin_fc27_player_page", "https://www.futbin.com/27/player/8/player"),
    ("ezzcoins_lowest_price_page", "https://ezzcoins.com/lowest-prices"),
    ("valtown_market_api", "https://tyler82800-fut-market-api.web.val.run/latest"),
)

def probe(name, url):
    result = {"source": name, "url": url, "checked_at": datetime.now(timezone.utc).isoformat(),
              "http_status": None, "content_type": None, "error": None,
              "data_verified": False, "reuse_authorized": False}
    try:
        req = Request(url, headers={"User-Agent": "FUTTrader27-SourceEvaluation/0.1"})
        with urlopen(req, timeout=12) as response:
            result["http_status"] = response.status
            result["content_type"] = response.headers.get("Content-Type", "")
            # Do not download or republish third-party content in this diagnostic.
    except HTTPError as exc:
        result["http_status"] = exc.code
        result["error"] = "HTTP error"
    except (URLError, TimeoutError, OSError) as exc:
        result["error"] = type(exc).__name__
    return result

if __name__ == "__main__":
    print(json.dumps({"results": [probe(name, url) for name, url in SOURCES],
                      "note": "HTTP reachability does not verify prices, schema, freshness or reuse rights."}, indent=2))
