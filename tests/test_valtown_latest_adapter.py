import unittest
from datetime import datetime,timezone
from valtown_latest_adapter import parse_latest,GROUPS

def fixture():
    return {"updated":"2026-11-17T12:00:00Z",
            "groups":{group:([{"eaId":37576,"name":"Test Icon","rating":94,
                               "price":14500000,"signal":"profit",
                               "forecast":[14600000]}] if group=="icons" else [])
                      for group in GROUPS}}
class ValTownAdapterTests(unittest.TestCase):
    def test_price_observation_never_becomes_trading_signal(self):
        result=parse_latest(fixture(),now=datetime(2026,11,17,12,15,tzinfo=timezone.utc))
        self.assertEqual(result["count"],1)
        self.assertEqual(result["rows"][0]["price"],14500000)
        self.assertFalse(result["rows"][0]["actionable"])
        self.assertIsNone(result["rows"][0]["per_card_observed_at"])
        self.assertEqual(result["rows"][0]["feed_updated_at"],"2026-11-17T12:00:00+00:00")
        self.assertFalse(result["per_card_timestamp_verified"])
        self.assertEqual(result["production_signals"],[])
        self.assertNotIn("signal",result["rows"][0])
        self.assertFalse(result["automatic_polling_enabled"])
    def test_stale_feed(self):
        result=parse_latest(fixture(),now=datetime(2026,11,17,16,tzinfo=timezone.utc))
        self.assertTrue(result["stale"])
    def test_missing_group_rejected(self):
        data=fixture()
        del data["groups"]["bronze"]
        with self.assertRaises(ValueError):
            parse_latest(data)
    def test_duplicate_card_rejected(self):
        data=fixture()
        data["groups"]["heroes"]=list(data["groups"]["icons"])
        with self.assertRaises(ValueError):
            parse_latest(data)
    def test_future_timestamp_rejected(self):
        with self.assertRaises(ValueError):
            parse_latest(fixture(),now=datetime(2026,11,17,11,tzinfo=timezone.utc))
if __name__=="__main__":
    unittest.main()
