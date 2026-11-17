import unittest
from datetime import datetime, timezone
from market_sources import ValTownJSON, SourceBlocked
from multi_source_collector import collect_many

class ValTownIntegrationTests(unittest.TestCase):
    def test_diagnostics_only(self):
        payload={'updated':datetime.now(timezone.utc).isoformat(),
                 'groups':{'gold':[{'eaId':123,'rarityId':1,'price':10000}],
                           'icons':[],'heroes':[],'bronze':[],'silver':[],'special':[]}}
        result=ValTownJSON().normalize(payload,{'id':'valtown','data_license':'test-fixture-only',
                                                 'license_url':'https://example.org/fixture'})
        self.assertEqual(result['kind'],'quality_diagnostics')
        self.assertEqual(result['diagnostics']['valid_prices'],1)
        self.assertFalse(result['actionable'])
        self.assertNotIn('observations',result)
    def test_license_required(self):
        with self.assertRaises(SourceBlocked):
            ValTownJSON().normalize({}, {'id':'valtown'})
    def test_unverified_never_fetches(self):
        source={'id':'valtown','connector':'valtown_json','enabled':False}
        result=collect_many([source],transport=lambda _:self.fail('should not fetch'))
        self.assertEqual(result['status'],'no_authorized_sources')
if __name__=='__main__':unittest.main()
