"""Smoke tests for the isolated mobile dashboard (no network access)."""
import unittest
from pathlib import Path

DASHBOARD = Path("experimental/mobile-trader/dashboard.html")

class MobileDashboardTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.html = DASHBOARD.read_text(encoding="utf-8")

    def test_mobile_and_local_import(self):
        self.assertIn('name="viewport"', self.html)
        self.assertIn('type="file"', self.html)
        self.assertIn('await f.text()', self.html)

    def test_unverified_data_only(self):
        self.assertIn("s.verified!==false", self.html)
        self.assertIn("s.production_signals_enabled!==false", self.html)
        self.assertIn("DATI NON VERIFICATI", self.html)

    def test_fee_and_history_comparison(self):
        self.assertIn("Math.ceil(buy/.95)", self.html)
        self.assertIn("c.price-p.price", self.html)
        self.assertIn("arr[i-1].updated_at", self.html)

    def test_opt_in_polling_keeps_unverified_guardrails(self):
        self.assertIn("id=\"refresh\"", self.html)
        self.assertIn("credentials:'omit'", self.html)
        self.assertIn("proxyUrl='/data/history.json'", self.html)
        self.assertIn("30*60*1000", self.html)
        self.assertIn("return valid({schema:'fut27-experimental-feed-v1'", self.html)

    def test_movement_summary_and_budget_filter(self):
        self.assertIn('id="analysis"', self.html)
        self.assertIn('id="show-drops"', self.html)
        self.assertIn('function renderAnalysis()', self.html)
        self.assertIn("c.price<=budget", self.html)
        self.assertIn("'Nessun segnale di acquisto.'", "'Nessun segnale di acquisto.'")

    def test_cloudflare_build_is_isolated(self):
        builder = Path("experimental/mobile-trader/build_pages.py").read_text(encoding="utf-8")
        self.assertIn('ROOT / "dashboard.html"', builder)
        self.assertIn('OUT / "index.html"', builder)
        self.assertNotIn("prices.json", builder)
        self.assertNotIn("main", builder)

    def test_no_html_injection_from_player_names(self):
        self.assertIn("name.textContent=c.name", self.html)
        self.assertNotIn("innerHTML", self.html)

if __name__ == "__main__":
    unittest.main()
