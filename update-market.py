#!/usr/bin/env python3
"""Market Trends 2.0: writes only isolated experimental state."""
import json
from pathlib import Path
from market_engine import atomic
from market_pipeline import run

if __name__=='__main__':
    config=json.loads(Path('config/market-sources.json').read_text())
    target=Path('experimental/market-state.json')
    previous=json.loads(target.read_text()) if target.exists() else None
    state=run(config,previous)
    atomic(target,state)
    print(state['status']+': '+str(state['fresh_unique_cards'])+' fresh cards; public prices.json unchanged')
