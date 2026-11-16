"""Non-persistent, read-only diagnostic for the experimental FC27 feed.

Outputs structural metadata only: no player names, IDs, prices or raw response.
This script does not approve ingestion, storage or redistribution.
"""
import json
import sys
import urllib.error
import urllib.request
from collections import Counter
from datetime import datetime, timezone

URL = "https://fc27-market.val.run/latest"
MAX_BYTES = 4_000_000

def main():
    report = {"endpoint": URL, "checked_at": datetime.now(timezone.utc).isoformat(),
              "reachable": False, "json_valid": False, "data_reuse_authorized": False,
              "production_ingestion_enabled": False}
    try:
        req = urllib.request.Request(URL, headers={"User-Agent": "FUTTrader27-Diagnostic/1.0", "Accept": "application/json"})
        with urllib.request.urlopen(req, timeout=15) as response:
            report["http_status"] = response.status
            report["content_type"] = response.headers.get("Content-Type", "").split(";")[0]
            raw = response.read(MAX_BYTES + 1)
        report["reachable"] = True
        report["response_bytes"] = len(raw)
        if len(raw) > MAX_BYTES:
            raise ValueError("response exceeds diagnostic size limit")
        data = json.loads(raw)
        report["json_valid"] = True
        # Structural inspection only; never log raw card records or values.
        if isinstance(data, dict) and isinstance(data.get("groups"), (dict, list)):
            groups = data["groups"]
            report["groups_type"] = type(groups).__name__
            report["groups_count"] = len(groups)
            samples = list(groups.items())[:3] if isinstance(groups, dict) else [(str(i), v) for i, v in enumerate(groups[:3])]
            shapes = []
            for group_name, group_value in samples:
                entry = {"group_label": str(group_name)[:40], "type": type(group_value).__name__}
                if isinstance(group_value, dict):
                    entry["keys"] = sorted(str(k) for k in group_value.keys())[:30]
                    entry["list_sizes"] = {str(k): len(v) for k, v in group_value.items() if isinstance(v, list)}
                    for v in group_value.values():
                        if isinstance(v, list) and v and isinstance(v[0], dict):
                            entry["item_keys"] = sorted(str(k) for k in v[0].keys())[:35]
                            break
                elif isinstance(group_value, list):
                    entry["count"] = len(group_value)
                    if group_value and isinstance(group_value[0], dict):
                        entry["item_keys"] = sorted(str(k) for k in group_value[0].keys())[:35]
                shapes.append(entry)
            report["group_shapes"] = shapes
        report["root_type"] = type(data).__name__
        if isinstance(data, dict):
            report["root_keys"] = sorted(str(k) for k in data.keys())[:60]
            for k in ("updated", "updated_at", "timestamp", "platform", "game", "source"):
                v = data.get(k)
                if isinstance(v, (str, int, float)) and k not in ("source",):
                    report[k] = str(v)[:120]
            for k, v in data.items():
                if isinstance(v, list):
                    report.setdefault("array_lengths", {})[str(k)[:60]] = len(v)
                    if v and isinstance(v[0], dict):
                        report.setdefault("array_item_keys", {})[str(k)[:60]] = sorted(str(z) for z in v[0].keys())[:40]
        elif isinstance(data, list):
            report["array_length"] = len(data)
            if data and isinstance(data[0], dict):
                report["array_item_keys"] = sorted(str(k) for k in data[0].keys())[:40]
    except (urllib.error.URLError, TimeoutError, ValueError, json.JSONDecodeError) as exc:
        report["error_type"] = type(exc).__name__
        report["error"] = str(exc)[:180]
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0 if report["json_valid"] else 1

if __name__ == "__main__":
    sys.exit(main())
