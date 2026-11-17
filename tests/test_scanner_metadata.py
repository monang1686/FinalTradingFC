import unittest
from datetime import datetime, timezone
from experimental_scanner import demo, scan
from card_catalog import build_catalog
from metadata_fusion import merge_catalogs

class ScannerMetadataTests(unittest.TestCase):
    def test_synthetic_scanner_metadata_provenance_without_signals(self):
        catalog=merge_catalogs([
            build_catalog([{'ea_id':900000001,'name':'Fixture One','rating':85}],
                          provenance='authorized-offline-fixture-a',authorized=True),
            build_catalog([{'ea_id':900000001,'position':'ST'}],
                          provenance='authorized-offline-fixture-b',authorized=True)])
        now=datetime(2026,11,17,12,0,tzinfo=timezone.utc)
        result=scan(demo(now),now=now,metadata_catalog=catalog)
        self.assertEqual(result['metadata_coverage'],{'matched':1,'total':3})
        row=result['rows'][0]
        self.assertEqual(row['metadata']['position'],'ST')
        self.assertEqual(row['metadata_field_sources']['position'],['authorized-offline-fixture-b'])
        self.assertFalse(result['authorized'])
        self.assertEqual(result['production_signals'],[])
        self.assertTrue(all(not r['actionable'] for r in result['rows']))
    def test_unlicensed_catalog_rejected(self):
        now=datetime(2026,11,17,12,0,tzinfo=timezone.utc)
        with self.assertRaises(PermissionError):
            scan(demo(now),now=now,metadata_catalog={'authorized':False})
if __name__=='__main__':
    unittest.main()
