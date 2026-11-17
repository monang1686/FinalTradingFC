import unittest
from card_catalog import build_catalog
from metadata_fusion import merge_catalogs,enrich_rows

class MetadataFusionTests(unittest.TestCase):
    def catalog(self, records, source):
        return build_catalog(records,provenance=source,authorized=True)
    def test_merge_complementary_fields_and_preserve_price(self):
        a=self.catalog([{"ea_id":123,"name":"Sample","rating":88}],"licensed-a")
        b=self.catalog([{"ea_id":123,"club":"10","position":"ST"}],"licensed-b")
        merged=merge_catalogs([a,b])
        snapshot={"authorized":False,"rows":[{"id":"123","price":5000,"actionable":False},
                                               {"id":"124","price":9000}]}
        result=enrich_rows(snapshot,merged)
        self.assertEqual(result["rows"][0]["metadata"]["position"],"ST")
        self.assertEqual(result["rows"][0]["price"],5000)
        self.assertFalse(result["rows"][0]["actionable"])
        self.assertFalse(result["authorized"])
        self.assertEqual(result["metadata_coverage"],{"matched":1,"total":2})
    def test_conflict_withheld(self):
        a=self.catalog([{"ea_id":123,"rating":88}],"licensed-a")
        b=self.catalog([{"ea_id":123,"rating":90}],"licensed-b")
        result=enrich_rows({"rows":[{"id":"123","price":1000}]},merge_catalogs([a,b]))
        self.assertNotIn("rating",result["rows"][0]["metadata"])
        self.assertEqual(result["rows"][0]["metadata_conflicts"]["rating"],["licensed-a","licensed-b"])
    def test_reject_unlicensed(self):
        with self.assertRaises(PermissionError):
            merge_catalogs([{"authorized":False,"provenance":"x","cards":{}}])
    def test_duplicate_provenance(self):
        a=self.catalog([],"licensed-a")
        with self.assertRaises(ValueError):
            merge_catalogs([a,a])
    def test_no_base_card_guessing(self):
        a=self.catalog([{"ea_id":123,"name":"Example"}],"licensed-a")
        result=enrich_rows({"rows":[{"id":"999","price":1000}]},merge_catalogs([a]))
        self.assertIsNone(result["rows"][0]["metadata"])
if __name__=="__main__":
    unittest.main()
