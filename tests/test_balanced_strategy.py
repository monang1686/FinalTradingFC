import unittest
from balanced_strategy import load_config,evaluate_trade

class BalancedStrategyTests(unittest.TestCase):
    def test_allocation(self):
        config=load_config()
        self.assertEqual(config["capital_credits"],100000)
        self.assertEqual(config["reserve_credits"],10000)
        self.assertFalse(config["auto_buy_enabled"])
    def test_illustrative_trade_never_auto_actionable(self):
        r=evaluate_trade("fluctuation",buy_price=9000,reference_sell_price=11000,
                         source_verified=True,observed_history_count=8,quote_age_minutes=5)
        self.assertTrue(r["eligible_for_review"])
        self.assertFalse(r["actionable"])
        self.assertFalse(r["auto_buy"])
        self.assertEqual(r["net_profit_estimate"],1450)
    def test_unverified_quote_blocked(self):
        r=evaluate_trade("fluctuation",buy_price=9000,reference_sell_price=11000,
                         observed_history_count=8,quote_age_minutes=5)
        self.assertFalse(r["eligible_for_review"])
    def test_stale_quote_blocked(self):
        r=evaluate_trade("fluctuation",buy_price=9000,reference_sell_price=11000,
                         source_verified=True,observed_history_count=8,quote_age_minutes=60)
        self.assertFalse(r["eligible_for_review"])
    def test_card_exposure_blocked(self):
        r=evaluate_trade("fluctuation",buy_price=9000,reference_sell_price=11000,
                         source_verified=True,observed_history_count=8,quote_age_minutes=5,
                         existing_card_exposure=4000)
        self.assertFalse(r["eligible_for_review"])
    def test_reserve_protected(self):
        r=evaluate_trade("fluctuation",buy_price=9000,reference_sell_price=11000,
                         source_verified=True,observed_history_count=8,quote_age_minutes=5,
                         available_credits=15000)
        self.assertFalse(r["eligible_for_review"])
    def test_bad_strategy_rejected(self):
        with self.assertRaises(ValueError):
            evaluate_trade("arbitrage",buy_price=1000,reference_sell_price=2000)
if __name__=="__main__":
    unittest.main()
