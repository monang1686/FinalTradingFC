import unittest
from dynamic_watchlist import plan_watchlist

class WatchlistTests(unittest.TestCase):
    def test_promo_priority_and_no_network(self):
        result=plan_watchlist([{"id":"12","categories":["fodder"],"rating":85},
                               {"id":"13","categories":["promo","meta"],"rating":90}])
        self.assertEqual(result["selected"][0]["id"],"13")
        self.assertEqual(result["selected"][0]["desired_refresh_minutes"],5)
        self.assertFalse(result["refresh_enabled"])
        self.assertEqual(result["external_requests_made"],0)
        self.assertEqual(result["production_signals"],[])
    def test_exact_ids_only(self):
        with self.assertRaises(ValueError):
            plan_watchlist([{"id":"123","categories":[]},{"id":"123","categories":[]}])
    def test_maximum_watchlist(self):
        cards=[{"id":str(i+1),"categories":["meta"]} for i in range(500)]
        self.assertEqual(plan_watchlist(cards)["count"],300)
    def test_budget_exhaustion(self):
        result=plan_watchlist([],requests_per_month=250,monthly_refreshes=251)
        self.assertEqual(result["monthly_requests_remaining"],0)
    def test_fodder_rating_filter(self):
        result=plan_watchlist([{"id":"10","categories":["fodder"],"rating":82}])
        self.assertEqual(result["count"],0)
if __name__=="__main__":
    unittest.main()
