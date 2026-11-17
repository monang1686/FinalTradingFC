import unittest
from free_price_csv_import import import_console_csv

SOURCE="https://example.org/authorized-export"
class PriceCsvImportTests(unittest.TestCase):
    def test_valid_observation_not_actionable(self):
        csv="ea_item_id,console_price,observed_at\n12345,12000,2026-11-16T18:00:00Z\n"
        out=import_console_csv(csv,source_url=SOURCE,permission_confirmed=True)
        self.assertEqual(out["quotes"][0]["price"],12000)
        self.assertFalse(out["authorized"])
        self.assertFalse(out["quotes"][0]["actionable"])
        self.assertEqual(out["production_signals"],[])
    def test_permission_required(self):
        with self.assertRaises(PermissionError):
            import_console_csv("ea_item_id,console_price,observed_at\n",source_url=SOURCE)
    def test_no_inferred_id_or_timestamp(self):
        for csv in (
            "name,console_price,observed_at\nTest,1000,2026-11-16T18:00:00Z\n",
            "ea_item_id,console_price\n12345,1000\n",
            "ea_item_id,console_price,observed_at\n12345,1000,2026-11-16\n",
        ):
            with self.assertRaises(ValueError):
                import_console_csv(csv,source_url=SOURCE,permission_confirmed=True)
    def test_duplicate_versions_rejected(self):
        csv="ea_item_id,console_price,observed_at\n12345,1000,2026-11-16T18:00:00Z\n12345,1100,2026-11-16T19:00:00Z\n"
        with self.assertRaises(ValueError):
            import_console_csv(csv,source_url=SOURCE,permission_confirmed=True)
if __name__=="__main__":
    unittest.main()
