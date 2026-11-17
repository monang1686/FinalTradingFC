import unittest
from futdb_connector import request_page,normalize_players,catalog_from_pages,enrich_with_futdb

PAGE={'pagination':{'pageCurrent':1,'pageTotal':1},
      'items':[{'id':123,'resourceId':123,'name':'Example','rating':88,
                'position':'ST','club':10,'league':20,'nation':30,'rarity':40},
               {'id':456,'resourceId':789,'name':'Ambiguous'}]}
class FutDBTests(unittest.TestCase):
    def test_free_players_endpoint_and_key_header(self):
        calls=[]
        def fake(url,headers):
            calls.append((url,headers))
            return PAGE
        r=request_page('players',key='fixture-key',transport=fake)
        self.assertEqual(r,PAGE)
        self.assertEqual(calls[0][0],'https://api.fut-db.com/api/players?page=1')
        self.assertEqual(calls[0][1]['X-AUTH-TOKEN'],'fixture-key')
    def test_no_premium_endpoint(self):
        with self.assertRaises(ValueError):
            request_page('players/prices',key='fixture',transport=lambda *_:PAGE)
    def test_no_key(self):
        with self.assertRaises(ValueError):
            request_page('players',key='',transport=lambda *_:PAGE)
    def test_ambiguous_ids_skipped(self):
        r=normalize_players(PAGE)
        self.assertEqual(len(r),1)
        self.assertEqual(r[0]['ea_id'],123)
        self.assertEqual(r[0]['club'],'10')
    def test_requires_explicit_reuse_approval(self):
        with self.assertRaises(PermissionError):
            catalog_from_pages([PAGE])
    def test_enrichment_does_not_touch_quotes(self):
        snapshot={'verified':False,'players':[{'id':'123','price':10000},
                                              {'id':'456','price':9000}]}
        r=enrich_with_futdb(snapshot,[PAGE],approved_for_reuse=True)
        self.assertEqual(r['metadata_coverage'],{'matched':1,'total':2})
        self.assertEqual(r['players'][0]['price'],10000)
        self.assertIsNone(r['players'][1]['metadata'])
        self.assertFalse(r['verified'])
if __name__=='__main__':unittest.main()
