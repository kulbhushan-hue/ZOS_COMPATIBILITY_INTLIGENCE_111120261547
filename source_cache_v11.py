"""Content-addressed, immutable raw-source cache for authorized public vendor documents.

Writes only response payloads and safe metadata; never stores cookies or credentials.
Offline replay verifies hashes. Local files cannot escape the source cache directory.
"""
import hashlib
import json
import re
from pathlib import Path
from bs4 import BeautifulSoup

MAX_BYTES=2_000_000

class ResponseCache:
    def __init__(self,root):
        self.root=Path(root)
        self.payloads=self.root/'objects'
        self.index=self.root/'manifest.jsonl'

    def save(self,vendor,url,final_url,content_type,body,fetched_at,item=None):
        if not isinstance(body,bytes) or len(body)>MAX_BYTES:
            raise ValueError('Document too large to cache')
        digest=hashlib.sha256(body).hexdigest()
        self.payloads.mkdir(parents=True,exist_ok=True)
        obj=self.payloads/digest
        if not obj.exists():
            tmp=obj.with_suffix('.tmp')
            tmp.write_bytes(body)
            tmp.replace(obj)
        record=dict(vendor=vendor,url=url,final_url=final_url,content_type=content_type,
                    fetched_at=fetched_at,sha256=digest,size=len(body),
                    contexts=(item or {}).get('contexts',[]))
        with self.index.open('a',encoding='utf-8') as f:
            f.write(json.dumps(record,ensure_ascii=False)+'\n')
        return record

    def entries(self):
        if not self.index.is_file():return
        latest={}
        for raw in self.index.read_text(encoding='utf-8').splitlines():
            try:
                item=json.loads(raw)
                key=(item['vendor'],item['url'])
                latest[key]=item
            except (ValueError,KeyError,TypeError):continue
        for key,entry in sorted(latest.items()):
            digest=entry.get('sha256','')
            if not re.fullmatch('[a-f0-9]{64}',digest):continue
            path=self.payloads/digest
            if not path.is_file():continue
            body=path.read_bytes()
            if len(body)>MAX_BYTES or hashlib.sha256(body).hexdigest()!=digest:continue
            yield entry,body


def describe_document(vendor,url,typ,body,digest,cache_status):
    pdf='pdf' in typ.lower() or body.startswith(b'%PDF')
    if pdf:
        return dict(vendor=vendor,url=url,format='PDF',response_sha256=digest,
                    cache_status=cache_status,bytes=len(body),html_tables=0,table_rows=0,
                    title='',script_tags=0,potential_dynamic_content='No',reason='PDF cached for local parsing')
    soup=BeautifulSoup(body,'lxml')
    tables=soup.find_all('table')
    scripts=soup.find_all('script')
    title=soup.title.get_text(' ',strip=True) if soup.title else ''
    content=soup.get_text(' ',strip=True)
    dynamic=bool(re.search(r'(?i)(__NEXT_DATA__|__NUXT__|ng-app|react-root|id=["\']app["\'])',body[:100000].decode('utf-8','replace')))
    if not dynamic and not tables and 'ibm.com/software/reports/compatibility/' in url.lower() and len(scripts)>=2 and len(content)<1800:
        dynamic=True
    reason=('Possible client-side rendering; examine cached HTML' if dynamic and not tables else
            'Tables available for parser review' if tables else
            'No HTML tables; inspect text, embedded data or PDF links')
    return dict(vendor=vendor,url=url,format='HTML',response_sha256=digest,
                cache_status=cache_status,bytes=len(body),html_tables=len(tables),
                table_rows=sum(len(t.find_all('tr')) for t in tables),
                title=title[:180],script_tags=len(scripts),potential_dynamic_content='Yes' if dynamic else 'No',reason=reason)
