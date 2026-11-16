#!/usr/bin/env python3
"""Disabled until a source-specific authorized adapter is reviewed and implemented."""
import json
from pathlib import Path
from market_engine import atomic, report

if __name__ == '__main__':
    config = json.loads(Path('config/market-source.json').read_text())
    # A boolean configuration change must never silently activate an unverified endpoint.
    if config.get('enabled'):
        raise SystemExit('BLOCKED: no verified production adapter implemented; see docs/market-trends.md')
    data = json.loads(Path('prices.json').read_text())
    atomic('data/market-trends.json', report(data))
    print('BLOCKED: no verified source; prices.json and history unchanged')
