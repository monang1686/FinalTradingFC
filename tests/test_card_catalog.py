import unittest
from card_catalog import build_catalog,enrich_market,card_id

class CatalogTests(unittest.TestCase):
    def test_exact_join_preserves_quote(self):
        catalog=build_catalog([{'ea_id':123,'name':'Sample','rating':88,'position':'ST'}],
                              provenance='authorized-fixture',authorized=True)
        snapshot={'verified':False,'players':[{'id':'123','price':10000,'timestamp':'2026-11-17T10:00:00Z'},
                                               {'id':'124','price':20000}]}
        out=enrich_market(snapshot,catalog)
        self.assertEqual(out['metadata_coverage'],{'matched':1,'total':2})
        self.assertEqual(out['players'][0]['price'],10000)
        self.assertEqual(out['players'][0]['metadata']['rating'],88)
        self.assertIsNone(out['players'][1]['metadata'])
        self.assertFalse(out['verified'])
    def test_rejects_unlicensed_catalog(self):
        with self.assertRaises(ValueError):
            build_catalog([],provenance='test',authorized=False)
    def test_no_base_card_guessing(self):
        catalog=build_catalog([{'ea_id':123,'name':'A'}],provenance='fixture',authorized=True)
        out=enrich_market({'players':[{'id':'456'}]},catalog)
        self.assertEqual(out['metadata_coverage']['matched'],0)
    def test_reject_duplicate_id(self):
        with self.assertRaises(ValueError):
            build_catalog([{'ea_id':123},{'ea_id':'123'}],provenance='fixture',authorized=True)
    def test_strict_ids(self):
        self.assertIsNone(card_id('00123'))
        self.assertIsNone(card_id(True))
        self.assertEqual(card_id(123),'123')
if __name__=='__main__':unittest.main()
