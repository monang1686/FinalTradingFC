import unittest
from importlib.machinery import SourceFileLoader
mod = SourceFileLoader("comparison", "experimental/mobile-trader/valtown_compare.py").load_module()

def snapshot(stamp, price):
    return {"schema":"fut27-experimental-feed-v1","source":"https://fc27-market.val.run/latest","game":"FC27","platform_claim":"PlayStation","verified":False,"production_signals_enabled":False,"updated_at":stamp,"cards":[{"group":"gold","ea_id":123,"name":"Test Card","price":price}]}

class ComparisonTests(unittest.TestCase):
    def test_price_drop_and_break_even(self):
        r=mod.compare(snapshot("2026-11-17T19:00:00Z",20000),snapshot("2026-11-17T20:00:00Z",18000))
        self.assertEqual(r["price_drops"],1)
        self.assertEqual(r["rows"][0]["change_percent"],-10)
        self.assertEqual(r["rows"][0]["break_even_sell_price"],18948)
        self.assertFalse(r["signals_enabled"])
    def test_same_timestamp_rejected(self):
        with self.assertRaises(ValueError):
            mod.compare(snapshot("2026-11-17T20:00:00Z",20000),snapshot("2026-11-17T20:00:00Z",18000))
    def test_source_change_rejected(self):
        a=snapshot("2026-11-17T19:00:00Z",20000)
        a["source"]="another"
        with self.assertRaises(ValueError):
            mod.compare(a,snapshot("2026-11-17T20:00:00Z",18000))
    def test_unverified_only(self):
        a=snapshot("2026-11-17T19:00:00Z",20000)
        a["verified"]=True
        with self.assertRaises(ValueError):
            mod.compare(a,snapshot("2026-11-17T20:00:00Z",18000))
