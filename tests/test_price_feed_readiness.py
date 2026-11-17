import unittest
from datetime import datetime, timezone
from price_feed_readiness import evaluate_feed,candidate_report

class FeedReadinessTests(unittest.TestCase):
    def test_all_current_candidates_blocked(self):
        report=candidate_report()
        self.assertFalse(report["live_collection_enabled"])
        self.assertTrue(all(not x["ready_for_live_quotes"] for x in report["candidates"]))
    def test_fully_verified_fresh_source_can_be_eligible_without_polling(self):
        candidate={key:True for key in ("exact_ea_card_id","console_market",
            "per_card_observed_at","documented_reuse_permission","sample_schema_verified")}
        candidate.update(source_id="licensed-fixture",sample_observed_at="2026-11-17T12:00:00Z")
        result=evaluate_feed(candidate,now=datetime(2026,11,17,12,30,tzinfo=timezone.utc))
        self.assertTrue(result["ready_for_live_quotes"])
        self.assertFalse(result["automatic_polling_enabled"])
    def test_stale_sample_blocks(self):
        candidate={key:True for key in ("exact_ea_card_id","console_market",
            "per_card_observed_at","documented_reuse_permission","sample_schema_verified")}
        candidate["sample_observed_at"]="2026-11-15T12:00:00Z"
        result=evaluate_feed(candidate,now=datetime(2026,11,17,12,30,tzinfo=timezone.utc))
        self.assertFalse(result["ready_for_live_quotes"])
    def test_bypass_blocks(self):
        candidate={key:True for key in ("exact_ea_card_id","console_market",
            "per_card_observed_at","documented_reuse_permission","sample_schema_verified")}
        candidate.update(sample_observed_at="2026-11-17T12:00:00Z",requires_bypass=True)
        self.assertFalse(evaluate_feed(candidate,now=datetime(2026,11,17,12,30,tzinfo=timezone.utc))["ready_for_live_quotes"])
if __name__=="__main__":
    unittest.main()
