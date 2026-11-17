"""Offline-first scanner. Synthetic reports never become production signals."""
import argparse
import copy
import json
from datetime import datetime, timezone, timedelta
from pathlib import Path
from market_engine import report, price, stamp
from market_sources import authorize
from metadata_fusion import enrich_rows

WEIGHTS = {'source_unverified':40,'stale_quote':35,'future_quote':50,
           'liquidity_unknown':20,'low_liquidity':20,'insufficient_history':20,
           'missing_windows':10,'anomalous_history':40,'volatile_history':20,
           'invalid_history':50,'source_unavailable':40}

def risk(flags):
    """Heuristic severity 0..100, never a probability of loss."""
    factors={f:WEIGHTS[f] for f in sorted(set(flags)) if f in WEIGHTS}
    score=min(100,sum(factors.values()))
    return {'score':score,'level':'high' if score>=60 else 'medium' if score>=25 else 'low',
            'factors':factors,'method':'heuristic_severity_not_loss_probability'}

def scan(data, source=None, now=None, min_profit=800, min_roi=5, metadata_catalog=None):
    now=now or datetime.now(timezone.utc)
    kind=data.get('data_kind','unverified')
    simulated=kind=='synthetic'
    allowed=False
    if kind=='production' and source:
        try:
            authorize(source,now)
            allowed=(data.get('verified') is True and data.get('source_id')==source['id'])
        except (ValueError,TypeError):
            pass
    output={'engine':'experimental-scanner-v1','generated_at':now.isoformat(),
            'data_kind':kind,'simulated':simulated,'authorized':allowed,
            'status':'synthetic_demo' if simulated else 'authorized' if allowed else 'blocked_unverified',
            'rows':[],'candidates':[],'production_signals':[],
            'source_risk':risk([] if simulated or allowed else ['source_unverified'])}
    if not (simulated or allowed):
        # No real quote values enter a report until reuse has been authorized.
        return output
    if data.get('game')!='EA Sports FC 27' or data.get('platform')!='console':
        raise ValueError('FC27 console contract required')
    trusted=copy.deepcopy(data)
    trusted['verified']=True  # computation only; synthetic output remains explicitly synthetic
    analyzed=report(trusted,now,min_profit,min_roi)
    trends={r['id']:r for r in analyzed['trends']}
    eligible={r['id']:r for r in analyzed['results']}
    seen=set()
    for card in data.get('players',[]):
        key=card.get('id')
        if not isinstance(key,str) or not key.isascii() or not key.isdigit() or str(int(key))!=key or int(key)<=0 or key in seen:
            raise ValueError('invalid/duplicate EA item ID')
        seen.add(key)
        row={'id':key,'name':card.get('name',''),'version':card.get('version'),
             'data_kind':kind,'simulated':simulated,'source_id':data.get('source_id'),
             'actionable':False,'changes_percent':dict.fromkeys(('1h','6h','24h')),
             'net_profit_estimate':None,'net_roi_percent':None,
             'warning':'Target storico ipotetico; nessuna asta o vendita garantita.'}
        flags=['synthetic_test_data'] if simulated else []
        if card.get('platform')!='console' or card.get('tradeable') is not True:
            flags.append('invalid_history')
        try:
            points=card['history']
            times=[stamp(p['timestamp']) for p in points]
            values=[price(p['price']) for p in points]
            if not points or times!=sorted(set(times)):
                raise ValueError('empty or non-unique/ordered history')
            at=times[-1]; age=(now-at).total_seconds()
            row.update(price=values[-1],timestamp=points[-1]['timestamp'],age_seconds=int(age))
            if age<0: flags.append('future_quote')
            elif age>3600: flags.append('stale_quote')
            if key in trends:
                row.update(trends[key]);flags.extend(trends[key]['risk_flags'])
            else:
                if len(points)<4: flags.append('insufficient_history')
                flags.append('liquidity_unknown')
            if any(v is None for v in row['changes_percent'].values()): flags.append('missing_windows')
            if any(abs(b/a-1)>.5 for a,b in zip(values,values[1:])): flags.append('anomalous_history')
            recent=[v for t,v in zip(times,values) if at-timedelta(hours=24)<=t<=at]
            if len(recent)>1 and (max(recent)-min(recent))/min(recent)>.25: flags.append('volatile_history')
            prior=sorted(v for t,v in zip(times[:-1],values[:-1]) if at-timedelta(hours=24)<=t<at)
            if len(prior)>=3:
                target=prior[len(prior)//2]
                net=target*95//100-values[-1]
                row.update(sell_target_estimate=target,ea_fee=target-target*95//100,
                           net_profit_estimate=net,net_roi_percent=round(net/values[-1]*100,2))
        except (ValueError,TypeError,KeyError,IndexError):
            flags.append('invalid_history')
        row.update(risk_flags=sorted(set(flags)),risk=risk(flags))
        output['rows'].append(row)
        if key in eligible and not any(f in flags for f in ('invalid_history','stale_quote','future_quote','anomalous_history')):
            row['actionable']=allowed
            output['candidates'].append(copy.deepcopy(row))
            if allowed: output['production_signals'].append(copy.deepcopy(row))
    output['candidates'].sort(key=lambda r:(r['risk']['score'],-r['net_roi_percent']))
    if metadata_catalog is not None:
        output=enrich_rows(output,metadata_catalog)
        # Candidates receive only matching metadata; never alter trading eligibility.
        by_id={row['id']:row for row in output['rows']}
        for candidate in output['candidates']:
            enriched=by_id[candidate['id']]
            for field in ('metadata','metadata_field_sources','metadata_conflicts'):
                candidate[field]=copy.deepcopy(enriched[field])
    return output

def demo(now=None):
    now=now or datetime.now(timezone.utc)
    cards=[]
    for key,age,sales in [('900000001',0,10),('900000002',120,None),('900000003',0,None)]:
        at=now-timedelta(minutes=age)
        card={'id':key,'name':'FIXTURE SINTETICA '+key,'version':'TEST ONLY',
              'platform':'console','tradeable':True,
              'history':[{'timestamp':(at-timedelta(hours=h)).isoformat(),'price':v}
                         for h,v in [(24,12000),(6,12000),(1,12000),(0,10000)]]}
        if sales is not None: card.update(sales_1h=sales,sales_observed_at=at.isoformat())
        cards.append(card)
    return {'game':'EA Sports FC 27','platform':'console','data_kind':'synthetic',
            'verified':False,'source_id':'synthetic-offline-fixture','players':cards}

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--demo',action='store_true',required=True,help='Synthetic offline fixture only; no network or output files')
    parser.parse_args()
    print(json.dumps(scan(demo()),ensure_ascii=False,indent=2))
