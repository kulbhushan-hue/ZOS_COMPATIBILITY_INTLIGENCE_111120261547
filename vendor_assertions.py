"""Vendor-specific, explicitly attributed observations. No inferred certification.

These observations are independent of installed PTF inventory and of existing
compatibility records. They are visible in Source Monitor but never silently
replace a matching AMXT/CSV cell without a matching product release.
"""
from __future__ import annotations
import re
from quality import ptf_ids
from bs4 import BeautifulSoup

OS_VERSIONS=('3.2','3.1','2.5')

def _cells(tr):
    return [c.get_text(' ',strip=True) for c in tr.find_all(['td','th'],recursive=False)]

def extract_ibm_zos_requirements(body:bytes, url:str) -> list[dict]:
    """IBM z/OS 3.2 install requirements: extract named product->required level.
    It is a requirement table, NOT proof a specified installed release is ready.
    """
    if not ('ibm.com/docs' in url and ('zos/3.2' in url or 'zos/3.2.0' in url)):
        return []
    soup=BeautifulSoup(body,'lxml');out=[]
    for table in soup.find_all('table'):
        rows=table.find_all('tr')
        if len(rows)<2:continue
        headers=' '.join(' '.join(_cells(r)) for r in rows[:2]).casefold()
        if not ('product' in headers and ('level' in headers or 'ptf' in headers or 'required' in headers)):continue
        for tr in rows[1:]:
            c=_cells(tr)
            if len(c)<2:continue
            product=c[0].strip();requirement=' '.join(c[1:]).strip()
            if not (4<=len(product)<=170 and requirement and len(requirement)<=1500):continue
            if 'product' in product.casefold() and 'level' in requirement.casefold():continue
            out.append({'vendor':'IBM','product':product,'vrm':'Not stated',
                'zos_version':'3.2','compatibility':'Not asserted',
                'required_level':requirement,'maintenance_ids':', '.join(ptf_ids(requirement)),
                'source_url':url,
                'evidence_level':'IBM published minimum product level; installed release not verified'})
    return out[:150]

def extract_precisely_mfx_lifecycle(body:bytes,url:str)->list[dict]:
    """Capture minimum supported z/OS for MFX releases, not maximum compatibility."""
    if 'precisely.com/support/mfx-support-lifecycle-schedule' not in url:return []
    soup=BeautifulSoup(body,'lxml');out=[]
    for table in soup.find_all('table'):
        for tr in table.find_all('tr'):
            cells=_cells(tr)
            if len(cells)<3:continue
            # Entries include Release Designation | MFX Version Number | Release Date | Minimum z/OS.
            for i,x in enumerate(cells):
                if not re.fullmatch(r'\d+\.\d+\.\d+',x.strip()):continue
                if i==0 or i+2>=len(cells):continue
                min_os=cells[i+2].strip()
                if not re.fullmatch(r'\d+\.\d+',min_os):continue
                out.append({'vendor':'Precisely','product':'MFX for z/OS',
                  'vrm':x,'zos_version':'', 'compatibility':'Not asserted',
                  'required_level':'Minimum z/OS '+min_os,'source_url':url,
                  'evidence_level':'Published minimum OS only; no 3.2 certification inferred'})
    return out[:100]

def extract_precisely_ironstream_announcement(body:bytes,url:str)->list[dict]:
    if 'precisely.com' not in url or 'ironstream-for-ibm-z-now-compatible-with-zos-32' not in url:return []
    soup=BeautifulSoup(body,'lxml');txt=soup.get_text(' ',strip=True)
    if not re.search(r'Ironstream for IBM Z.{0,120}compatible with (?:IBM )?z/OS 3\.2',txt,re.I):return []
    return [{'vendor':'Precisely','product':'Ironstream for IBM Z','vrm':'Not stated',
             'zos_version':'3.2','compatibility':'Yes (release unspecified)',
             'source_url':url,'evidence_level':'Published product-level announcement; release not specified'}]

def extract_precisely_service_pack(body:bytes,url:str)->list[dict]:
    """Capture vendor-specific alphanumeric maintenance like SDF21QS, no assumptions."""
    if 'precisely.com' not in url or 'ironstream' not in url.lower():return []
    text=BeautifulSoup(body,'lxml').get_text(' ',strip=True)
    out=[]
    for match in re.finditer(r'\b(SDF[0-9A-Z]{4,8})\b',text,re.I):
        context=text[max(0,match.start()-100):match.end()+220]
        if not re.search(r'z\s*/\s*OS\s*(?:v)?3\.2',context,re.I):continue
        code=match.group(1).upper()
        if code not in [x['maintenance_id'] for x in out]:
            out.append({'vendor':'Precisely','product':'Ironstream for z/OS',
                'vrm':'Not stated','zos_version':'3.2','compatibility':'Not asserted',
                'maintenance_id':code,'source_url':url,'source_excerpt':context,
                'evidence_level':'PTF mentioned near z/OS 3.2; installation not verified'})
    return out[:60]



def extract_explicit_vendor_release_table(vendor:str, body:bytes, url:str)->list[dict]:
    """Only accept a table that explicitly gives product AND installed release and
    the target z/OS compatibility. Generic marketing text must not certify VRM.
    Used for Rocket/ASG public HTML documents when such a matrix exists.
    """
    if vendor not in ('Rocket','ASG'):return []
    soup=BeautifulSoup(body,'lxml');out=[]
    for table in soup.select('table'):
        trs=table.select('tr')
        if len(trs)<2:continue
        heads=[re.sub(r'\s+',' ',h).casefold() for h in _cells(trs[0])]
        def ix(terms):return next((i for i,h in enumerate(heads) if any(t in h for t in terms)),None)
        prod=ix(['product','software','solution'])
        vrm=ix(['release','version','vrm'])
        os_cols={v:next((i for i,h in enumerate(heads) if re.search(r'(?i)z\s*/\s*os\s*(?:v)?'+re.escape(v).replace(r'\.','[.r]')+r'\b',h)),None) for v in OS_VERSIONS}
        if prod is None or vrm is None or not any(i is not None for i in os_cols.values()):continue
        for tr in trs[1:]:
            cells=_cells(tr)
            if max(prod,vrm)>=len(cells):continue
            name=cells[prod].strip();release=cells[vrm].strip()
            if not (3<=len(name)<=150 and re.fullmatch(r'(?i)v?\d+(?:[.\-]\d+){0,4}',release)):continue
            for os,idx in os_cols.items():
                if idx is None or idx>=len(cells):continue
                val=cells[idx].strip().casefold()
                if val not in ('yes','no','supported','not supported','y','n','✔','✓'):continue
                out.append({'vendor':vendor,'product':name,'vrm':release,'zos_version':os,
                    'compatibility':'Yes' if val in ('yes','supported','y','✔','✓') else 'No',
                    'source_url':url,'evidence_level':'Explicit vendor table: product, release, z/OS; manual source verification recommended'})
    return out[:200]

def extract_extra_assertions(vendor:str,body:bytes,url:str)->list[dict]:
    if vendor=='IBM':return extract_ibm_zos_requirements(body,url)
    if vendor in ('Rocket','ASG'):return extract_explicit_vendor_release_table(vendor,body,url)
    if vendor=='Precisely':
        return extract_precisely_mfx_lifecycle(body,url)+extract_precisely_ironstream_announcement(body,url)+extract_precisely_service_pack(body,url)
    return []


def extract_official_document_tables(vendor: str, text: str, source_url: str) -> list[dict]:
    """Conservatively parse exported text/PDF pipe-delimited compatibility tables.

    Only explicit table cells are used; prose and nearby product names do not
    become certification. This is useful for authorized PDF/HTML-text exports.
    """
    if vendor not in ('IBM','BMC','Rocket','ASG'):
        return []
    lines=[line.strip() for line in text.splitlines() if line.strip()]
    results=[]
    # Real PDF text often doesn't preserve table structure. No row/cell separators
    # means no structured claim — the raw text is retained as contextual evidence.
    for index,line in enumerate(lines):
        if '|' not in line:continue
        cells=[x.strip() for x in line.strip('|').split('|')]
        if vendor=='IBM':
            if not ('ibm.com' in source_url and any('z/OS 3.2' in x or 'zos/3.2' in x for x in [source_url,text[:500]])):
                continue
            if len(cells)==2 and 5<=len(cells[0])<=140 and cells[1] and not cells[0].lower().startswith(('if you use','product','---')):
                # Prevent treating unrelated tables as a product requirement.
                headers=' '.join(lines[max(0,index-5):index]).casefold()
                if ('product level' in headers or ('ibm product' in headers and 'level' in headers)):
                    results.append({'vendor':'IBM','product':cells[0],'vrm':'Not stated',
                        'zos_version':'3.2','compatibility':'Not asserted',
                        'required_level':cells[1][:1000],
                        'maintenance_ids':', '.join(ptf_ids(cells[1])),
                        'source_url':source_url,'evidence_level':'Published IBM product minimum in exported table; not installed release certification'})
        elif vendor=='BMC':
            if len(cells)<2:continue
            m=re.fullmatch(r'(?i)z\s*/\s*OS\s*(?:V)?([235])[.R]([125])',cells[0])
            if not m:continue
            os=f'{m.group(1)}.{m.group(2)}'
            headers=[]
            for previous in reversed(lines[max(0,index-8):index]):
                if '|' in previous and ('mainframe' in previous.casefold() or 'operating system' in previous.casefold()):
                    headers=[h.strip() for h in previous.strip('|').split('|')]
                    break
            if len(headers)<len(cells) or not headers:continue
            note=next((cells[j] for j,h in enumerate(headers) if j<len(cells) and 'comment' in h.casefold()),'')
            for j,cell in enumerate(cells[1:],1):
                if j>=len(headers) or 'comment' in headers[j].casefold():continue
                val=cell.casefold()
                if val not in ('x','yes','no','y','n','✓','✔'):continue
                results.append({'vendor':'BMC','product':headers[j], 'vrm':'Not stated',
                    'zos_version':os,'compatibility':'No' if val in ('no','n') else 'Yes',
                    'required_level':note,'source_url':source_url,
                    'evidence_level':'Explicit BMC document table; release unspecified; manual review required'})
    # Duplicate PDF page headers/tables are common.
    unique={}
    for row in results:
        key=(row['vendor'],row['product'],row['vrm'],row['zos_version'],row.get('required_level',''))
        unique[key]=row
    return list(unique.values())[:200]
