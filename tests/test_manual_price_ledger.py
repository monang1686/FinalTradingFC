import unittest
from datetime import datetime, timezone
from manual_price_ledger import validate_observation,summarize_observations

def quote(item="12345",price=1000,when="2026-11-16T18:00:00Z"):
    return {"ea_item_id":item,"console_price":price,"observed_at":when,
            "source_url":"https://example.org/price/12345"}
class ManualPriceLedgerTests(unittest.TestCase):
    def test_observations_are_not_trading_signals(self):
        out=summarize_observations([quote()],now=datetime(2026,11,17,12,tzinfo=timezone.utc))
        self.assertEqual(out["total_observations"],1)
        self.assertTrue(out["cards"][0]["stale"])
        self.assertIsNone(out["cards"][0]["trend_percent"])
        self.assertFalse(out["cards"][0]["actionable"])
        self.assertEqual(out["production_signals"],[])
    def test_reject_missing_exact_id_and_price(self):
        for item in ("", "000123", "card name", "12.3"):
            with self.assertRaises(ValueError):
                validate_observation(quote(item=item))
        with self.assertRaises(ValueError):
            validate_observation(quote(price=0))
    def test_reject_future_or_unzoned_time(self):
        with self.assertRaises(ValueError):
            validate_observation(quote(when="2030-01-01T00:00:00Z"))
        with self.assertRaises(ValueError):
            validate_observation(quote(when="2026-11-16T18:00:00"))
    def test_reject_duplicate_observation(self):
        with self.assertRaises(ValueError):
            summarize_observations([quote(),quote()])
if __name__=="__main__":
    unittest.main()
