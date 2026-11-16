"""Synthetic fixtures for isolated tests only; never published as market quotes."""
import copy
import importlib.util
import unittest
from datetime import datetime, timezone, timedelta
from market_engine import ingest, report, stamp, price

NOW = datetime(2026,11,16,12,tzinfo=timezone.utc)
SOURCE = dict(enabled=True, verified=True, id='test-only', endpoint='https://example.invalid', permission_url='https://example.invalid/terms', provenance_url='https://example.invalid/docs', verified_at=(NOW-timedelta(days=2)).isoformat())

def payload(at=NOW, value=10000):
    return dict(game='EA Sports FC 27', platform='console', source_id='test-only', data_kind='production', players=[dict(id='1', name='TEST ONLY', tradeable=True, price=value, timestamp=at.isoformat())])

class MarketTests(unittest.TestCase):
    def test_source_disabled(self):
        with self.assertRaises(ValueError): ingest(payload(), {}, {}, NOW)
    def test_wrong_game_platform_and_sandbox(self):
        for field,value in [('game','FC 26'),('platform','pc'),('data_kind','sandbox'),('source_id','unknown')]:
            p=payload();p[field]=value
            with self.assertRaises(ValueError): ingest(p,{},SOURCE,NOW)
    def test_stale_future_and_naive(self):
        for value in [(NOW-timedelta(minutes=61)).isoformat(),(NOW+timedelta(seconds=1)).isoformat(),'2026-11-16T12:00:00']:
            p=payload();p['players'][0]['timestamp']=value
            with self.assertRaises(ValueError): ingest(p,{},SOURCE,NOW)
    def test_bad_prices(self):
        for value in [True,0,-1,1.1,'100',15000001]:
            with self.assertRaises(ValueError): price(value)
    def test_duplicate(self):
        p=payload();p['players']*=2
        with self.assertRaises(ValueError): ingest(p,{},SOURCE,NOW)
    def test_idempotent_and_conflict(self):
        data=ingest(payload(),{},SOURCE,NOW)
        self.assertEqual(data,ingest(payload(),data,SOURCE,NOW))
        with self.assertRaises(ValueError): ingest(payload(value=11000),data,SOURCE,NOW)
    def test_anomaly_and_regression(self):
        data=ingest(payload(NOW-timedelta(minutes=30)),{},SOURCE,NOW)
        with self.assertRaises(ValueError): ingest(payload(value=20000),data,SOURCE,NOW)
        with self.assertRaises(ValueError): ingest(payload(NOW-timedelta(minutes=45)),data,SOURCE,NOW)
    def test_partial_failure_no_mutation(self):
        data=ingest(payload(),{},SOURCE,NOW); before=copy.deepcopy(data)
        p=payload();p['players'].append(dict(p['players'][0],id='2',price=-1))
        with self.assertRaises(ValueError): ingest(p,data,SOURCE,NOW)
        self.assertEqual(data,before)
    def data(self):
        data={}
        for hours,value in [(24,12000),(6,12000),(1,12000),(0,10000)]:
            at=NOW-timedelta(hours=hours)
            p=payload(at,value);p['players'][0].update(sales_1h=10,sales_observed_at=at.isoformat())
            data=ingest(p,data,SOURCE,at)
        return data
    def test_windows_and_fee(self):
        result=report(self.data(),NOW)
        self.assertEqual(result['trends'][0]['changes_percent'],dict.fromkeys(['1h','6h','24h'],-16.6667))
        self.assertEqual(result['results'][0]['net_profit_estimate'],1400)
        self.assertEqual(result['results'][0]['net_roi_percent'],14)
    def test_missing_windows_and_liquidity(self):
        data=ingest(payload(),{},SOURCE,NOW);r=report(data,NOW)
        self.assertEqual(r['trends'][0]['changes_percent'],dict.fromkeys(['1h','6h','24h']))
        self.assertEqual(r['results'],[])
        self.assertIn('liquidity_unknown',r['trends'][0]['risk_flags'])
    def test_stale_and_unverified_suppressed(self):
        self.assertEqual(report(self.data(),NOW+timedelta(hours=2))['results'],[])
        self.assertEqual(report({'players':[payload()['players'][0]]},NOW)['trends'],[])
    def test_no_liquidity_no_signal(self):
        data=self.data();del data['players'][0]['sales_1h']
        self.assertEqual(report(data,NOW)['results'],[])
    def test_empty_snapshot(self):
        p=payload();p['players']=[]
        with self.assertRaises(ValueError): ingest(p,{},SOURCE,NOW)
    def test_source_switch(self):
        data=self.data();data['source_id']='other'
        with self.assertRaises(ValueError): ingest(payload(),data,SOURCE,NOW)

if __name__=='__main__': unittest.main()
