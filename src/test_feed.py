import copy, unittest
from datetime import datetime,timezone,timedelta
from validate_feed import admit,Rejected
NOW=datetime(2026,11,27,20,tzinfo=timezone.utc)
def fixture():
    return dict(schema='FMT_INPUTS_1',sequence=2,issued='2026-11-27T19:00:00Z',valid_from='2026-11-27T00:00:00Z',valid_until='2026-11-28T00:00:00Z',scope={'server':'AMPGlobalUSA-Demo','symbol':'MNQZ26','currency':'USD','account_type':'DEMO'},strategy='SOURCE_ALIGNED_R2_ORIGINAL_EXITS',policy={'commission_rt_usd':1.22,'slippage_ticks_each_side':2,'margin_floor_usd':100,'flatten_minutes':20},days=[dict(date=f'202611{d}',allow=False,close_minute=0,session_verified=False,news_verified=False,named_event=False) for d in range(26,30)],offsets=[{'from':'2026-11-27T00:00:00Z','until':'2026-11-28T00:00:00Z','minutes':0}],evidence=[dict(kind=k,url='https://example.invalid/TEST_ONLY',retrieved='2026-11-27T18:00:00Z',sha256='0'*64) for k in ['exchange_sessions','named_news','broker_offset','broker_margin','cost_basis']])
class Checks(unittest.TestCase):
    def rejected(self,p,**kw):
        with self.assertRaises((Rejected,ValueError)):admit(p,NOW,1,**{'signature_verified':True,**kw})
    def test_blocked_unknown_session_valid(self): self.assertEqual(admit(fixture(),NOW,1,True)['sequence'],2)
    def test_unsigned(self): self.rejected(fixture(),signature_verified=False)
    def test_rollback(self):
        p=fixture();p['sequence']=1;self.rejected(p)
    def test_expired(self):
        p=fixture();p['valid_until']='2026-11-27T20:00:00Z';self.rejected(p)
    def test_future_issued(self):
        p=fixture();p['issued']='2026-11-27T21:00:00Z';self.rejected(p)
    def test_forever(self):
        p=fixture();p['valid_until']='2099-01-01T00:00:00Z';self.rejected(p)
    def test_live(self):
        p=fixture();p['scope']['account_type']='REAL';self.rejected(p)
    def test_risk_injection(self):
        p=fixture();p['risk_cap']=1000;self.rejected(p)
    def test_policy_change(self):
        p=fixture();p['policy']['commission_rt_usd']=0;self.rejected(p)
    def test_missing_evidence(self):
        p=fixture();p['evidence'].pop();self.rejected(p)
    def test_calendar_gap(self):
        p=fixture();p['days'].pop(1);self.rejected(p)
    def test_duplicate_day(self):
        p=fixture();p['days'].append(copy.deepcopy(p['days'][-1]));self.rejected(p)
    def test_offset_gap(self):
        p=fixture();p['offsets'][0]['until']='2026-11-27T19:00:00Z';self.rejected(p)
    def test_unknown_allowed(self):
        p=fixture();p['days'][1]['allow']=True;self.rejected(p)
    def test_news_day_allowed(self):
        p=fixture();p['days'][1].update(allow=True,session_verified=True,news_verified=True,named_event=True,close_minute=1020);self.rejected(p)
    def test_early_close_allowed(self):
        p=fixture();p['days'][1].update(allow=True,session_verified=True,news_verified=True,close_minute=780);self.rejected(p)
    def test_no_mutation_on_rejection(self):
        p=fixture();p['risk_state']={'day':0};before=copy.deepcopy(p);self.rejected(p);self.assertEqual(p,before)
if __name__=='__main__': unittest.main()
