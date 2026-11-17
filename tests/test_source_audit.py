import unittest
from unittest.mock import patch
from audit_market_sources import audit

class AuditTests(unittest.TestCase):
    def test_default_config_is_blocked(self):
        r=audit()
        self.assertFalse(r['live_feed_enabled'])
        self.assertGreaterEqual(len(r['providers']),3)
        self.assertTrue(all(p['status']=='blocked' for p in r['providers']))
        self.assertTrue(all(p['automated_requests_started'] is False for p in r['providers']))
    def test_approved_source_does_not_crash(self):
        import tempfile,json
        from datetime import datetime,timezone
        s={'id':'example','connector':'json_api','endpoint':'https://example.org/data',
           'permission_url':'https://example.org/terms','provenance_url':'https://example.org/provenance',
           'verified_at':datetime.now(timezone.utc).isoformat(),'enabled':True,'verified':True,
           'free':True,'automation_allowed':True,'storage_allowed':True,'interval_minutes':30}
        with tempfile.NamedTemporaryFile(mode='w+',suffix='.json',encoding='utf-8') as f:
            json.dump({'sources':[s]},f);f.flush()
            result=audit(f.name)
        self.assertEqual(result['providers'][0]['status'],'approved_for_connector_review')
        self.assertFalse(result['live_feed_enabled'])
if __name__=='__main__':unittest.main()
