import unittest
from datetime import datetime,timezone
from datafluxor_price_adapter import parse_prices

def fixture():
    return {"success":True,"data":{"items":[{"game":"fc27","ea_id":67340611,
        "platform":"ps","market":"console","price":1250000,
        "observed_at":"2026-11-17T12:00:00Z","exact":True}]}}
NOW=datetime(2026,11,17,12,30,tzinfo=timezone.utc)
class DataFluxorPriceAdapterTests(unittest.TestCase):
    def test_valid_non_actionable_observation(self):
        result=parse_prices(fixture(),now=NOW)
        self.assertEqual(result["quotes"][0]["id"],"67340611")
        self.assertFalse(result["quotes"][0]["actionable"])
        self.assertEqual(result["production_signals"],[])
        self.assertFalse(result["automatic_polling_enabled"])
    def test_stale_quote(self):
        self.assertTrue(parse_prices(fixture(),now=datetime(2026,11,17,16,tzinfo=timezone.utc))["quotes"][0]["stale"])
    def test_pc_rejected(self):
        data=fixture()
        data["data"]["items"][0]["platform"]="pc"
        with self.assertRaises(ValueError):
            parse_prices(data,now=NOW)
    def test_missing_per_card_time_rejected(self):
        data=fixture()
        del data["data"]["items"][0]["observed_at"]
        with self.assertRaises(ValueError):
            parse_prices(data,now=NOW)
    def test_duplicate_card_rejected(self):
        data=fixture()
        data["data"]["items"].append(dict(data["data"]["items"][0]))
        with self.assertRaises(ValueError):
            parse_prices(data,now=NOW)
if __name__=="__main__":
    unittest.main()
