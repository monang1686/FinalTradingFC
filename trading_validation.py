"""Offline, conservative FC27 trading backtest. No network, no real-price claims.

A trade is filled only if an explicit synthetic buy/sell event exists. A price
snapshot alone never proves an executable auction or sale.
"""
from dataclasses import dataclass
from datetime import datetime, timezone
from market_engine import price, stamp

@dataclass(frozen=True)
class Rules:
    fee_percent: int = 5
    max_holding_hours: int = 24
    min_net_profit: int = 800
    min_roi_percent: float = 5.0

def validate_observation(row, now=None):
    """Return reasons to withhold a real-world signal, not a confidence claim."""
    now = now or datetime.now(timezone.utc)
    issues = []
    if row.get('data_kind') != 'production' or row.get('verified') is not True:
        issues.append('unverified_data')
    if row.get('authorized') is not True:
        issues.append('rights_unconfirmed')
    if row.get('game') != 'EA Sports FC 27' or row.get('platform') != 'console':
        issues.append('wrong_market')
    item_id = row.get('id')
    if not isinstance(item_id,str) or not item_id.isascii() or not item_id.isdecimal() or item_id.startswith('0') or int(item_id)==0:
        issues.append('invalid_item_id')
    if not isinstance(row.get('version'),str) or not row['version'].strip():
        issues.append('version_unknown')
    if row.get('tradeable') is not True:
        issues.append('tradeability_unconfirmed')
    try:
        observed = stamp(row.get('timestamp'))
        if observed > now or (now-observed).total_seconds() > 3600:
            issues.append('quote_not_fresh')
        price(row.get('price'))
    except (ValueError,TypeError,OverflowError):
        issues.append('invalid_price_or_timestamp')
    if type(row.get('sales_1h')) is not int or row['sales_1h'] < 5:
        issues.append('liquidity_unverified')
    return issues

def signal_status(row, now=None):
    reasons=validate_observation(row,now)
    if reasons:
        return {'status':'insufficient_data','reasons':reasons,'actionable':False}
    buy=row['price']
    target=row.get('sell_target_estimate')
    try:
        price(target)
    except (ValueError,TypeError):
        return {'status':'insufficient_data','reasons':['target_unavailable'],'actionable':False}
    net=(target*95)//100-buy
    roi=net/buy*100
    if net<800 or roi<5:
        return {'status':'avoid','reasons':['insufficient_margin'],'actionable':False}
    return {'status':'potential_opportunity','reasons':['execution_unverified'],'actionable':False,
            'net_profit_estimate':net,'roi_estimate_percent':round(roi,2)}

def backtest(events, starting_credits=100000, rules=None):
    """Synthetic execution-event replay, chronological and cash-constrained.

    Events: timestamp, kind ('buy'/'sell'), item_id, price, quantity=1.
    An explicit buy fill opens a position; an explicit sell fill closes it.
    No automatic execution based on quote snapshots, and no overlapping
    positions for the same item. Unrealized inventory is not booked as profit.
    """
    rules=rules or Rules()
    if type(starting_credits) is not int or starting_credits<=0:
        raise ValueError('positive integer starting credits required')
    if rules.fee_percent!=5 or rules.max_holding_hours<=0:
        raise ValueError('invalid simulation rules')
    parsed=[]
    for event in events:
        if event.get('kind') not in ('buy','sell') or not isinstance(event.get('item_id'),str) or not event['item_id']:
            raise ValueError('invalid fill event')
        if event.get('quantity',1)!=1 or type(event.get('quantity',1)) is not int:
            raise ValueError('only single-card fills supported')
        parsed.append((stamp(event.get('timestamp')),event['kind'],event['item_id'],price(event.get('price'))))
    if parsed!=sorted(parsed,key=lambda e:e[0]):
        raise ValueError('events must be chronological')
    cash=starting_credits
    peak=cash
    max_drawdown=0.0
    open_positions={}
    trades=[]
    unmatched=0
    for at,kind,item,value in parsed:
        if kind=='buy':
            if item in open_positions or value>cash:
                unmatched+=1
                continue
            cash-=value
            open_positions[item]=(at,value)
        else:
            if item not in open_positions:
                unmatched+=1
                continue
            bought_at,buy=open_positions.pop(item)
            proceeds=value*(100-rules.fee_percent)//100
            cash+=proceeds
            net=proceeds-buy
            hours=(at-bought_at).total_seconds()/3600
            trades.append({'item_id':item,'net_profit':net,'roi_percent':round(net/buy*100,2),
                           'holding_hours':round(hours,3),'within_holding_limit':hours<=rules.max_holding_hours})
        # Conservative equity marks remaining inventory at zero until an explicit sale.
        equity=cash
        peak=max(peak,equity)
        max_drawdown=max(max_drawdown,(peak-equity)/peak*100)
    completed=len(trades)
    return {'mode':'synthetic_fill_events_only','real_trading_signals':0,
            'starting_credits':starting_credits,'cash_credits':cash,
            'realized_profit':sum(t['net_profit'] for t in trades),
            'completed_trades':completed,'open_positions':len(open_positions),
            'unmatched_events':unmatched,'completion_rate_percent':round(completed/(completed+len(open_positions))*100,2) if completed+len(open_positions) else None,
            'win_rate_percent':round(sum(t['net_profit']>0 for t in trades)/completed*100,2) if completed else None,
            'average_holding_hours':round(sum(t['holding_hours'] for t in trades)/completed,2) if completed else None,
            'cash_only_drawdown_percent':round(max_drawdown,2),
            'trades':trades,
            'warning':'Synthetic fills only. Drawdown uses cash with inventory valued at zero; not portfolio mark-to-market.'}
