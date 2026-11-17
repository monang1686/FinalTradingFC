"""One-page FUT-DB diagnostic; manually invoked only. No secrets or response bodies logged."""
import json
import os
from urllib.error import HTTPError, URLError
from futdb_connector import request_page

def classify_error(error):
    if isinstance(error, PermissionError):
        return "authentication_or_entitlement_denied"
    if isinstance(error, HTTPError):
        if error.code == 429:
            return "rate_limited"
        if error.code in (401, 403):
            return "authentication_or_entitlement_denied"
        if error.code == 404:
            return "endpoint_not_found"
        if error.code >= 500:
            return "provider_server_error"
        return "http_error"
    if isinstance(error, RuntimeError) and str(error) == "FUT-DB request limit reached":
        return "rate_limited"
    if isinstance(error, URLError):
        return "network_error"
    if isinstance(error, (ValueError, KeyError, TypeError, json.JSONDecodeError)):
        return "response_schema_error"
    return "unexpected_error"

def main():
    if not os.environ.get("FUTDB_API_KEY"):
        print(json.dumps({"status": "secret_missing"}))
        return 2
    try:
        page = request_page("players", page=1)
    except Exception as error:
        print(json.dumps({"status": classify_error(error)}))
        return 3
    items = page["items"]
    keys = ("id", "resourceId", "baseId", "playerId")
    print(json.dumps({"status": "connected", "count": len(items),
                      "id_fields": [k for k in keys if items and k in items[0]]}))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
