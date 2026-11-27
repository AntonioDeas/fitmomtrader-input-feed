import unittest
from unittest.mock import patch
from datetime import datetime, timezone
from io import BytesIO
from urllib.error import HTTPError
from check_sources import collect, monthly_sources

class Response(BytesIO):
    status=200
    headers={'Content-Type':'text/html'}
    def geturl(self): return 'https://www.bls.gov/example'

class SourceChecks(unittest.TestCase):
    def test_december_rollover(self):
        sources=monthly_sources(datetime(2026,12,31,tzinfo=timezone.utc))
        self.assertEqual(set(sources),{'named_news_bls_2026_12','named_news_bls_2027_01'})
    def test_success_not_authority(self):
        with patch('check_sources.urlopen',return_value=Response(b'public source')):
            result=collect('https://www.bls.gov/example')
        self.assertTrue(result['fetch_ok'])
        self.assertEqual(result['semantic_validation'],'NOT_IMPLEMENTED_NOT_TRADING_AUTHORITY')
    def test_http403_remains_failure(self):
        with patch('check_sources.urlopen',side_effect=HTTPError('https://www.bls.gov/example',403,'Forbidden',{},None)):
            result=collect('https://www.bls.gov/example')
        self.assertFalse(result['fetch_ok'])
        self.assertEqual(result['semantic_validation'],'UNAVAILABLE')
    def test_empty_rejected(self):
        with patch('check_sources.urlopen',return_value=Response(b'')):
            self.assertFalse(collect('https://www.bls.gov/example')['fetch_ok'])
    def test_redirect_rejected(self):
        with patch('check_sources.urlopen',return_value=Response(b'data')):
            self.assertFalse(collect('https://other.invalid/example')['fetch_ok'])
    def test_oversize_rejected(self):
        with patch('check_sources.urlopen',return_value=Response(b'x'*2_000_001)):
            self.assertFalse(collect('https://www.bls.gov/example')['fetch_ok'])
