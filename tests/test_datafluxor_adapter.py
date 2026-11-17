"""No-network tests for DataFluxor sample adaptation."""
import unittest
from datetime import datetime,timezone
from datafluxor_adapter import AdapterError,normalize_prices

NOW=datetime(2026,11,17,12,0,tzinfo=timezone.utc)
def sample(**kw):
    item={'ea_id':67340611,'game':'fc27','platform':'ps','market':'console',
          'name':'Example Player','price':125000,'observed_at':'2026-11-17T11:45:00Z',
          'price_source':'card'}
    item.update(kw)
    return {'success':True,'data':{'items':[item]}}

class AdapterTests(unittest.TestCase):
    def test_candidate_never_actionable(self):
        result=normalize_prices(sample(),now=NOW)
        self.assertEqual(len(result['accepted']),1)
        self.assertFalse(result['accepted'][0]['actionable'])
        self.assertFalse(result['authorized'])
        self.assertFalse(result['live_feed_connected'])
    def test_missing_timestamp(self):
        self.assertIn('missing_observed_at',normalize_prices(sample(observed_at=None),now=NOW)['rejected'][0]['reasons'])
    def test_stale(self):
        self.assertIn('stale_or_future_observation',normalize_prices(sample(observed_at='2026-11-17T09:00:00Z'),now=NOW)['rejected'][0]['reasons'])
    def test_wrong_platform(self):
        self.assertIn('wrong_market',normalize_prices(sample(platform='pc',market='pc'),now=NOW)['rejected'][0]['reasons'])
    def test_zero_unlisted(self):
        self.assertIn('invalid_or_unlisted_price',normalize_prices(sample(price=0),now=NOW)['rejected'][0]['reasons'])
    def test_wrong_game(self):
        self.assertIn('wrong_game',normalize_prices(sample(game='fc26'),now=NOW)['rejected'][0]['reasons'])
    def test_identity_mismatch(self):
        self.assertIn('identity_or_staleness_flag',normalize_prices(sample(mismatch=True),now=NOW)['rejected'][0]['reasons'])
    def test_no_items(self):
        with self.assertRaises(AdapterError):normalize_prices({'success':True,'data':{}},now=NOW)
    def test_failed_envelope(self):
        with self.assertRaises(AdapterError):normalize_prices({'success':False,'data':{'items':[]}},now=NOW)
    def test_duplicate(self):
        item=sample()['data']['items'][0]
        result=normalize_prices({'success':True,'data':{'items':[item,item]}},now=NOW)
        self.assertEqual(len(result['accepted']),1)
        self.assertIn('duplicate_ea_id',result['rejected'][0]['reasons'])

if __name__=='__main__':unittest.main()
