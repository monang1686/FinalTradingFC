import unittest
from datetime import datetime, timezone
from email.message import Message
from urllib.error import HTTPError
from futdb_connector import parse_retry_after, request_page, FutDBRateLimitError
from futdb_connection_check import classify_error

class RetryAfterTests(unittest.TestCase):
    def test_seconds(self):
        self.assertEqual(parse_retry_after("120"), 120)
        self.assertEqual(parse_retry_after("0"), 0)
    def test_http_date(self):
        now=datetime(2026,11,17,12,0,0,tzinfo=timezone.utc)
        self.assertEqual(parse_retry_after("Tue, 17 Nov 2026 12:05:00 GMT",now=now),300)
    def test_invalid_or_unbounded(self):
        for value in (None,"", "-1", "secret", "9999999999"):
            self.assertIsNone(parse_retry_after(value))
    def test_429_preserves_safe_hint_without_retry(self):
        headers=Message()
        headers["Retry-After"]="300"
        calls=[]
        def fake(url, headers_in):
            calls.append(url)
            raise HTTPError(url,429,"rate limit",headers,None)
        with self.assertRaises(FutDBRateLimitError) as caught:
            request_page("players",key="test",transport=fake)
        self.assertEqual(caught.exception.retry_after_seconds,300)
        self.assertEqual(classify_error(caught.exception),"rate_limited")
        self.assertEqual(len(calls),1)
    def test_429_without_hint(self):
        def fake(url, headers_in):
            raise HTTPError(url,429,"rate limit",Message(),None)
        with self.assertRaises(FutDBRateLimitError) as caught:
            request_page("players",key="test",transport=fake)
        self.assertIsNone(caught.exception.retry_after_seconds)

if __name__=="__main__":
    unittest.main()
