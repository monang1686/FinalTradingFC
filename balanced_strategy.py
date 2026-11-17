"""Offline evaluator for the balanced 100k strategy; never executes trades."""
import json
from pathlib import Path

CONFIG_PATH=Path(__file__).resolve().parent/"config"/"balanced-100k.json"

def load_config(path=CONFIG_PATH):
    data=json.loads(Path(path).read_text(encoding="utf-8"))
    allocations=sum(s["capital_limit"] for s in data["strategies"].values())
    if allocations+data["reserve_credits"]!=data["capital_credits"]:
        raise ValueError("allocation and reserve must equal capital")
    if data["production_signals_enabled"] or data["auto_buy_enabled"] or data["auto_polling_enabled"]:
        raise ValueError("experimental configuration cannot activate live execution")
    return data

def evaluate_trade(strategy, *, buy_price, reference_sell_price, source_verified=False,
                   observed_history_count=0, quote_age_minutes=None,
                   existing_strategy_exposure=0, existing_card_exposure=0,
                   total_open_exposure=0, available_credits=100000):
    config=load_config()
    if strategy not in config["strategies"]:
        raise ValueError("unknown strategy")
    p=config["strategies"][strategy]
    numeric=(buy_price,reference_sell_price,existing_strategy_exposure,
             existing_card_exposure,total_open_exposure,available_credits)
    if any(type(x) is not int or x<0 for x in numeric) or buy_price<=0 or reference_sell_price<=0:
        raise ValueError("positive integer prices and nonnegative exposures required")
    if quote_age_minutes is not None and (type(quote_age_minutes) not in (int,float) or quote_age_minutes<0):
        raise ValueError("invalid quote age")
    if type(observed_history_count) is not int or observed_history_count<0:
        raise ValueError("invalid history count")
    net_sale=reference_sell_price*95//100
    net_profit=net_sale-buy_price
    roi=round(100*net_profit/buy_price,2)
    discount=round(100*(reference_sell_price-buy_price)/reference_sell_price,2)
    checks={
        "source_verified":source_verified is True,
        "history_sufficient":observed_history_count>=p["min_history_observations"],
        "quote_fresh":quote_age_minutes is not None and quote_age_minutes<=p["max_quote_age_minutes"],
        "roi":roi>=p["min_net_roi_percent"],
        "profit":net_profit>=p["min_net_profit"],
        "discount":discount>=p["min_discount_percent"],
        "card_limit":buy_price+existing_card_exposure<=min(p["max_per_card"],config["risk"]["max_same_card_exposure_credits"]),
        "strategy_limit":buy_price+existing_strategy_exposure<=p["capital_limit"],
        "portfolio_limit":buy_price+total_open_exposure<=config["risk"]["max_open_exposure_credits"],
        "cash_reserve":available_credits-buy_price>=config["reserve_credits"],
    }
    return {"strategy":strategy,"net_profit_estimate":net_profit,"net_roi_percent":roi,
            "discount_percent":discount,"checks":checks,
            "eligible_for_review":all(checks.values()),
            "actionable":False,"auto_buy":False,
            "warning":"Historical reference is not a guaranteed sale; manual review required."}
