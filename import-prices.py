#!/usr/bin/env python3
"""FUT Trader 27: import authorized/manual CSV price observations into prices.json.

CSV columns: id,name,version,platform,tradeable,price,timestamp
Timestamps must be UTC ISO-8601; e.g. 2026-11-16T14:00:00Z.
No scraping, no external requests, no fabricated timestamps.
"""
import argparse
import csv
import json
from datetime import datetime, timezone
from pathlib import Path

REQUIRED = ('id', 'name', 'version', 'platform', 'tradeable', 'price', 'timestamp')
VALID_PLATFORMS = {'console', 'ps5', 'xbox'}

def parse_time(value):
    dt = datetime.fromisoformat(value.replace('Z', '+00:00'))
    if dt.tzinfo is None:
        raise ValueError('timestamp must include timezone')
    dt = dt.astimezone(timezone.utc)
    if dt > datetime.now(timezone.utc):
        raise ValueError('future observation timestamp')
    return dt.isoformat().replace('+00:00', 'Z')

def import_csv(csv_path, json_path, source):
    if not source.strip() or source.lower() in ('unknown', 'live', 'real-time'):
        raise ValueError('Specify a truthful source label, e.g. manual-observations')
    existing = json.loads(json_path.read_text(encoding='utf-8')) if json_path.exists() else {'version': 1, 'players': []}
    cards = {(str(p['id']), p['platform']): p for p in existing.get('players', [])}
    count = 0
    with csv_path.open(newline='', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        if not set(REQUIRED).issubset(reader.fieldnames or []):
            raise ValueError('Missing CSV columns: ' + ', '.join(sorted(set(REQUIRED) - set(reader.fieldnames or []))))
        for line, row in enumerate(reader, start=2):
            try:
                card_id, name = row['id'].strip(), row['name'].strip()
                platform = row['platform'].strip().lower()
                tradeable = row['tradeable'].strip().lower()
                price = int(row['price'])
                stamp = parse_time(row['timestamp'].strip())
                if not card_id or not name or platform not in VALID_PLATFORMS or tradeable not in ('true', 'false') or price <= 0:
                    raise ValueError('invalid card, platform, tradeable or price')
                key = (card_id, platform)
                card = cards.setdefault(key, {'id': card_id, 'name': name, 'version': row['version'].strip(), 'platform': platform, 'tradeable': tradeable == 'true', 'history': []})
                card.update(name=name, version=row['version'].strip(), tradeable=tradeable == 'true')
                if not any(x['timestamp'] == stamp for x in card['history']):
                    card['history'].append({'timestamp': stamp, 'price': price})
                    count += 1
            except (ValueError, TypeError, KeyError) as e:
                raise ValueError(f'Invalid CSV row {line}: {e}') from e
    for card in cards.values():
        card['history'] = sorted(card['history'], key=lambda x: x['timestamp'])[-288:]
    existing.update(version=1, verified=False, source=source, updated_at=datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'), players=sorted(cards.values(), key=lambda p: (p['id'], p['platform'])))
    # Write only after complete validation.
    temp = json_path.with_suffix(json_path.suffix + '.tmp')
    temp.write_text(json.dumps(existing, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    temp.replace(json_path)
    return count, len(cards)

if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('csv', type=Path)
    p.add_argument('--output', type=Path, default=Path('prices.json'))
    p.add_argument('--source', default='manual-observations')
    args = p.parse_args()
    count, cards = import_csv(args.csv, args.output, args.source)
    print(f'Imported {count} observations for {cards} cards into {args.output}')
