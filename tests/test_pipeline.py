"""Offline-only synthetic contracts; no fixture is a market observation."""
import copy
import unittest
from datetime import timedelta
from unittest.mock import patch
from market_sources import collect, authorize, SourceBlocked, public_host, NoRedirect
from market_pipeline import run
from market_engine import ingest, report
from test_market import NOW, SOURCE, payload

S={**SOURCE,'connector':'json_api','free':True,'automation_allowed':True,'storage_allowed':True,'interval_minutes':30}

class PipelineTests(unittest.TestCase):
    def test_disabled_never_calls_transport(self):
        with patch('market_sources.fetch_json') as transport:
            with self.assertRaises(SourceBlocked): collect({**S,'enabled':False},transport)
            transport.assert_not_called()
    def test_each_permission_required(self):
        for field in ('verified','free','automation_allowed','storage_allowed'):
            with self.assertRaises(SourceBlocked): authorize({**S,field:False},NOW)
    def test_expired_verification(self):
        with self.assertRaises(SourceBlocked): authorize({**S,'verified_at':(NOW-timedelta(days=91)).isoformat()},NOW)
    def test_public_feed_license_before_request(self):
        with patch('market_sources.authorize'),patch('market_sources.fetch_json') as transport:
            with self.assertRaises(SourceBlocked): collect({**S,'connector':'public_json'},transport)
            transport.assert_not_called()
    def test_authorized_json_contract(self):
        with patch('market_sources.authorize'):
            self.assertEqual(collect(S,lambda s:payload()),payload())
            with self.assertRaises(ValueError): collect(S,lambda s:{'source_id':'wrong'})
    def test_private_host_and_redirect_refused(self):
        with patch('socket.getaddrinfo',return_value=[(2,1,6,'',('127.0.0.1',443))]):
            with self.assertRaises(SourceBlocked): public_host('https://example.invalid')
        with self.assertRaises(SourceBlocked): NoRedirect().redirect_request(None,None,302,'',{},'https://example.invalid')
    def test_partial_feed_preserves_history(self):
        p=payload();p['players'].append({**p['players'][0],'id':'2'})
        old=ingest(p,{},SOURCE,NOW)
        data=ingest(payload(NOW+timedelta(minutes=30)),old,SOURCE,NOW+timedelta(minutes=30))
        self.assertEqual(len(data['players']),2)
        self.assertEqual(data['players'][1]['history'],old['players'][1]['history'])
    def test_failed_source_preserves_snapshot_suppresses_signals(self):
        state=run({'sources':[S]},now=NOW,collector=lambda s:payload())
        previous=copy.deepcopy(state)
        def fail(s): raise OSError('secret server body')
        failed=run({'sources':[S]},state,NOW+timedelta(hours=1),fail)
        entry=failed['sources'][S['id']]
        self.assertEqual(entry['snapshot'],state['sources'][S['id']]['snapshot'])
        self.assertEqual(entry['analysis']['results'],[])
        self.assertEqual(entry['fresh_cards'],0)
        self.assertEqual(entry['error'],'OSError')
        self.assertEqual(state,previous)
    def test_interval_no_request(self):
        state=run({'sources':[S]},now=NOW,collector=lambda s:payload())
        with patch('market_sources.fetch_json') as network:
            next_state=run({'sources':[S]},state,NOW+timedelta(minutes=1),network)
            network.assert_not_called()
            self.assertEqual(next_state['sources'][S['id']]['status'],'waiting_interval')
    def test_sources_isolated_and_unique_coverage(self):
        second={**S,'id':'second'}
        state=run({'sources':[S,second]},now=NOW,collector=lambda s:{**payload(),'source_id':s['id']})
        self.assertEqual(len(state['sources']),2)
        self.assertEqual(state['fresh_unique_cards'],1)
    def test_duplicate_configuration(self):
        with self.assertRaises(ValueError): run({'sources':[S,S]},now=NOW)
    def test_blocked_state_has_no_prices(self):
        state=run({'sources':[{**S,'enabled':False}]},now=NOW)
        self.assertEqual(state['fresh_unique_cards'],0)
        self.assertEqual(state['sources'][S['id']]['snapshot'],{})
    def test_stale_partial_card_not_fresh(self):
        old=ingest(payload(),{},SOURCE,NOW)
        later=NOW+timedelta(hours=2)
        p=payload(later);p['players'][0]['id']='2'
        data=ingest(p,old,SOURCE,later)
        self.assertEqual([r['id'] for r in report(data,later)['trends']],['2'])

    def test_noncanonical_item_id_rejected(self):
        p=payload();p['players'][0]['id']='01'
        with self.assertRaises(ValueError): ingest(p,{},SOURCE,NOW)
    def test_version_identity_change_rejected(self):
        p=payload();p['players'][0]['version']='Gold'
        old=ingest(p,{},SOURCE,NOW)
        p=payload(NOW+timedelta(minutes=30));p['players'][0]['version']='TOTW'
        with self.assertRaises(ValueError): ingest(p,old,SOURCE,NOW+timedelta(minutes=30))
    def test_source_outage_does_not_stop_other_source(self):
        second={**S,'id':'second'}
        def collector(source):
            if source['id']==S['id']: raise OSError('outage')
            return {**payload(),'source_id':source['id']}
        state=run({'sources':[S,second]},now=NOW,collector=collector)
        self.assertEqual(state['sources'][S['id']]['status'],'source_error')
        self.assertEqual(state['sources']['second']['status'],'ok')
        self.assertEqual(state['fresh_unique_cards'],1)
