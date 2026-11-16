"""Synthetic-only diagnostics; no endpoint requests."""
import contextlib
import io
import json
import unittest
from unittest.mock import patch
from datetime import timedelta
import diagnose_valtown
from valtown_adapter import inspect
from valtown_compare import compare
from test_valtown_adapter import fixture, NOW

class DiagnosticTests(unittest.TestCase):
    def test_same_prices_do_not_prove_frequency(self):
        p=fixture();q=inspect(p,NOW)
        r=compare(p,p,q,q,60)
        self.assertEqual(r['price_changes'],0)
        self.assertFalse(r['feed_timestamp_advanced'])
        self.assertFalse(r['data_reuse_authorized'])
        self.assertEqual(r['observation_interval_seconds'],60)
    def test_regression_not_advanced(self):
        first=fixture();second=fixture();second['updated']='2026-11-16T21:00:00Z'
        r=compare(first,second,inspect(first,NOW),inspect(second,NOW))
        self.assertFalse(r['feed_timestamp_advanced'])
        self.assertTrue(r['feed_timestamp_regressed'])
    def test_offsets_compared_as_instants(self):
        p=fixture();q=fixture();q['updated']='2026-11-16T23:00:00+01:00'
        r=compare(p,q,inspect(p,NOW),inspect(q,NOW))
        self.assertFalse(r['feed_timestamp_advanced'])
        self.assertFalse(r['feed_timestamp_regressed'])
    def test_duplicate_item_with_different_rarity(self):
        p=fixture();p['groups']['gold'][1].update(eaId=100,rarityId=2)
        r=inspect(p,NOW)
        self.assertEqual(r['duplicate_pairs'],0)
        self.assertEqual(r['duplicate_ea_ids'],1)
        self.assertEqual(r['unique_ea_ids'],1)
    def test_bad_ids_and_extreme_prices(self):
        for key in (True,'01','-1','bad',None):
            p=fixture();p['groups']['gold'][0].update(eaId=key,price=15000001)
            r=inspect(p,NOW)
            self.assertEqual(r['invalid_ea_ids'],1)
            self.assertEqual(r['invalid_prices'],1)
    def test_schema_failure_exit_status(self):
        class Response:
            status=200
            headers={'Content-Type':'application/json'}
            def __enter__(self):return self
            def __exit__(self,*args):pass
            def read(self,*args):return b'{"groups": {}}'
        stream=io.StringIO()
        with patch('urllib.request.urlopen',return_value=Response()),contextlib.redirect_stdout(stream):
            code=diagnose_valtown.main()
        self.assertEqual(code,1)
        self.assertFalse(json.loads(stream.getvalue())['schema_valid'])
