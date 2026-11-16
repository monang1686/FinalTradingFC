#!/usr/bin/env python3
"""FUT Trader 27: cautious snapshot collector for a publicly documented JSON endpoint.

No scraping, trading, price predictions or Telegram alerts. Do not schedule
without verifying the endpoint operator's permission for automated reuse.
This source's platform is UNVERIFIED: output is deliberately NOT prices.json.
"""
import argparse
import json
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path
from urllib.request import Request, urlopen

URL = 'https://fc27-market.val.run/latest'
MAX_BYTES = 8_000_000

def parse_stamp(s):
    if not isinstance(s, str):
        raise ValueError('missing updated timestamp')
    d = datetime.fromisoformat(s.replace('Z', '+00:00'))
    if d.tzinfo is None:
        raise ValueError('updated timestamp has no timezone')
    d = d.astimezone(timezone.utc)
    if d > datetime.now(timezone.utc) + timedelta(minutes=5):
        raise ValueError('future updated timestamp')
    return d

def normalize(payload):
    if not isinstance(payload, dict) or not isinstance(payload.get('groups'), dict):
        raise ValueError('unexpected JSON schema')
    stamp = parse_stamp(payload.get('updated'))
    observations = []
    seen = set()
    for category, cards in payload['groups'].items():
        if not isinstance(category, str) or not isinstance(cards, list):
            raise ValueError('invalid group')
        for card in cards:
            if not isinstance(card, dict):
                continue
            ea_id, price, name = card.get('eaId'), card.get('price'), card.get('name')
            if isinstance(ea_id, bool) or not isinstance(ea_id, (int, str)) or not str(ea_id).isdigit():
                continue
            if isinstance(price, bool) or not isinstance(price, int) or price <= 0:
                continue
            if not isinstance(name, str) or not name.strip():
                continue
            key = str(ea_id)
            if key in seen:
                continue
            seen.add(key)
            observations.append({'id': key, 'name': name.strip(), 'category': category,
                                 'price': price, 'timestamp': stamp.isoformat().replace('+00:00','Z')})
    if not observations:
        raise ValueError('no valid observations')
    return {'source': URL, 'source_updated_at': stamp.isoformat().replace('+00:00','Z'),
            'platform': 'unverified', 'status': 'research_only_no_trading_alerts',
            'observations': observations}

def fetch():
    req = Request(URL, headers={'Accept': 'application/json', 'User-Agent': 'FUTTrader27-Research/0.1'})
    with urlopen(req, timeout=15) as response:
        if response.status != 200:
            raise ValueError('HTTP status not 200')
        raw = response.read(MAX_BYTES + 1)
        if len(raw) > MAX_BYTES:
            raise ValueError('response too large')
    return json.loads(raw)

def main():
    p = argparse.ArgumentParser()
    p.add_argument('--input', type=Path, help='Offline JSON fixture; no network call')
    p.add_argument('--output', type=Path, default=Path('fc27-market-snapshot.json'))
    p.add_argument('--max-age-minutes', type=int, default=120)
    args = p.parse_args()
    if args.max_age_minutes < 1:
        p.error('--max-age-minutes must be positive')
    payload = json.loads(args.input.read_text(encoding='utf-8')) if args.input else fetch()
    result = normalize(payload)
    age = datetime.now(timezone.utc) - parse_stamp(result['source_updated_at'])
    if age > timedelta(minutes=args.max_age_minutes):
        raise ValueError(f'stale source: last update {result["source_updated_at"]}')
    if args.output.exists():
        previous = json.loads(args.output.read_text(encoding='utf-8'))
        if previous.get('source_updated_at') == result['source_updated_at']:
            print('No new source timestamp; snapshot unchanged')
            return
    args.output.parent.mkdir(parents=True, exist_ok=True)
    tmp = args.output.with_suffix(args.output.suffix + '.tmp')
    tmp.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    tmp.replace(args.output)
    print(f'Saved {len(result["observations"])} observations, platform unverified, no trading alerts')

if __name__ == '__main__':
    try:
        main()
    except (ValueError, OSError, json.JSONDecodeError) as exc:
        print(f'ERROR: {exc}', file=sys.stderr)
        sys.exit(1)
