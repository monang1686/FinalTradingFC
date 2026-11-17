import unittest
from experimental_multisource_demo import build_demo

class MultisourceDemoTests(unittest.TestCase):
    def test_synthetic_provenance_and_conflict(self):
        data=build_demo()
        self.assertEqual(data['metadata_coverage'],{'matched':2,'total':3})
        self.assertEqual(data['rows'][0]['metadata']['rating'],88)
        self.assertNotIn('rating',data['rows'][1]['metadata'])
        self.assertIn('rating',data['rows'][1]['metadata_conflicts'])
        self.assertFalse(data['authorized'])
        self.assertEqual(data['production_signals'],[])
        self.assertTrue(all(not r['actionable'] for r in data['rows']))
if __name__=='__main__':
    unittest.main()
