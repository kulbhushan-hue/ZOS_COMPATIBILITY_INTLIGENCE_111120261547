"""Conservative extraction of vendor-specific, row-oriented support matrices.

All extracted rows are source assertions, never installed-system readiness.
Unknown release is preserved as evidence-only rather than a certified claim.
"""
from __future__ import annotations
import hashlib
import re
from bs4 import BeautifulSoup
from safe_extract_v8 import flat, os_versions, split_identity, match_label, valid_product_name, safe_install_status
from quality import ptf_ids, maintenance_availability

SUPPORTED={'IBM','BMC','Rocket','ASG','Precisely'}
YES={'x','✓','✔','yes','supported','compatible','certified'}
NO={'no','not supported','unsupported','not compatible'}


def _unique_inventory(vendor, label, byvendor):
    """Only exact normalized product identities; do not assign nearest match."""
    name, stated_release=split_identity(label)
    candidates=[]
    for item in byvendor.get(vendor,[]):
        ip=flat(item.get('product')); ir=flat(item.get('release'))
        base,embedded=split_identity(ip)
        base=base if embedded else ip
        if base.casefold()==name.casefold() and ir:
            candidates.append((ip,ir))
    return candidates,stated_release


def extract_vendor_matrix(body,vendor,url,byvendor,stamp):
    """Returns (compatibility, unpromoted observations).

    Matrix: OS in first column, product column names, X/checkmark statuses.
    Release assigned only if single unambiguous release in source heading or
    product header. Notes mentioning minimum supported release do not certify
    the inventory's release and remain in evidence-only observations.
    """
    if vendor not in SUPPORTED:return [],[]
    soup=BeautifulSoup(body,'lxml')
    for n in soup(['script','style','nav','footer']):n.decompose()
    digest=hashlib.sha256(body).hexdigest()
    good=[];review=[]
    for table in soup.find_all('table'):
        if table.find_parent('table'):continue
        trs=table.find_all('tr')
        if len(trs)<2:continue
        header=[flat(c.get_text(' ',strip=True)) for c in trs[0].find_all(['th','td'],recursive=False)]
        if len(header)<2:continue
        # Only row-oriented OS matrix; generic tables have no OS header.
        if not re.search(r'(?i)(operating system|mainframe|^os$|^z/os)',header[0]):continue
        for tr in trs[1:]:
            cells=[flat(c.get_text(' ',strip=True)) for c in tr.find_all(['th','td'],recursive=False)]
            if not cells or not re.search(r'(?i)z\s*/\s*os',cells[0]):continue
            oss=os_versions(cells[0]);
            if not oss:continue
            for j in range(1,min(len(cells),len(header))):
                flag=cells[j].casefold()
                # Only unambiguous entire-cell indicators; ignore asterisk/footnote statuses.
                status='Yes' if flag in YES else 'No' if flag in NO else ''
                if not status or not valid_product_name(header[j]):continue
                inventory,header_release=_unique_inventory(vendor,header[j],byvendor)
                # Source-specific scope: release in product heading or exact unique inventory
                # plus release text in a nearby heading, NOT a generic version minimum note.
                release=header_release
                if not release:
                    for h in table.find_all_previous(['h1','h2','h3'],limit=3):
                        ht=flat(h.get_text(' ',strip=True))
                        m=re.search(r'(?i)(?:release|version)\s+v?(\d+(?:\.\d+){1,3})\b',ht)
                        if m and len(inventory)==1 and header[j].casefold() in ht.casefold():release=m.group(1);break
                if len(inventory)==1 and release:
                    ip,ir=inventory[0]
                    if release.lstrip('vV')!=ir.lstrip('vV'):
                        release='' # source release does not match known inventory
                else:
                    release=''
                for os in oss:
                    record=dict(vendor=vendor,product=header[j],release=release,
                       zos_version=os,compatibility=status,
                       evidence_level='Source OS-by-product matrix; explicit cell',
                       source_url=url,source_excerpt=' | '.join(cells)[:700],
                       source_timestamp=stamp,document_sha256=digest,
                       match_status=match_label(vendor,header[j],release,byvendor))
                    if release:
                        good.append(record)
                    else:
                        review.append(dict(vendor=vendor,product=header[j],release='Not established',
                          zos_version=os,assertion=status,observation_type='Release-unspecified OS support',
                          source_url=url,source_excerpt=(header[j]+' | '+' | '.join(cells))[:700],
                          source_timestamp=stamp,reason='Exact installed product release not established by source'))
    # exact source-cell duplicates only
    good=list({(x['vendor'],x['product'],x['release'],x['zos_version'],x['compatibility'],x['source_url']):x for x in good}.values())
    review=list({(x['vendor'],x['product'],x['zos_version'],x['assertion'],x['source_url']):x for x in review}.values())
    return good,review


def extract_ibm_report_table(body,url,byvendor,stamp):
    """IBM SPCR variant: unique release heading + OS column, status column.
    Requirements with only a listed OS and no support status are evidence-only.
    """
    soup=BeautifulSoup(body,'lxml');digest=hashlib.sha256(body).hexdigest();claims=[];notes=[]
    headings=[flat(h.get_text(' ',strip=True)) for h in soup.find_all(['h1','h2','h3'])]
    matches=[]
    for item in byvendor.get('IBM',[]):
        p=flat(item.get('product'));r=flat(item.get('release'))
        if not p or not r:continue
        pbase,_=split_identity(p)
        if any(re.search(r'(?<!\w)'+re.escape(pbase)+r'\s+(?:version\s+|v)?'+re.escape(r.lstrip('vV'))+r'(?![.\d])',h,re.I) for h in headings):
            matches.append((p,r))
    matches=list(set(matches))
    if len(matches)!=1:return [],[]
    p,r=matches[0]
    for table in soup.find_all('table'):
        if table.find_parent('table'):continue
        trs=table.find_all('tr')
        if len(trs)<2:continue
        head=[flat(c.get_text(' ',strip=True)).casefold() for c in trs[0].find_all(['th','td'],recursive=False)]
        osidx=next((i for i,h in enumerate(head) if h in ('operating system','operating systems','os','platform','supported operating systems')),None)
        if osidx is None:continue
        stidx=next((i for i,h in enumerate(head) if any(t in h for t in ('support status','compatibility','supported','status'))),None)
        for row in trs[1:]:
            values=[flat(c.get_text(' ',strip=True)) for c in row.find_all(['td','th'],recursive=False)]
            if osidx>=len(values) or not re.search(r'(?i)z\s*/\s*os',values[osidx]):continue
            for os in os_versions(values[osidx]):
                status=''
                if stidx is not None and stidx<len(values):
                    flag=values[stidx].casefold()
                    status='Yes' if flag in YES else 'No' if flag in NO else ''
                if status:
                    claims.append(dict(vendor='IBM',product=p,release=r,zos_version=os,compatibility=status,
                        evidence_level='IBM SPCR exact product/release + support-status row',
                        source_url=url,source_excerpt=' | '.join(values)[:700],source_timestamp=stamp,
                        document_sha256=digest,match_status=match_label('IBM',p,r,byvendor)))
                else:
                    notes.append(dict(vendor='IBM',product=p,release=r,zos_version=os,assertion='Listed',
                       observation_type='OS listed without explicit support status',source_url=url,
                       source_excerpt=' | '.join(values)[:700],source_timestamp=stamp,
                       reason='No explicit supported/unsupported value'))
    return claims,notes
