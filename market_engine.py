"""Verified observation infrastructure. No provider is approved by default."""
import json
from datetime import datetime, timezone, timedelta
from pathlib import Path

MAX_AGE = timedelta(minutes=60)

def stamp(value):
    if not isinstance(value, str):
        raise ValueError('missing timestamp')
    dt = datetime.fromisoformat(value.replace('Z', '+00:00'))
    if dt.tzinfo is None:
        raise ValueError('timezone required')
    return dt.astimezone(timezone.utc)

def price(value):
    if type(value) is not int or not 0 < value <= 15000000:
        raise ValueError('invalid integer price')
    return value

def atomic(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + '.tmp')
    temp.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    temp.replace(path)

def ingest(payload, previous, source, now=None):
    """All-or-nothing validation; timestamps belong to source, never the fetch."""
    now = now or datetime.now(timezone.utc)
    if source.get('enabled') is not True or source.get('verified') is not True:
        raise ValueError('no verified authorized source configured')
    for field in ('id', 'endpoint', 'permission_url', 'provenance_url', 'verified_at'):
        if not source.get(field):
            raise ValueError('source evidence missing: ' + field)
    if stamp(source['verified_at']) > now:
        raise ValueError('future verification')
    if payload.get('game') != 'EA Sports FC 27' or payload.get('platform') != 'console':
        raise ValueError('wrong game or market')
    if payload.get('source_id') != source['id'] or payload.get('data_kind') != 'production':
        raise ValueError('wrong source or non-production data')
    if not isinstance(payload.get('players'), list) or not 0 < len(payload['players']) <= 25000:
        raise ValueError('invalid/empty snapshot')
    if previous.get('players') and previous.get('source_id') != source['id']:
        raise ValueError('source change requires separate history')
    old = {str(c['id']): c for c in previous.get('players', [])}
    cards, seen = [], set()
    for item in payload['players']:
        key = item.get('id')
        if not isinstance(key, str) or not key.isdigit() or int(key) <= 0 or key != str(int(key)) or key in seen:
            raise ValueError('invalid or duplicate card version id')
        seen.add(key)
        if item.get('tradeable') is not True or not isinstance(item.get('name'), str) or not item['name'].strip():
            raise ValueError('missing tradeability/name')
        at, value = stamp(item.get('timestamp')), price(item.get('price'))
        if at > now or now - at > MAX_AGE:
            raise ValueError('future or stale observation')
        version=item.get('version')
        if version is not None and (not isinstance(version,str) or not version.strip()):
            raise ValueError('invalid version metadata')
        prior_version=old.get(key,{}).get('version')
        if prior_version and version and prior_version!=version:
            raise ValueError('card version identity changed')
        history = list(old.get(key, {}).get('history', []))
        if history:
            last = history[-1]
            if at < stamp(last['timestamp']):
                raise ValueError('timestamp regression')
            if at == stamp(last['timestamp']) and value != last['price']:
                raise ValueError('conflicting same-time quote')
            if abs(value / last['price'] - 1) > .5:
                raise ValueError('anomaly: move greater than 50%; manual source review required')
        if not history or at > stamp(history[-1]['timestamp']):
            history.append({'timestamp': at.isoformat(), 'price': value})
        history = [p for p in history if stamp(p['timestamp']) >= now - timedelta(days=7)]
        card = {k: item[k] for k in ('id', 'name', 'tradeable')}
        card.update(version=version or prior_version, source_id=source['id'], platform='console', price=value, timestamp=at.isoformat(), history=history[-336:])
        # Liquidity is unavailable unless the source supplies measured sales and its window.
        sales = item.get('sales_1h')
        if sales is not None:
            if type(sales) is not int or sales < 0 or stamp(item.get('sales_observed_at')) != at:
                raise ValueError('invalid measured liquidity')
            card.update(sales_1h=sales, sales_observed_at=at.isoformat())
        cards.append(card)
    # Retain absent cards for partial feeds; their own timestamps determine freshness.
    present = {c['id'] for c in cards}
    cards.extend(c for key,c in old.items() if key not in present and c.get('history') and stamp(c['history'][-1]['timestamp']) >= now-timedelta(days=7))
    return {'version': 2, 'game': 'EA Sports FC 27', 'platform': 'console',
            'source': source['endpoint'], 'source_id': source['id'], 'verified': True,
            'updated_at': max((c['timestamp'] for c in cards), key=stamp), 'players': sorted(cards, key=lambda c:c['id'])}

def report(data, now=None, min_profit=800, min_roi=5):
    now = now or datetime.now(timezone.utc)
    output = {'engine': 'market-trends-v2', 'live_feed_connected': False, 'status': 'blocked_no_verified_source', 'trends': [], 'results': []}
    if data.get('verified') is not True or data.get('game') != 'EA Sports FC 27' or data.get('platform') != 'console':
        return output
    output.update(live_feed_connected=True, status='no_fresh_observations')
    for card in data.get('players', []):
        try:
            if card.get('tradeable') is not True or card.get('platform') != 'console':
                continue
            points = sorted(card['history'], key=lambda p: stamp(p['timestamp']))
            times = [stamp(p['timestamp']) for p in points]
            values = [price(p['price']) for p in points]
            if len(set(times)) != len(times) or not times or times[-1] > now or now-times[-1] > MAX_AGE:
                continue
            changes = {}
            for hours in (1, 6, 24):
                target = times[-1]-timedelta(hours=hours)
                candidates = [i for i,t in enumerate(times) if target-timedelta(minutes=15) <= t <= target]
                changes[str(hours)+'h'] = round((values[-1]/values[candidates[-1]]-1)*100, 4) if candidates else None
            risks = ['historical_target_not_live_listing']
            sales = card.get('sales_1h')
            if type(sales) is not int or sales < 0 or stamp(card.get('sales_observed_at')) != times[-1]:
                sales = None
                risks.append('liquidity_unknown')
            elif sales < 5:
                risks.append('low_liquidity')
            if any(abs(b/a-1) > .5 for a,b in zip(values, values[1:])):
                risks.append('anomalous_history')
            if len(values)<4:
                risks.append('insufficient_history')
            row = {'source': data.get('source'), 'source_id': data.get('source_id'), 'age_seconds': int((now-times[-1]).total_seconds()), 'reliability': 'validated_observation_not_execution_guarantee', 'version': card.get('version'), 'id': card['id'], 'name': card['name'], 'timestamp': points[-1]['timestamp'], 'price': values[-1],
                   'changes_percent': changes, 'sales_1h': sales, 'risk_flags': risks}
            output['trends'].append(row)
            output['status'] = 'ok'
            prior = [v for t,v in zip(times[:-1],values[:-1]) if times[-1]-timedelta(hours=24) <= t]
            if len(prior)<3 or sales is None or sales<5 or 'anomalous_history' in risks:
                continue
            prior.sort()
            target = prior[len(prior)//2]
            net = target*95//100-values[-1]
            roi = net/values[-1]*100
            if net>=min_profit and roi>=min_roi:
                output['results'].append({**row, 'sell_target_estimate': target, 'net_profit_estimate': net,
                                          'net_roi_percent': round(roi,2), 'warning': 'Stima storica, nessuna asta o vendita garantita'})
        except (ValueError, TypeError, KeyError, IndexError):
            continue
    output['results'].sort(key=lambda r:-r['net_roi_percent'])
    return output
