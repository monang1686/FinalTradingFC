import unittest
from importlib.machinery import SourceFileLoader
mod = SourceFileLoader("history", "experimental/mobile-trader/valtown_history.py").load_module()
def snap(time, price):
    return {"schema":"fut27-experimental-feed-v1","source":"https://fc27-market.val.run/latest","game":"FC27","platform_claim":"PlayStation","verified":False,"production_signals_enabled":False,"updated_at":time,"cards":[{"group":"gold","ea_id":123,"name":"Test","price":price}]}
class HistoryTests(unittest.TestCase):
    def setUp(self):
        self.empty={"schema":"fut27-experimental-history-v1","snapshots":[]}
        self.first=snap("2026-11-17T20:00:00Z",20000)
    def test_first_then_second(self):
        h,c=mod.advance(self.empty,self.first)
        self.assertIsNone(c)
        h,c=mod.advance(h,snap("2026-11-17T21:00:00Z",18000))
        self.assertEqual(c["price_drops"],1)
        self.assertEqual(len(h["snapshots"]),2)
    def test_identical_timestamp_idempotent(self):
        h,_=mod.advance(self.empty,self.first)
        h2,c=mod.advance(h,self.first)
        self.assertEqual(h,h2)
        self.assertIsNone(c)
    def test_conflicting_same_timestamp_rejected(self):
        h,_=mod.advance(self.empty,self.first)
        with self.assertRaises(ValueError):
            mod.advance(h,snap("2026-11-17T20:00:00Z",19000))
    def test_regression_rejected(self):
        h,_=mod.advance(self.empty,self.first)
        with self.assertRaises(ValueError):
            mod.advance(h,snap("2026-11-17T19:00:00Z",19000))
