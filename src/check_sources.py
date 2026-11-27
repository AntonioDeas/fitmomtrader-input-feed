"""Cloud evidence collection only. Does not produce or authorize trading inputs."""
from datetime import datetime, timezone
from urllib.request import Request, urlopen
from urllib.parse import urlparse
import hashlib,json,os
from html.parser import HTMLParser

class TextOnly(HTMLParser):
    def __init__(self): super().__init__(); self.parts=[]
    def handle_data(self,data): self.parts.append(data)

def visible_text(body):
    parser=TextOnly(); parser.feed(body.decode('utf-8', errors='strict'))
    return ' '.join(' '.join(parser.parts).split())

def monthly_sources(now):
    year,month=now.year,now.month
    next_year,next_month=(year+1,1) if month==12 else (year,month+1)
    return {f'named_news_bls_{y}_{m:02d}':f'https://www.bls.gov/schedule/{y}/{m:02d}_sched_list.htm' for y,m in [(year,month),(next_year,next_month)]}

SOURCES={
 'named_news_bls':'https://www.bls.gov/schedule/news_release/bls.ics',
 'named_news_fomc':'https://www.federalreserve.gov/monetarypolicy/fomccalendars.htm',
 'broker_margin':'https://www.ampfutures.com/trading-info/margins',
 'exchange_sessions':'https://www.cmegroup.com/trading-hours.html',
}
def collect(url):
    request=Request(url,headers={'User-Agent':'FitMomTraderResearchSourceCheck/0.1 (public schedule verification; no trading requests)'})
    try:
        with urlopen(request,timeout=20) as response:
            final=response.geturl()
            if urlparse(final).scheme!='https' or urlparse(final).hostname!=urlparse(url).hostname:
                raise ValueError('Unexpected source redirect')
            body=response.read(2_000_001)
            if len(body)>2_000_000:raise ValueError('Source exceeds bounded response size')
            if not body:raise ValueError('Empty source')
            return {'url':url,'final_url':final,'fetch_ok':True,'status':response.status,'bytes':len(body),'sha256':hashlib.sha256(body).hexdigest(),'content_type':response.headers.get('Content-Type',''),'semantic_validation':'NOT_IMPLEMENTED_NOT_TRADING_AUTHORITY'}
    except Exception as e:
        return {'url':url,'fetch_ok':False,'error':type(e).__name__+': '+str(e)[:240],'semantic_validation':'UNAVAILABLE'}
def main():
    sources=dict(SOURCES); sources.update(monthly_sources(datetime.now(timezone.utc)))
    result={'checked_utc':datetime.now(timezone.utc).isoformat(),'trading_authorized':False,'feed_published':False,'status':'EVIDENCE_COLLECTION_ONLY','sources':{k:collect(u) for k,u in sources.items()},'unresolved':['Exact product-session parsing and completeness','Named-news event coverage/classification','Supported broker-offset evidence','Authenticated publisher and native admission/cache integration']}
    print(json.dumps(result,indent=2))
    if os.environ.get('GITHUB_STEP_SUMMARY'):
        with open(os.environ['GITHUB_STEP_SUMMARY'],'a') as f:
            f.write('# Input-source collection — not a trading refresh\n\nNo operating inputs were published. Production trading authorization is unchanged.\n\n')
            for k,v in result['sources'].items():f.write('- '+k+': '+('retrieved; semantic validation pending' if v['fetch_ok'] else 'FETCH FAILED: '+v.get('error','unknown'))+'\n')
    return 0 if all(v['fetch_ok'] for v in result['sources'].values()) else 1
if __name__=='__main__':raise SystemExit(main())
