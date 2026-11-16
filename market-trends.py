#!/usr/bin/env python3
import argparse
import json
from pathlib import Path
from market_engine import report

if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('file', nargs='?', default='prices.json')
    args = p.parse_args()
    print(json.dumps(report(json.loads(Path(args.file).read_text())), ensure_ascii=False, indent=2))
