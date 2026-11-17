"""Bounded, experimental snapshot history stored in GitHub Actions cache."""
import json
import sys
from pathlib import Path
import importlib.util

# Load the sibling experimental comparator explicitly: the repository also
# contains a different root-level module named valtown_compare.py.
_comparator_path = Path(__file__).resolve().with_name('valtown_compare.py')
_spec = importlib.util.spec_from_file_location('fut27_experimental_valtown_compare', _comparator_path)
_comparator = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_comparator)
compare, index, timestamp = _comparator.compare, _comparator.index, _comparator.timestamp

LIMIT = 336

def advance(history, snapshot):
    if not isinstance(history, dict) or history.get("schema") != "fut27-experimental-history-v1":
        raise ValueError("invalid history")
    index(snapshot)
    snapshots = history.get("snapshots")
    if not isinstance(snapshots, list):
        raise ValueError("invalid snapshots")
    if snapshots:
        latest = snapshots[-1]
        index(latest)
        if latest["source"] != snapshot["source"]:
            raise ValueError("source changed")
        old_time, new_time = timestamp(latest["updated_at"]), timestamp(snapshot["updated_at"])
        if new_time < old_time:
            raise ValueError("timestamp regression")
        if new_time == old_time:
            if latest != snapshot:
                raise ValueError("conflicting same-time snapshot")
            return history, None
    updated = (snapshots + [snapshot])[-LIMIT:]
    comparison = compare(updated[-2], updated[-1]) if len(updated) >= 2 else None
    return {"schema": "fut27-experimental-history-v1", "verified": False,
            "production_signals_enabled": False, "snapshots": updated}, comparison

def main():
    if len(sys.argv) != 4:
        raise SystemExit("Usage: valtown_history.py HISTORY.json SNAPSHOT.json COMPARISON.json")
    history_path, snapshot_path, comparison_path = map(Path, sys.argv[1:])
    if not snapshot_path.exists():
        print("No new snapshot; history unchanged")
        return
    history = json.loads(history_path.read_text()) if history_path.exists() else {
        "schema": "fut27-experimental-history-v1", "snapshots": []}
    new_history, comparison = advance(history, json.loads(snapshot_path.read_text()))
    history_path.parent.mkdir(parents=True, exist_ok=True)
    history_path.write_text(json.dumps(new_history, ensure_ascii=False) + "\n")
    if comparison:
        comparison_path.write_text(json.dumps(comparison, ensure_ascii=False, indent=2) + "\n")
        print("Comparison:", comparison["matched"], "cards,", comparison["price_drops"], "price drops")
    else:
        print("Waiting for second distinct source timestamp")
    print("Historical snapshots:", len(new_history["snapshots"]), "; experimental only")

if __name__ == "__main__":
    main()
