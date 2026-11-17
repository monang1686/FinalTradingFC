import unittest
from datetime import datetime,timezone,timedelta
from multi_source_collector import collect_many,reconcile_quotes

NOW=datetime.now(timezone.utc)
def source(id):
    return {'id':id,'endpoint':'https://example.com/data','permission_url':'https://example.com/terms',
            'provenance_url':'https://example.com/source','verified_at':NOW.isoformat(),
            'enabled':True,'verified':True,'free':True,'automation_allowed':True,
            'storage_allowed':True,'interval_minutes':30,'connector':'json_api'}
class CollectorTests(unittest.TestCase):
    def test_blocks_unknown_permission(self):
        s=source('a');s['automation_allowed']=False
        r=collect_many([s],transport=lambda x: self.fail('network attempted'))
        self.assertEqual(r['status'],'no_authorized_sources')
    def test_two_concurrent_sources(self):
        r=collect_many([source('a'),source('b')],transport=lambda s:{'source_id':s['id'],'observations':[]})
        self.assertEqual(r['source_count'],2)
        self.assertFalse(r['actionable'])
    def test_isolate_failure(self):
        def fetch(s):
            if s['id']=='a':raise RuntimeError('unavailable')
            return {'source_id':s['id']}
        r=collect_many([source('a'),source('b')],transport=fetch)
        self.assertEqual(r['status'],'partial')
        self.assertEqual(r['source_count'],1)
    def test_duplicate_id(self):
        with self.assertRaises(ValueError):collect_many([source('a'),source('a')])
    def test_no_sources(self):
        self.assertEqual(collect_many([])['status'],'no_authorized_sources')
    def test_consensus(self):
        obs=[{'source_id':sid,'ea_id':123,'platform':'console','price':p,'observed_at':NOW.isoformat()} for sid,p in [('a',10000),('b',10200)]]
        r=reconcile_quotes(obs)
        self.assertEqual(r['references'][0]['agreement'],'consistent')
        self.assertFalse(r['actionable'])
    def test_divergence(self):
        obs=[{'source_id':sid,'ea_id':123,'platform':'console','price':p,'observed_at':NOW.isoformat()} for sid,p in [('a',10000),('b',15000)]]
        self.assertEqual(reconcile_quotes(obs)['references'][0]['agreement'],'divergent')
    def test_duplicate_source_no_false_consensus(self):
        obs=[{'source_id':'a','ea_id':123,'platform':'console','price':10000,'observed_at':NOW.isoformat()}]*2
        self.assertEqual(len(reconcile_quotes(obs)['references']),0)
    def test_cloned_feeds_not_independent(self):
        obs=[{'source_id':sid,'origin_family':'bowli-fut-market','ea_id':123,
              'platform':'console','price':p,'observed_at':NOW.isoformat()}
             for sid,p in [('valtown-a',10000),('valtown-b',10200)]]
        r=reconcile_quotes(obs)
        self.assertEqual(len(r['references']),0)
        self.assertTrue(any(x['reason']=='duplicate source quote' for x in r['rejected']))
    def test_stale_rejected(self):
        obs=[{'source_id':'a','ea_id':123,'platform':'console','price':10000,'observed_at':(NOW-timedelta(days=1)).isoformat()}]
        self.assertEqual(len(reconcile_quotes(obs)['references']),0)
if __name__=='__main__':unittest.main()
