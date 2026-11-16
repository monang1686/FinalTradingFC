#!/usr/bin/env python3
"""FUT Trader 27 - Market Trends v0.1. No scraping or live market claims."""
import argparse
import json
import math
from datetime import datetime, timezone
from pathlib import Path

FEE = 0.05

def analyze(data, min_profit=800, min_roi=5, max_age_minutes=60):
    now = datetime.now(timezone.utc)
    results = []
    for card in data.get('players', []):
        try:
            if card.get('tradeable') is not True or card.get('platform') not in ('console', 'ps5', 'xbox'):
                continue
            history = card.get('history', [])
            if len(history) < 4:
                continue
            ordered = sorted(history, key=lambda x: x['timestamp'])
            latest = ordered[-1]
            last_time = datetime.fromisoformat(latest['timestamp'].replace('Z', '+00:00'))
            if (now - last_time).total_seconds() > max_age_minutes * 60 or last_time > now:
                continue
            prices = [int(x['price']) for x in ordered]
            if any(x <= 0 for x in prices):
                continue
            buy = prices[-1]
            prior = sorted(prices[:-1])
            middle = len(prior) // 2
            sell = prior[middle] if len(prior) % 2 else (prior[middle-1] + prior[middle]) // 2
            profit = math.floor(sell * (1-FEE)) - buy
            roi = 100 * profit / buy
            if profit < min_profit or roi < min_roi or sell <= buy:
                continue
            results.append({
                'id': str(card['id']), 'name': str(card['name']),
                'version': str(card.get('version', '')),
                'platform': card['platform'], 'buy_reference': buy,
                'sell_target_estimate': sell, 'net_profit_estimate': profit,
                'net_roi_percent': round(roi, 2), 'timestamp': latest['timestamp'],
                'observations': len(prices), 'source': data.get('source', 'unknown'),
                'warning': 'Stima su dati storici, non annuncio Compra ora verificato'
            })
        except (ValueError, KeyError, TypeError, OverflowError):
            continue
    return sorted(results, key=lambda x: (-x['net_roi_percent'], -x['net_profit_estimate']))

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('file', nargs='?', default='prices.json')
    args = parser.parse_args()
    data = json.loads(Path(args.file).read_text(encoding='utf-8'))
    print(json.dumps({'engine': 'market-trends-v0.1', 'live_feed_connected': False,
                      'results': analyze(data)}, ensure_ascii=False, indent=2))
