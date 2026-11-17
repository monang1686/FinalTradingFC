"""Manual, one-page FUT-DB connection check. Never log the API token."""
import os
import json
from futdb_connector import request_page

def main():
    if not os.environ.get("FUTDB_API_KEY"):
        print(json.dumps({"status":"secret_missing"}))
        return 2
    try:
        page=request_page("players",page=1)
    except PermissionError:
        print(json.dumps({"status":"access_denied"}))
        return 3
    except Exception as error:
        print(json.dumps({"status":"request_failed","error_type":type(error).__name__}))
        return 4
    items=page["items"]
    keys=("id","resourceId","baseId","playerId")
    print(json.dumps({"status":"connected","count":len(items),
                      "id_fields":[k for k in keys if items and k in items[0]]}))
    return 0

if __name__=="__main__":
    raise SystemExit(main())
