import copy,json,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from datetime import timedelta
from feed_cache import FeedCache
from validate_feed import Rejected
from test_feed import fixture,NOW

# Test verifier stub is deliberately NOT authentication or a production signer.
def verifier(payload,auth):return auth=='TEST_ONLY'
class CacheChecks(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.path=Path(self.temp.name)/'research-cache.json'
        self.cache=FeedCache(self.path,verifier)
        self.cache.install(fixture(),'TEST_ONLY',NOW)
    def test_restart_original_expiry(self):
        self.assertEqual(FeedCache(self.path,verifier).current(NOW)['valid_until'],fixture()['valid_until'])
    def test_expired_cache_not_extended(self):
        with self.assertRaises(Rejected):self.cache.current(NOW+timedelta(days=1))
    def test_replay_survives_restart(self):
        with self.assertRaises(Rejected):FeedCache(self.path,verifier).install(fixture(),'TEST_ONLY',NOW)
    def test_failed_auth_preserves_cache(self):
        before=self.path.read_bytes();p=fixture();p['sequence']=3
        with self.assertRaises(Rejected):self.cache.install(p,'BAD',NOW)
        self.assertEqual(before,self.path.read_bytes())
    def test_interrupted_commit_preserves_cache(self):
        before=self.path.read_bytes();p=fixture();p['sequence']=3
        with patch('feed_cache.os.replace',side_effect=OSError('simulated disk failure')):
            with self.assertRaises(OSError):self.cache.install(p,'TEST_ONLY',NOW)
        self.assertEqual(before,self.path.read_bytes());self.assertEqual(list(self.path.parent.glob('*.pending.*')),[])
    def test_corruption_does_not_reset_version(self):
        self.path.write_text('{');p=fixture();p['sequence']=3
        with self.assertRaises(ValueError):self.cache.install(p,'TEST_ONLY',NOW)
        self.assertEqual(self.path.read_text(),'{')
    def test_atomic_new_version(self):
        p=fixture();p['sequence']=3;self.cache.install(p,'TEST_ONLY',NOW)
        self.assertEqual(self.cache.current(NOW)['sequence'],3)
    def test_cached_auth_rechecked(self):
        data=json.loads(self.path.read_text());data['authentication']='BAD';self.path.write_text(json.dumps(data))
        with self.assertRaises(Rejected):self.cache.current(NOW)
