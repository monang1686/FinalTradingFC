import unittest
from datetime import datetime,timezone
from local_observation_exchange import validate_bundle

NOW=datetime(2026,11,17,20,tzinfo=timezone.utc)
def sample():
    return {"format":"fut-trader-27-observations-v1","data_kind":"manual_unverified",
            "production_signals":[],"records":[{"id":"12345","name":"Test 87","strategy":"fluctuation",
            "buy":9000,"target":11000,"history":4,
            "source":"https://example.com/market","observed":"2026-11-17T19:00:00Z"}]}
class LocalObservationExchangeTests(unittest.TestCase):
    def test_roundtrip(self):
        result=validate_bundle(sample(),now=NOW)
        self.assertEqual(result["records"][0]["id"],"12345")
        self.assertFalse(result["actionable"])
    def test_future_timestamp(self):
        data=sample()
        data["records"][0]["observed"]="2026-11-18T00:00:00Z"
        with self.assertRaises(ValueError):validate_bundle(data,now=NOW)
    def test_reject_credentials_in_url(self):
        data=sample()
        data["records"][0]["source"]="https://user:secret@example.com"
        with self.assertRaises(ValueError):validate_bundle(data,now=NOW)
    def test_reject_production_signals(self):
        data=sample()
        data["production_signals"]=[{"id":"12345"}]
        with self.assertRaises(ValueError):validate_bundle(data,now=NOW)
    def test_reject_wrong_format(self):
        data=sample()
        data["format"]="unknown"
        with self.assertRaises(ValueError):validate_bundle(data,now=NOW)
if __name__=="__main__":unittest.main()
