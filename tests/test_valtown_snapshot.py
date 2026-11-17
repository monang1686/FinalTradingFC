import datetime as dt
import unittest
from importlib.machinery import SourceFileLoader

mod = SourceFileLoader("snapshot", "experimental/mobile-trader/valtown_snapshot.py").load_module()

class SnapshotTests(unittest.TestCase):
    def setUp(self):
        self.now = dt.datetime(2026, 11, 17, 20, 25, tzinfo=dt.timezone.utc)
        self.payload = {"updated": "2026-11-17T20:00:00Z", "groups": {"icons": [{"eaId": 37576, "name": "Ronaldo", "price": 15000000}]}}
    def test_valid_unverified(self):
        result = mod.transform(self.payload, self.now)
        self.assertEqual(result["count"], 1)
        self.assertFalse(result["verified"])
        self.assertFalse(result["production_signals_enabled"])
    def test_stale_rejected(self):
        with self.assertRaises(ValueError):
            mod.transform(self.payload, self.now + dt.timedelta(hours=3))
    def test_duplicate_rejected(self):
        self.payload["groups"]["icons"] *= 2
        with self.assertRaises(ValueError):
            mod.transform(self.payload, self.now)
    def test_invalid_price_rejected(self):
        self.payload["groups"]["icons"][0]["price"] = "15000000"
        with self.assertRaises(ValueError):
            mod.transform(self.payload, self.now)

if __name__ == "__main__":
    unittest.main()
