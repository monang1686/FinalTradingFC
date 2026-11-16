import copy
import unittest
from datetime import timedelta
from experimental_scanner import demo, scan, risk
from test_market import NOW
from test_pipeline import S

class ScannerTests(unittest.TestCase):
    def test_synthetic_never_operational(self):
        result=scan(demo(NOW),now=NOW)
        self.assertEqual(result['status'],'synthetic_demo')
        self.assertEqual(len(result['candidates']),1)
        self.assertEqual(result['production_signals'],[])
        self.assertTrue(all(r['simulated'] and not r['actionable'] for r in result['rows']))
    def test_fee_roi_and_windows(self):
        row=scan(demo(NOW),now=NOW)['candidates'][0]
        self.assertEqual(row['ea_fee'],600)
        self.assertEqual(row['net_profit_estimate'],1400)
        self.assertEqual(row['net_roi_percent'],14)
        self.assertEqual(row['changes_percent'],dict.fromkeys(('1h','6h','24h'),-16.6667))
    def test_stale_quote_visible_but_not_candidate(self):
        result=scan(demo(NOW),now=NOW)
        row=result['rows'][1]
        self.assertIn('stale_quote',row['risk_flags'])
        self.assertFalse(any(r['id']==row['id'] for r in result['candidates']))
    def test_missing_liquidity_suppresses_candidate(self):
        r=scan(demo(NOW),now=NOW)['rows'][2]
        self.assertIn('liquidity_unknown',r['risk_flags'])
        self.assertFalse(r['actionable'])
    def test_unverified_real_data_not_disclosed(self):
        p=demo(NOW);p.update(data_kind='production',verified=True)
        result=scan(p,now=NOW)
        self.assertEqual(result['rows'],[])
        self.assertEqual(result['status'],'blocked_unverified')
    def test_wrong_source_not_disclosed(self):
        p=demo(NOW);p.update(data_kind='production',verified=True)
        self.assertEqual(scan(p,S,NOW)['rows'],[])
    def test_real_requires_all_permissions(self):
        p=demo(NOW);p.update(data_kind='production',verified=True,source_id=S['id'])
        result=scan(p,{**S,'storage_allowed':False},NOW)
        self.assertEqual(result['rows'],[])
    def test_authorized_contract_offline(self):
        # Synthetic values test the production contract in memory, never a real quote.
        p=demo(NOW);p.update(data_kind='production',verified=True,source_id=S['id'])
        result=scan(p,S,NOW)
        self.assertEqual(len(result['production_signals']),1)
        self.assertFalse(result['simulated'])
    def test_no_mutation(self):
        p=demo(NOW);before=copy.deepcopy(p);scan(p,now=NOW)
        self.assertEqual(p,before)
    def test_missing_window_is_null(self):
        p=demo(NOW);p['players'][0]['history']=p['players'][0]['history'][-1:]
        row=scan(p,now=NOW)['rows'][0]
        self.assertEqual(row['changes_percent'],dict.fromkeys(('1h','6h','24h')))
        self.assertIn('insufficient_history',row['risk_flags'])
    def test_anomalous_history_no_candidate(self):
        p=demo(NOW);p['players'][0]['history'][0]['price']=100000
        result=scan(p,now=NOW)
        self.assertIn('anomalous_history',result['rows'][0]['risk_flags'])
        self.assertFalse(any(r['id']==p['players'][0]['id'] for r in result['candidates']))
    def test_future_history_no_candidate(self):
        p=demo(NOW);p['players'][0]['history'][-1]['timestamp']=(NOW+timedelta(minutes=1)).isoformat()
        result=scan(p,now=NOW)
        self.assertIn('future_quote',result['rows'][0]['risk_flags'])
        self.assertEqual(result['candidates'],[])
    def test_invalid_or_unsorted_history(self):
        for value in ([],list(reversed(demo(NOW)['players'][0]['history']))):
            p=demo(NOW);p['players'][0]['history']=value
            self.assertIn('invalid_history',scan(p,now=NOW)['rows'][0]['risk_flags'])
    def test_risk_bounded_explained_and_deduplicated(self):
        r=risk(['source_unverified','source_unverified','stale_quote','anomalous_history'])
        self.assertEqual(r['score'],100)
        self.assertEqual(len(r['factors']),3)
        self.assertEqual(r['method'],'heuristic_severity_not_loss_probability')
    def test_wrong_game_platform_rejected(self):
        for field,value in [('game','FC 26'),('platform','pc')]:
            p=demo(NOW);p[field]=value
            with self.assertRaises(ValueError):scan(p,now=NOW)
    def test_duplicates_rejected(self):
        p=demo(NOW);p['players'].append(copy.deepcopy(p['players'][0]))
        with self.assertRaises(ValueError):scan(p,now=NOW)
