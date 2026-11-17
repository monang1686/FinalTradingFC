import unittest
from source_capabilities import readiness, CAPABILITIES

class CapabilityTests(unittest.TestCase):
    def test_valtown_is_standby_not_live(self):
        r=readiness()
        self.assertFalse(r['live_signals_enabled'])
        self.assertFalse(r['free_live_price_source_verified'])
        val=next(x for x in r['providers'] if x['provider']=='val-town')
        self.assertTrue(val['capabilities']['price_preview'])
        self.assertFalse(val['usable_for_live_signals'])
    def test_no_provider_claims_live_authorization(self):
        self.assertTrue(all(not p['usable_for_live_signals'] for p in readiness()['providers']))
    def test_no_false_independent_source(self):
        self.assertEqual(CAPABILITIES['val-town']['source_family'],'bowli-fut-market')
if __name__=='__main__':unittest.main()
