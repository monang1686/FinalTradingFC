"""Strict offline adapter for a DataFluxor FUT prices response.

This module never performs HTTP calls. Source licensing, tradeability and
liquidity must be verified independently before a real signal is allowed.
"""
from datetime import datetime, timezone
from market_engine import price, stamp

class AdapterError(ValueError):
    pass

def normalize_prices(payload, *, now=None):
    """Return safe observations; never fabricate missing provenance.

    Input must be a successful DataFluxor-style envelope with data.items.
    Unknown, stale, ambiguous, zero-priced and mismatched records are rejected.
    The output is a *candidate observation* list, NOT an ingestible verified
    production feed. Market engine authorization is a separate step.
    """
    now=now or datetime.now(timezone.utc)
    if not isinstance(payload,dict) or payload.get('success') is not True:
        raise AdapterError('successful response envelope required')
    data=payload.get('data')
    if not isinstance(data,dict) or not isinstance(data.get('items'),list):
        raise AdapterError('data.items array required')
    accepted=[];rejected=[];seen=set()
    for index,item in enumerate(data['items']):
        reasons=[]
        if not isinstance(item,dict):
            rejected.append({'index':index,'reasons':['invalid_record']})
            continue
        ea_id=item.get('ea_id')
        if type(ea_id) is not int or ea_id<=0:
            reasons.append('unresolved_ea_id')
        elif ea_id in seen:
            reasons.append('duplicate_ea_id')
        else:
            seen.add(ea_id)
        if item.get('game')!='fc27':
            reasons.append('wrong_game')
        if item.get('platform') not in ('ps','xbox') or item.get('market')!='console':
            reasons.append('wrong_market')
        if item.get('mismatch') or item.get('unresolved') or item.get('stale') is True:
            reasons.append('identity_or_staleness_flag')
        if not isinstance(item.get('name'),str) or not item['name'].strip():
            reasons.append('missing_name')
        try:
            p=price(item.get('price'))
        except (ValueError,TypeError):
            reasons.append('invalid_or_unlisted_price');p=None
        try:
            observed=stamp(item.get('observed_at'))
            if observed>now or (now-observed).total_seconds()>3600:
                reasons.append('stale_or_future_observation')
        except (ValueError,TypeError,OverflowError):
            observed=None;reasons.append('missing_observed_at')
        if reasons:
            rejected.append({'index':index,'ea_id':ea_id,'reasons':reasons})
            continue
        accepted.append({'id':str(ea_id),'name':item['name'].strip(),
                         'price':p,'timestamp':observed.isoformat(),
                         'platform':'console','price_source':item.get('price_source'),
                         'version_verified':False,'tradeability_verified':False,
                         'liquidity_verified':False,'authorized':False,
                         'actionable':False})
    return {'mode':'offline_candidate_observations','provider':'datafluxor',
            'authorized':False,'live_feed_connected':False,
            'accepted':accepted,'rejected':rejected,
            'warning':'Not verified for reuse or execution. No live trading signals.'}
