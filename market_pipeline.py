"""Experimental single-file state; histories are never mixed across sources."""
import copy
from datetime import datetime, timezone, timedelta
from market_engine import ingest, report, stamp
from market_sources import collect, authorize

def run(config, previous=None, now=None, collector=collect):
    now=now or datetime.now(timezone.utc)
    state=copy.deepcopy(previous or {'sources':{}})
    state.update(version=2,generated_at=now.isoformat(),experimental=True,automations_active=False)
    configured=config.get('sources',[])
    ids=[s.get('id') for s in configured]
    if len(ids)!=len(set(ids)):
        raise ValueError('duplicate source configuration')
    next_sources={}
    for source in configured:
        sid=source['id']; old=state['sources'].get(sid,{})
        entry={'snapshot':old.get('snapshot',{}),'last_success_at':old.get('last_success_at')}
        try:
            authorize(source,now)
            last=entry['last_success_at']
            if last and now-stamp(last)<timedelta(minutes=source['interval_minutes']):
                entry.update(status='waiting_interval',error=None)
            else:
                payload=collector(source)
                entry['snapshot']=ingest(payload,entry['snapshot'],source,now)
                entry.update(status='ok',error=None,last_success_at=now.isoformat())
        except Exception as exc:
            # A source outage cannot destroy history or stop independent sources.
            # Keep error type only: server responses/URLs may contain secrets.
            entry.update(status='blocked' if isinstance(exc,ValueError) else 'source_error',error=type(exc).__name__)
        entry.update(endpoint=source.get('endpoint'),permission_url=source.get('permission_url'),
                     provenance_url=source.get('provenance_url'),block_reason=source.get('block_reason'))
        analysis=report(entry['snapshot'],now)
        entry['analysis']=analysis
        entry['fresh_cards']=len(analysis['trends']) if entry['status'] in ('ok','waiting_interval') else 0
        if entry['status'] not in ('ok','waiting_interval'):
            analysis.update(status='source_unavailable',live_feed_connected=False,trends=[],results=[])
        next_sources[sid]=entry
    state['sources']=next_sources
    state['fresh_unique_cards']=len({r['id'] for e in next_sources.values() for r in e['analysis']['trends']})
    state['status']='ok' if state['fresh_unique_cards'] else 'blocked_no_fresh_authorized_data'
    return state
