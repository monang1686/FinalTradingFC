import unittest
from urllib.error import HTTPError, URLError
from futdb_connection_check import classify_error

class FutDBDiagnosticTests(unittest.TestCase):
    def http(self, code):
        return HTTPError("https://api.fut-db.com/api/players", code, "ignored", {}, None)
    def test_rate_limit(self):
        self.assertEqual(classify_error(self.http(429)), "rate_limited")
        self.assertEqual(classify_error(RuntimeError("FUT-DB request limit reached")), "rate_limited")
    def test_auth(self):
        self.assertEqual(classify_error(self.http(401)), "authentication_or_entitlement_denied")
        self.assertEqual(classify_error(self.http(403)), "authentication_or_entitlement_denied")
        self.assertEqual(classify_error(PermissionError("secret")), "authentication_or_entitlement_denied")
    def test_other_http(self):
        self.assertEqual(classify_error(self.http(404)), "endpoint_not_found")
        self.assertEqual(classify_error(self.http(503)), "provider_server_error")
    def test_network_and_schema(self):
        self.assertEqual(classify_error(URLError("secret")), "network_error")
        self.assertEqual(classify_error(ValueError("secret")), "response_schema_error")
    def test_no_exception_text_in_status(self):
        self.assertNotIn("secret", classify_error(RuntimeError("secret")))
if __name__ == "__main__":
    unittest.main()
