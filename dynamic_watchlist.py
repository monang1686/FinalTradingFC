"""Deterministic FC27 watchlist planner. No HTTP calls or EA account automation.

Prioritizes explicit card categories, bounded API budgets and quote freshness.
A plan never authorizes scraping or creates trading signals.
"""
from datetime import datetime, timezone

CATEGORY_WEIGHT={"promo":100,"meta":85,"totw":80,"fodder":60,"other":10}
DEFAULT_MINUTES={"promo":5,"meta":5,"totw":10,"fodder":30,"other":60}

def plan_watchlist(cards, *, max_cards=300, requests_per_month=250,
                   monthly_refreshes=0, now=None):
    if not isinstance(cards,list) or len(cards)>30000:
        raise ValueError("invalid card catalog")
    if type(max_cards) is not int or not 1<=max_cards<=300:
        raise ValueError("max_cards must be 1..300")
    if type(requests_per_month) is not int or requests_per_month<0:
        raise ValueError("invalid request budget")
    if type(monthly_refreshes) is not int or monthly_refreshes<0:
        raise ValueError("invalid consumed budget")
    now=now or datetime.now(timezone.utc)
    if now.tzinfo is None:
        raise ValueError("timezone-aware now required")
    seen=set()
    selected=[]
    for card in cards:
        if not isinstance(card,dict):
            raise ValueError("invalid card")
        ident=card.get("id")
        if not isinstance(ident,str) or not ident.isascii() or not ident.isdigit() or str(int(ident))!=ident or int(ident)<=0 or ident in seen:
            raise ValueError("exact unique EA card-version IDs required")
        seen.add(ident)
        categories=card.get("categories",[])
        if not isinstance(categories,list) or not all(isinstance(c,str) and c in CATEGORY_WEIGHT for c in categories):
            raise ValueError("invalid categories")
        category=max(categories or ["other"],key=lambda c:CATEGORY_WEIGHT[c])
        rating=card.get("rating")
        if rating is not None and (type(rating) is not int or not 1<=rating<=99):
            raise ValueError("invalid rating")
        if category=="fodder" and rating is not None and not 84<=rating<=90:
            continue
        selected.append({"id":ident,"category":category,"rating":rating,
                         "priority":CATEGORY_WEIGHT[category],
                         "desired_refresh_minutes":DEFAULT_MINUTES[category]})
    selected.sort(key=lambda x:(-x["priority"],x["id"]))
    selected=selected[:max_cards]
    remaining=max(0,requests_per_month-monthly_refreshes)
    return {"generated_at":now.isoformat(),"selected":selected,"count":len(selected),
            "monthly_request_budget":requests_per_month,
            "monthly_requests_remaining":remaining,
            "refresh_enabled":False,"external_requests_made":0,
            "source_permission_required":True,"production_signals":[]}
