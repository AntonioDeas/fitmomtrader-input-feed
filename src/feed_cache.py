"""Reference cache for updater fault tests; NOT installed in MT5.
Authentication is supplied by a separately tested verifier. No verifier default,
network, trading API, calendar generation, or risk-state access exists here.
"""
import json, os, tempfile
from pathlib import Path
from validate_feed import admit, Rejected

class FeedCache:
    def __init__(self, path, verify):
        self.path=Path(path)
        self.verify=verify

    def _read(self):
        if not self.path.exists(): return None
        data=json.loads(self.path.read_text())
        if set(data)!={'payload','authentication'}: raise Rejected('CACHE_FIELDS')
        if self.verify(data['payload'],data['authentication']) is not True:
            raise Rejected('CACHE_AUTHENTICATION')
        return data

    def install(self,payload,authentication,now):
        old=self._read()  # Corruption blocks replacement; never silently reset version.
        sequence=old['payload']['sequence'] if old else 0
        admitted=admit(payload,now,sequence,self.verify(payload,authentication))
        self.path.parent.mkdir(parents=True,exist_ok=True)
        fd,name=tempfile.mkstemp(prefix=self.path.name+'.pending.',dir=self.path.parent)
        try:
            with os.fdopen(fd,'w') as stream:
                json.dump({'payload':payload,'authentication':authentication},stream,sort_keys=True)
                stream.flush();os.fsync(stream.fileno())
            os.replace(name,self.path)  # Payload and high-water version commit together.
        finally:
            if os.path.exists(name):os.unlink(name)
        return admitted

    def current(self,now):
        data=self._read()
        if data is None:raise Rejected('NO_VALID_CACHE')
        p=data['payload']
        admit(p,now,p['sequence']-1,True) # Recheck original expiry; never renew it.
        return p
