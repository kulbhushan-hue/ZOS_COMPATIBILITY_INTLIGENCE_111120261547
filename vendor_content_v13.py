"""Source-specific evidence extraction from documented, public vendor HTML.

Only explicit product/version/OS cells become exact compatibility claims.
Unsupported or release-unspecified statements remain review observations.
"""
from __future__ import annotations
import re
from bs4 import BeautifulSoup
from safe_extract_v8 import flat

ZOS = ('2.5', '3.1', '3.2')

def _obs(vendor,product,release,zos,assertion,kind,url,excerpt,stamp,reason):
    return dict(vendor=vendor, product=product,release=release or 'Not established',
                zos_version=zos or 'Not stated',assertion=assertion,
                observation_type=kind,source_url=url,source_excerpt=flat(excerpt)[:700],
                source_timestamp=stamp,reason=reason)

def _rows(table):
    return [[flat(c.get_text(' ',strip=True)) for c in tr.find_all(('th','td'),recursive=False)]
            for tr in table.find_all('tr')]

def _match_release(byvendor, vendor, product, release):
    def norm(x):return re.sub(r'[^a-z0-9]','',str(x).casefold())
    return any(norm(i.get('product'))==norm(product) and str(i.get('release','')).lstrip('vV')==str(release).lstrip('vV')
               for i in byvendor.get(vendor,[]))

def extract_v13(body,vendor,url,byvendor,stamp):
    """Return (verified compatibility, release-level observations, PTF rows).
    PTF rows are returned only when the exact source release matches inventory;
    other maintenance is retained as evidence-only observations.
    """
    if vendor not in ('Precisely','BMC','VANGUARD Integrity Prof.','IBM','Rocket','ASG','Action Software International'):
        return [],[],[]
    soup=BeautifulSoup(body,'lxml')
    for n in soup(['script','style','nav','footer']):n.decompose()
    text=flat(soup.get_text(' ',strip=True))
    title=flat(soup.title.get_text(' ',strip=True)) if soup.title else ''
    h=' '.join(x.get_text(' ',strip=True) for x in soup.find_all(['h1','h2','h3']))
    claims=[];notes=[];ptfs=[]
    if vendor=='Precisely':
        # Release-specific lifecycle data: 'Minimum z/OS 3.1' does NOT certify 3.2.
        if 'mfx-support-lifecycle' in url.lower() or ('MFX Version Number' in text and 'Minimum z/OS' in text):
            for table in soup.find_all('table'):
                rr=_rows(table)
                header=' '.join(' '.join(row) for row in rr[:4]).lower()
                if not ('minimum' in header and ('mfx' in header or 'version number' in header)):continue
                for row in rr[1:]:
                    rel=next((x for x in row if re.fullmatch(r'3\.1\.\d+',x)),None)
                    os=next((x for x in row if x in ZOS),None)
                    if rel and os:
                        notes.append(_obs(vendor,'MFX for z/OS',rel,os,'Minimum supported OS',
                            'Published minimum OS (not OS 3.2 certification)',url,' | '.join(row),stamp,
                            'Minimum OS does not prove compatibility with a newer z/OS version'))
        # 2026 announcement: exact product family support but version unspecified.
        if ('ironstream-for-ibm-z-now-compatible' in url.lower() or
            ('Ironstream for IBM Z' in h and re.search(r'compatible with (?:IBM )?z/OS\s*3\.2',text,re.I))):
            if re.search(r'compatible with (?:IBM )?z/OS\s*3\.2',text,re.I):
                notes.append(_obs(vendor,'Ironstream for IBM Z','', '3.2','Yes',
                    'Vendor announcement; specific product release not stated',url,
                    re.search(r'.{0,70}compatible with (?:IBM )?z/OS\s*3\.2.{0,140}',text,re.I).group(0),stamp,
                    'Product release not stated; not promoted to exact inventory compatibility'))
        # Do not interpret 'PTF' in a general announcement as applicable to any installed release.
        if ('service-pack-notice' in url.lower() or 'Ironstream for z/OS v2.1.12 Service Pack Notice' in h):
            if re.search(r'Ironstream for z/OS\s*v?2\.1\.12',text,re.I):
                product='Ironstream for z/OS';release='2.1.12'
                for table in soup.find_all('table'):
                    rr=_rows(table)
                    if not rr or not any('PTF ID' in cell for row in rr[:2] for cell in row):continue
                    for row in rr[1:]:
                        if not row:continue
                        ptf=next((x for x in row if re.fullmatch(r'SDF[A-Z0-9]{4,6}',x,re.I)),None)
                        if not ptf:continue
                        excerpt=' | '.join(row)
                        mentioned_os=re.search(r'(?i)z/OS\s*(?:v)?(3\.2|3\.1|2\.5)',excerpt)
                        os=mentioned_os.group(1) if mentioned_os else 'Not stated'
                        notes.append(_obs(vendor,product,release,os,ptf.upper(),
                            'Published service-pack PTF (applicability unconfirmed)',url,excerpt,stamp,
                            'Service pack announcement is not proof of a required or installed PTF'))
                        if _match_release(byvendor,vendor,product,release):
                            ptfs.append(dict(vendor=vendor,product=product,release=release,zos_version=os,
                                ptf_id=ptf.upper(),maintenance_type='PTF',publication_status='Published / available — source statement',
                                installation_status='Unknown',component='',source_url=url,source_excerpt=excerpt[:700],
                                source_timestamp=stamp,evidence_level='Vendor service pack publication; applicability needs verification',
                                match_status='Exact product/release inventory match'))
    if vendor=='BMC':
        # Preserve BMC's actual minimum-supported-product-version explanation.
        for table in soup.find_all('table'):
            rr=_rows(table)
            if len(rr)<2 or not rr[0] or not re.search(r'(?i)operating systems?\s*/?\s*mainframe',rr[0][0]):continue
            comment_idx=next((i for i,h in enumerate(rr[0]) if 'comment' in h.casefold()),len(rr[0]))
            products=rr[0][1:comment_idx]
            for row in rr[1:]:
                if not row:continue
                m=re.fullmatch(r'z\s*/\s*OS\s*(\d+\.\d+)',row[0],re.I)
                if not m:continue
                os=m.group(1)
                comments=' '.join(row[comment_idx:])
                minimum=re.search(r'support started in version\s+([\d.]+)(?:\s+patch\s+(\d+))?',comments,re.I)
                if not minimum:continue  # V10 already preserves release-unspecified OS cells
                for i,product in enumerate(products,1):
                    if i>=len(row) or row[i].strip().upper() not in ('X','✓','✔'):continue
                    extra=f'Minimum product version {minimum.group(1)}' if minimum else 'Version not specified'
                    notes.append(_obs(vendor,product,'',os,'Supported',
                        'BMC product matrix; minimum release caveat',url,
                        f'{product} | {row[0]} | {row[i]} | {comments}',stamp,
                        extra+'; does not verify the exact installed release'))
    if vendor=='VANGUARD Integrity Prof.':
        # Vanguard states explicitly 'Minimum Tested z/OS' and 'Maximum Tested z/OS'.
        for table in soup.find_all('table'):
            rr=_rows(table)
            if not rr:continue
            header=[x.casefold() for x in rr[0]]
            if not any('minimum tested' in x for x in header) or not any('maximum tested' in x for x in header):continue
            try:
                pi=next(i for i,x in enumerate(header) if 'product' in x)
                vi=next(i for i,x in enumerate(header) if x=='version')
                mi=next(i for i,x in enumerate(header) if 'minimum tested' in x)
                ma=next(i for i,x in enumerate(header) if 'maximum tested' in x)
            except StopIteration:continue
            for row in rr[1:]:
                if len(row)<=max(pi,vi,mi,ma):continue
                product,release,low,high=(row[z] for z in (pi,vi,mi,ma))
                if not (re.fullmatch(r'\d+\.\d+',low) and re.fullmatch(r'\d+\.\d+',high)):continue
                for os in ZOS:
                    if tuple(map(int,low.split('.')))<=tuple(map(int,os.split('.')))<=tuple(map(int,high.split('.'))):
                        notes.append(_obs(vendor,product,release,os,'Tested range',
                            'Published minimum/maximum tested z/OS',url,' | '.join(row),stamp,
                            'Published tested range; reconcile source identity with inventory before certifying'))
    if vendor=='Rocket' and ('TMON Modernization' in h or 'tmon-modernization' in url.lower()):
        if re.search(r'TMON support for IBM.{0,30}z/OS.{0,20}3\.2',text,re.I):
            notes.append(_obs(vendor,'TMON','', '3.2','Support announced',
                'Rocket TMON family announcement (release not stated)',url,
                re.search(r'.{0,40}TMON support for IBM.{0,30}z/OS.{0,20}3\.2.{0,90}',text,re.I).group(0),stamp,
                'The announcement is not an installed-version certification'))
    if vendor=='Action Software International':
        for table in soup.find_all('table'):
            rr=_rows(table)
            if len(rr)<2:continue
            header=' | '.join(rr[0]).casefold()
            if not ('release' in header and 'system compatibility' in header):continue
            for row in rr[1:]:
                if len(row)<2:continue
                m=re.fullmatch(r'\s*((?:event|uss)ACTION)\s*(\d+\.\d+)\s*',row[0],re.I)
                if not m:continue
                product,release=m.group(1),m.group(2)
                compat=next((x for x in row if 'z/OS' in x),None)
                if not compat:continue
                boundaries=re.findall(r'z\s*/\s*OS\s*(\d+\.\d+)',compat,re.I)
                if len(boundaries)<2:continue
                low,high=map(lambda x:tuple(map(int,x.split('.'))),boundaries[:2])
                for os in ZOS:
                    if low<=tuple(map(int,os.split('.')))<=high:
                        notes.append(_obs(vendor,product,release,os,'Published compatibility range',
                            'Release history OS compatibility range',url,' | '.join(row),stamp,
                            'Date and end-of-service status must be reviewed independently'))
    # Nothing about empty or IBM SPCR error-page shells implies support.
    dedup=lambda a,ks:list({tuple(r.get(k,'') for k in ks):r for r in a}.values())
    return (claims,dedup(notes,('vendor','product','release','zos_version','assertion','source_url','source_excerpt')),
            dedup(ptfs,('vendor','product','release','zos_version','ptf_id','source_url')))
