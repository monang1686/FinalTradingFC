"""Multi-provider concurrent FC27 collector, with per-source authorization gates.

No network activity occurs unless the caller supplies approved, enabled sources.
A failure in one provider never changes or fabricates another provider's data.
"""
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from market_sources import collect, authorize, SourceBlocked
from market_engine import stamp
import json
from pathlib import Path

def collect_many(sources, *, transport=None, max_workers=3):
    if not isinstance(sources,list):
        raise ValueError('sources must be a list')
    if not 1 <= max_workers <= 3:
        raise ValueError('max_workers must be between 1 and 3')
    results={}; failures={}; approved=[]
    ids=set()
    for source in sources:
        sid=source.get('id') if isinstance(source,dict) else None
        if not isinstance(sid,str) or not sid or sid in ids:
            raise ValueError('invalid or duplicate source id')
        ids.add(sid)
        try:
            authorize(source)
            approved.append(source)
        except (SourceBlocked,ValueError,TypeError,KeyError) as exc:
            failures[sid]={'status':'blocked','reason':str(exc)}
    def run(source):
        if transport is None:
            return collect(source)
        return collect(source,transport=transport)
    with ThreadPoolExecutor(max_workers=max_workers) as pool:
        pending={pool.submit(run,source):source['id'] for source in approved}
        for future in as_completed(pending):
            sid=pending[future]
            try:
                payload=future.result()
                if not isinstance(payload,dict):
                    raise ValueError('invalid normalized response')
                results[sid]=payload
            except Exception as exc:
                failures[sid]={'status':'error','reason':type(exc).__name__}
    return {'collected_at':datetime.now(timezone.utc).isoformat(),
            'sources':results,'failures':failures,
            'source_count':len(results),
            'status':'no_authorized_sources' if not approved else
                     ('partial' if failures else 'collected'),
            'actionable':False}

def reconcile_quotes(observations, *, max_age_seconds=3600):
    """Compare normalized provider observations without making trade signals.

    Each input is a candidate {source_id, ea_id, platform, price, observed_at}.
    Independent providers must use identical EA IDs and console market.
    """
    now=datetime.now(timezone.utc)
    grouped={}; rejected=[]
    for index,o in enumerate(observations):
        try:
            if not isinstance(o,dict):
                raise ValueError('invalid observation')
            sid=o['source_id'];ea=o['ea_id'];platform=o['platform']
            p=o['price'];at=stamp(o['observed_at'])
            if not isinstance(sid,str) or not sid or type(ea) is not int or ea<=0:
                raise ValueError('invalid identity')
            if platform!='console' or type(p) is not int or p<=0 or p>15000000:
                raise ValueError('invalid market or price')
            if not 0 <= (now-at).total_seconds() <= max_age_seconds:
                raise ValueError('stale observation')
            grouped.setdefault(ea,{}).setdefault(sid,[]).append(p)
        except (ValueError,KeyError,TypeError,OverflowError) as exc:
            rejected.append({'index':index,'reason':str(exc)})
    out=[]
    for ea,by_source in grouped.items():
        # Multiple quotes from the same provider do not count as independent votes.
        if any(len(values)!=1 for values in by_source.values()):
            rejected.append({'ea_id':ea,'reason':'duplicate source quote'})
            continue
        prices=sorted(values[0] for values in by_source.values())
        median=prices[len(prices)//2] if len(prices)%2 else (prices[len(prices)//2-1]+prices[len(prices)//2])/2
        spread=(max(prices)-min(prices))/median if median else 1
        out.append({'ea_id':ea,'sources':len(prices),'median_reference_price':median,
                    'spread_percent':round(spread*100,2),
                    'agreement':'unconfirmed' if len(prices)<2 else
                                ('consistent' if spread<=0.05 else 'divergent'),
                    'actionable':False})
    return {'references':sorted(out,key=lambda x:x['ea_id']),
            'rejected':rejected,'actionable':False}


def offline_config_report(path='config/market-sources.json'):
    """Read provider configuration without issuing requests or activating sources."""
    config=json.loads(Path(path).read_text(encoding='utf-8'))
    sources=config.get('sources',[])
    if not isinstance(sources,list):
        raise ValueError('sources must be an array')
    report=collect_many(sources,transport=lambda _: (_ for _ in ()).throw(RuntimeError('network disabled in offline report')))
    return {'configured':len(sources),'authorized':len(sources)-sum(v['status']=='blocked' for v in report['failures'].values()),'blocked':report['failures'],'live_collection':False}

if __name__=='__main__':
    print(json.dumps(offline_config_report(),indent=2,ensure_ascii=False))
