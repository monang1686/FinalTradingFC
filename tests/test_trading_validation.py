"""Offline safety and accounting regression tests."""
import unittest
from datetime import datetime, timezone
from trading_validation import backtest, signal_status, validate_observation

NOW=datetime(2026,11,17,0,0,tzinfo=timezone.utc)
def row(**kw):
    data={'data_kind':'production','verified':True,'authorized':True,
          'game':'EA Sports FC 27','platform':'console','id':'123456789',
          'version':'Gold','tradeable':True,'timestamp':'2026-11-16T23:50:00Z',
          'price':10000,'sales_1h':10,'sell_target_estimate':12000}
    data.update(kw)
    return data
def fill(hour,kind,price,item='123'):
    return {'timestamp':f'2026-11-17T{hour:02d}:00:00Z','kind':kind,'price':price,'item_id':item}

class ValidationTests(unittest.TestCase):
    def test_good_row_still_not_actionable_without_execution(self):
        s=signal_status(row(),NOW)
        self.assertEqual(s['status'],'potential_opportunity')
        self.assertFalse(s['actionable'])
        self.assertEqual(s['net_profit_estimate'],1400)
    def test_unverified_blocked(self):
        self.assertIn('unverified_data',validate_observation(row(verified=False),NOW))
    def test_rights_blocked(self):
        self.assertIn('rights_unconfirmed',validate_observation(row(authorized=False),NOW))
    def test_pc_blocked(self):
        self.assertIn('wrong_market',validate_observation(row(platform='pc'),NOW))
    def test_missing_version(self):
        self.assertIn('version_unknown',validate_observation(row(version=None),NOW))
    def test_untradeable(self):
        self.assertIn('tradeability_unconfirmed',validate_observation(row(tradeable=False),NOW))
    def test_stale(self):
        self.assertIn('quote_not_fresh',validate_observation(row(timestamp='2026-11-16T20:00:00Z'),NOW))
    def test_unknown_liquidity(self):
        self.assertIn('liquidity_unverified',validate_observation(row(sales_1h=None),NOW))
    def test_invalid_id(self):
        self.assertIn('invalid_item_id',validate_observation(row(id='000123'),NOW))
    def test_low_margin(self):
        self.assertEqual(signal_status(row(sell_target_estimate=10500),NOW)['status'],'avoid')
    def test_no_target(self):
        self.assertEqual(signal_status(row(sell_target_estimate=None),NOW)['status'],'insufficient_data')
    def test_synthetic_never_actionable(self):
        self.assertFalse(signal_status(row(data_kind='synthetic'),NOW)['actionable'])

class ReplayTests(unittest.TestCase):
    def test_five_percent_fee(self):
        r=backtest([fill(1,'buy',10000),fill(2,'sell',12000)])
        self.assertEqual(r['realized_profit'],1400)
        self.assertEqual(r['cash_credits'],101400)
        self.assertEqual(r['completed_trades'],1)
    def test_no_implicit_fill(self):
        r=backtest([fill(1,'buy',10000)])
        self.assertEqual(r['realized_profit'],0)
        self.assertEqual(r['open_positions'],1)
    def test_unmatched_sale_not_profit(self):
        r=backtest([fill(2,'sell',12000)])
        self.assertEqual(r['realized_profit'],0)
        self.assertEqual(r['unmatched_events'],1)
    def test_loss(self):
        r=backtest([fill(1,'buy',10000),fill(2,'sell',9000)])
        self.assertEqual(r['realized_profit'],-1450)
        self.assertEqual(r['win_rate_percent'],0)
    def test_no_credit_leverage(self):
        r=backtest([fill(1,'buy',200000)],starting_credits=100000)
        self.assertEqual(r['unmatched_events'],1)
    def test_reject_unsorted(self):
        with self.assertRaises(ValueError):
            backtest([fill(2,'sell',12000),fill(1,'buy',10000)])
    def test_reject_price_snapshot(self):
        with self.assertRaises(ValueError):
            backtest([fill(1,'quote',10000)])
    def test_no_duplicate_position(self):
        r=backtest([fill(1,'buy',10000),fill(2,'buy',10000),fill(3,'sell',12000)])
        self.assertEqual(r['completed_trades'],1)
        self.assertEqual(r['unmatched_events'],1)

if __name__=='__main__':
    unittest.main()
