"""Research admission contract only. NOT an EA/updater; no network or order API.
Caller must verify detached signature against a pinned publisher key BEFORE admission.
Evidence hashes provide provenance, not proof that source interpretation is correct.
"""
from datetime import datetime, timezone, timedelta
import hashlib, json, math

class Rejected(ValueError): pass

def require(ok, reason):
    if not ok: raise Rejected(reason)

def stamp(s):
    require(isinstance(s,str) and s.endswith('Z'), 'UTC_REQUIRED')
    return datetime.fromisoformat(s.replace('Z','+00:00'))

def number(x): return type(x) in (int,float) and math.isfinite(x)

def admit(p, now, current_sequence, signature_verified=False):
    require(signature_verified is True, 'SIGNATURE_NOT_VERIFIED')
    require(now.tzinfo is not None and now.utcoffset()==timedelta(0), 'UTC_REQUIRED')
    require(set(p)=={'schema','sequence','issued','valid_from','valid_until','scope','strategy','policy','days','offsets','evidence'}, 'SCHEMA_FIELDS')
    require(p['schema']=='FMT_INPUTS_1', 'SCHEMA_VERSION')
    require(type(p['sequence']) is int and p['sequence']>current_sequence, 'REPLAY_OR_ROLLBACK')
    require(p['scope']=={'server':'AMPGlobalUSA-Demo','symbol':'MNQZ26','currency':'USD','account_type':'DEMO'}, 'SCOPE_MISMATCH')
    require(p['strategy']=='SOURCE_ALIGNED_R2_ORIGINAL_EXITS', 'STRATEGY_CHANGE')
    require(p['policy']=={'commission_rt_usd':1.22,'slippage_ticks_each_side':2,'margin_floor_usd':100,'flatten_minutes':20}, 'POLICY_CHANGE_REQUIRES_REVIEW')
    issued,start,end=map(stamp,[p['issued'],p['valid_from'],p['valid_until']])
    require(issued<=now and now-issued<=timedelta(hours=24), 'ISSUE_FRESHNESS')
    require(start<=now<end and start<=issued<end, 'EXPIRED_OR_NOT_CURRENT')
    require(end-issued<=timedelta(hours=72), 'UNBOUNDED_COVERAGE')
    evidence={}
    require(isinstance(p['evidence'],list), 'EVIDENCE_REQUIRED')
    for e in p['evidence']:
        require(set(e)=={'kind','url','retrieved','sha256'}, 'EVIDENCE_FIELDS')
        require(e['kind'] not in evidence and e['url'].startswith('https://'), 'EVIDENCE_SOURCE')
        h=e['sha256'];require(isinstance(h,str) and len(h)==64 and all(c in '0123456789abcdef' for c in h), 'EVIDENCE_HASH')
        retrieved=stamp(e['retrieved']);require(retrieved<=issued and issued-retrieved<=timedelta(hours=24), 'EVIDENCE_STALE')
        evidence[e['kind']]=e
    require(set(evidence)=={'exchange_sessions','named_news','broker_offset','broker_margin','cost_basis'}, 'EVIDENCE_INCOMPLETE')
    require(isinstance(p['offsets'],list) and p['offsets'], 'OFFSET_MISSING')
    last=None
    for o in p['offsets']:
        require(set(o)=={'from','until','minutes'}, 'OFFSET_FIELDS')
        a,z=stamp(o['from']),stamp(o['until'])
        require(a<z and type(o['minutes']) is int and -840<=o['minutes']<=840, 'OFFSET_INVALID')
        if last is not None: require(a==last,'OFFSET_GAP_OR_OVERLAP')
        else: require(a<=start,'OFFSET_START_GAP')
        last=z
    require(last>=end,'OFFSET_END_GAP')
    require(isinstance(p['days'],list) and p['days'], 'CALENDAR_MISSING')
    dates=[]
    for d in p['days']:
        require(set(d)=={'date','allow','close_minute','session_verified','news_verified','named_event'}, 'DAY_FIELDS')
        day=datetime.strptime(d['date'],'%Y%m%d').date();dates.append(day)
        require(type(d['allow']) is bool and type(d['session_verified']) is bool and type(d['news_verified']) is bool and type(d['named_event']) is bool,'DAY_TYPES')
        require(type(d['close_minute']) is int and 0<=d['close_minute']<=1440,'CLOSE_INVALID')
        if d['allow']:
            require(d['session_verified'] and d['news_verified'] and not d['named_event'] and d['close_minute']==1020,'UNVERIFIED_OR_EXCLUDED_SESSION')
    require(dates==sorted(set(dates)),'DUPLICATE_OR_UNORDERED_DAYS')
    require(all(b-a==timedelta(days=1) for a,b in zip(dates,dates[1:])),'CALENDAR_GAP')
    # Conservative UTC padding covers ET calendar date and next named trading day.
    require(dates[0]<=start.date()-timedelta(days=1) and dates[-1]>=end.date()+timedelta(days=1),'CALENDAR_COVERAGE')
    return {'sequence':p['sequence'],'valid_until':p['valid_until'],'digest':hashlib.sha256(json.dumps(p,sort_keys=True,separators=(',',':')).encode()).hexdigest()}
