"""Synthetic tests only: no network calls or real price storage."""
import unittest
from datetime import datetime, timezone, timedelta
from valtown_adapter import inspect

NOW = datetime(2026, 11, 16, 22, 30, tzinfo=timezone.utc)

def fixture():
    return {"updated": "2026-11-16T22:00:00Z",
            "groups": {"gold": [
                {"eaId": 100, "rarityId": 1, "price": 1500},
                {"eaId": 101, "rarityId": 1, "price": 2500}
            ]}}

class ValTownAdapterTests(unittest.TestCase):
    def test_metadata_only(self):
        r = inspect(fixture(), NOW)
        self.assertEqual(r["cards"], 2)
        self.assertEqual(r["valid_prices"], 2)
        self.assertEqual(r["age_minutes"], 30)
        self.assertFalse(r["authorized_for_reuse"])
        self.assertFalse(r["can_generate_buy_signals"])
        self.assertNotIn("players", r)
    def test_duplicate_pair(self):
        p = fixture()
        p["groups"]["silver"] = [dict(p["groups"]["gold"][0])]
        self.assertEqual(inspect(p, NOW)["duplicate_pairs"], 1)
    def test_missing_and_invalid(self):
        p = fixture()
        p["groups"]["gold"][0]["price"] = 0
        p["groups"]["gold"][0].pop("eaId")
        r = inspect(p, NOW)
        self.assertEqual((r["invalid_prices"], r["missing_ids"]), (1, 1))
    def test_future_timestamp(self):
        p = fixture()
        p["updated"] = (NOW + timedelta(minutes=1)).isoformat()
        with self.assertRaises(ValueError):
            inspect(p, NOW)
    def test_invalid_group(self):
        p = fixture()
        p["groups"]["gold"] = {}
        with self.assertRaises(ValueError):
            inspect(p, NOW)
    def test_unexpected_group(self):
        p = fixture()
        p["groups"]["unknown"] = []
        with self.assertRaises(ValueError):
            inspect(p, NOW)

if __name__ == "__main__":
    unittest.main()
