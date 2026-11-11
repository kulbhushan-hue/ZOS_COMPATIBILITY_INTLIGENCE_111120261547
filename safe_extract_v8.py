"""Conservative source-scoped HTML extraction for V8.

Never use a URL's inventory context as a row's product identity. An absent
product/release/OS is an unknown, not permission to infer it from surrounding
unrelated rows. Linked maintenance sections are bounded by anchor identities.
"""
import hashlib
import re
from urllib.parse import urljoin, urldefrag
from bs4 import BeautifulSoup, Tag
from quality import ptf_ids, maintenance_availability, installation_status, match_key

OS_RE=re.compile(r'(?i)\bz\s*/\s*OS\s*(?:v|version\s*)?([235])(?:\.|\s*r)([125])\b')
FIXCAT_RE=re.compile(r'(?i)TargetSystem-RequiredService\.z/OS\.V([235])R([125])')
VER_RE=re.compile(r'(?i)^(.*?)\s+v?(\d+(?:\.\d+){0,3})(?:\s*\([^)]*\))?$')
MAINT_RE=re.compile(r'(?i)\b(?:ptf|apar|usermod|sysmod|fixcat|fmid|maintenance|service)\b')
INVALID_PRODUCT_RE=re.compile(r'(?i)^(?:yes|no|in progress|n/a|unknown|unverified|pending)(?:\s+(?:ptfs?|info|additional|more|details))*$')
ANY_FIXCAT_RE=re.compile(r'(?i)TargetSystem-RequiredService\.([^\s,;<>]+)')

def valid_product_name(name):
 name=flat(name)
 return bool(len(name)>2 and len(name)<180 and not INVALID_PRODUCT_RE.fullmatch(name) and name.casefold() not in ('product','release','version','z/os'))

def scoped_fixcat_version(text):
 """Only a z/OS FIXCAT establishes z/OS applicability. Other FIXCATs must not
 be interpreted as z/OS, even if the surrounding page mentions old releases.
 Returns (versions, has_fixcat)."""
 cats=ANY_FIXCAT_RE.findall(flat(text))
 if not cats:return [],False
 found=sorted({f'{a}.{b}' for c in cats for a,b in FIXCAT_RE.findall('TargetSystem-RequiredService.'+c)})
 return found,True


def flat(s):return re.sub(r'\s+',' ',str(s or '')).strip()
def os_versions(s):return sorted(set([f'{a}.{b}' for a,b in OS_RE.findall(flat(s))]+[f'{a}.{b}' for a,b in FIXCAT_RE.findall(flat(s))]))
def status(s):
 t=flat(s).casefold()
 if t in ('yes','y','supported','compatible','certified','✔','✓'):return 'Yes'
 if t in ('no','n','unsupported','not compatible','not supported'):return 'No'
 if t in ('in progress','under evaluation','pending'):return 'In Progress'
 return ''

def cell_status(cell):
 direct=flat(' '.join(str(n) for n in cell.find_all(string=True,recursive=False)))
 # Compatibility flag may be followed by a PTF link. Only the direct cell text
 # is authoritative; linked maintenance label is not itself a status.
 if status(direct):return status(direct)
 if direct.casefold() in ('yes -','no -','in progress -'):return status(direct[:-2])
 return status(cell.get_text(' ',strip=True))

def split_identity(label,release_hint=''):
 label=flat(label); release_hint=flat(release_hint)
 if release_hint:
  return label,release_hint
 m=VER_RE.match(label)
 return (flat(m.group(1)),m.group(2)) if m and ('.' in m.group(2) or re.search(r'(?i)\s+v'+re.escape(m.group(2))+r'$',label)) else (label,'')

def inventory_identity(vendor,label,byvendor,release_hint=''):
 """Match only the identity explicitly printed within the SAME table cell/section.

 Avoid substring match: `ACF2 16.0` cannot match `CA 7 12.0`.
 """
 p,r=split_identity(label,release_hint)
 if not p:return '',''
 choices=[]
 for x in byvendor.get(vendor,[]):
  ip,ir=flat(x.get('product')),flat(x.get('release'))
  if match_key(vendor,p,r)==match_key(vendor,ip,ir):
   choices.append((ip,ir))
 if choices:
  return p,r  # still retain printed product as evidence
 return p,r

def match_label(vendor,product,release,byvendor):
 if not product or not release:return 'Release unspecified'
 def key(p,r):
  name,embedded=split_identity(p)
  return match_key(vendor,name if embedded and embedded.lstrip('vV')==flat(r).lstrip('vV') else p,r)
 actual=key(product,release)
 return 'Exact inventory match' if any(key(x.get('product'),x.get('release'))==actual for x in byvendor.get(vendor,[])) else 'No exact inventory match'

def parse_tables(soup,vendor,url,byvendor,stamp,digest):
 results=[]
 for table in soup.find_all('table'):
  # Nested tables must not be traversed repeatedly via outer table.
  if table.find_parent('table'):continue
  rows=table.find_all('tr')
  if not rows:continue
  header=[]; oscols={}; pcol=None; rcol=None
  for tr in rows:
   cells=tr.find_all(['th','td'],recursive=False)
   values=[flat(c.get_text(' ',strip=True)) for c in cells]
   if not values:continue
   candidate={i:os_versions(v) for i,v in enumerate(values) if os_versions(v)}
   if candidate and any('product' in v.casefold() or 'release' in v.casefold() or 'version' in v.casefold() for v in values):
    header=values;oscols=candidate
    pcol=next((i for i,v in enumerate(values) if 'product' in v.casefold() or 'description' in v.casefold()),None)
    rcol=next((i for i,v in enumerate(values) if v.casefold() in ('release','version','vrm')),None)
    continue
   if oscols:
    if pcol is None or pcol>=len(values):continue
    product_name=values[pcol];rel=values[rcol] if rcol is not None and rcol<len(values) else ''
    if not valid_product_name(product_name) or os_versions(product_name):continue
    p,r=inventory_identity(vendor,product_name,byvendor,rel)
    if not valid_product_name(p):continue
    for col,vers in oscols.items():
     if col>=len(values):continue
     flag=cell_status(cells[col])
     if not flag:continue
     for version in vers:
      results.append(dict(vendor=vendor,product=p,release=r,zos_version=version,compatibility=flag,
         evidence_level='Exact product row and z/OS table cell',source_url=url,source_excerpt=' | '.join(values)[:700],
         source_timestamp=stamp,document_sha256=digest,match_status=match_label(vendor,p,r,byvendor)))
    continue
   # Broadcom-style matrix with z/OS version in first column, names in column headers.
   if not header and len(values)>=2 and any('z/os' in v.casefold() for v in values[0:1]):
    header=values
    continue
   if header and len(values)>=2 and os_versions(values[0]):
    for idx in range(1,min(len(values),len(header))):
     flag=cell_status(cells[idx]);p,r=inventory_identity(vendor,header[idx],byvendor)
     if not flag or not valid_product_name(p):continue
     for version in os_versions(values[0]):
      results.append(dict(vendor=vendor,product=p,release=r,zos_version=version,compatibility=flag,
         evidence_level='Explicit vendor support matrix cell',source_url=url,source_excerpt=(header[idx]+' | '+' | '.join(values))[:700],
         source_timestamp=stamp,document_sha256=digest,match_status=match_label(vendor,p,r,byvendor)))
 return results

def extract_ibm_product_os_table(soup,vendor,url,byvendor,stamp,digest):
 """Read product-scoped IBM SPCR-style OS tables only when a unique official
 heading explicitly identifies an inventory product and *full release*.
 A generic z/OS software requirement page cannot certify a product.
 """
 if vendor!='IBM':return []
 heading_matches=set()
 for heading in soup.find_all(['h1','h2']):
  phrase=flat(heading.get_text(' ',strip=True))
  for item in byvendor.get(vendor,[]):
   p,r=flat(item.get('product')),flat(item.get('release'))
   if not p or not r:continue
   base,_=split_identity(p,r)
   pattern=r'(?<![A-Za-z0-9])'+re.escape(base)+r'\s+(?:v|version\s*)?'+re.escape(r.lstrip('vV'))+r'(?![0-9]|\.[0-9])'
   if re.search(pattern,phrase,re.I):heading_matches.add((p,r))
 if len(heading_matches)!=1:return []
 product,release=next(iter(heading_matches));out=[]
 for table in soup.find_all('table'):
  if table.find_parent('table'):continue
  rows=table.find_all('tr',recursive=False)
  if len(rows)<2:continue
  heads=[flat(c.get_text(' ',strip=True)).casefold() for c in rows[0].find_all(['th','td'],recursive=False)]
  if not any('operating system' in h or h in ('os','platform') for h in heads):continue
  if not any('support' in h or 'compatib' in h or 'status' in h for h in heads):continue
  os_col=next(i for i,h in enumerate(heads) if 'operating system' in h or h in ('os','platform'))
  status_col=next(i for i,h in enumerate(heads) if 'support' in h or 'compatib' in h or 'status' in h)
  for row in rows[1:]:
   values=[flat(c.get_text(' ',strip=True)) for c in row.find_all(['td','th'],recursive=False)]
   if max(os_col,status_col)>=len(values):continue
   # Do not classify a platform like Linux 3.2 as z/OS 3.2.
   if 'z/os' not in values[os_col].casefold():continue
   sts=status(values[status_col]);versions=os_versions(values[os_col])
   if not sts:continue
   for ver in versions:
    out.append(dict(vendor=vendor,product=product,release=release,zos_version=ver,
      compatibility=sts,evidence_level='IBM product-heading + explicit OS support row',
      source_url=url,source_excerpt=' | '.join(values)[:700],source_timestamp=stamp,
      document_sha256=digest,match_status=match_label(vendor,product,release,byvendor)))
 return out

def section_nodes(target):
 """Read sibling content until a *different* named maintenance anchor.

 Does not walk through unrelated tables or rows beyond the anchor boundary.
 """
 node=target
 pieces=[]
 for _ in range(120):
  node=node.find_next(True)
  if node is None:break
  if node.name in ('a','section') and node is not target and (node.get('name') or node.get('id')):
   # do not stop on anchors nested in the current target itself
   if node.name=='a' and (node.get('name') or node.get('id')):break
  if node.name in ('td','th','p','li','h2','h3','h4'):
   if node.find_parent('script') or node.find_parent('nav'):continue
   # only leaf nodes to avoid double counting large nested table contents
   t=flat(node.get_text(' ',strip=True))
   if t and len(t)<1500:pieces.append(t)
  if sum(map(len,pieces))>9000:break
 return pieces

def explicit_section_identity(parts,vendor,byvendor):
 """Only explicit contiguous product/version in section; never fallback to URL context."""
 head=' '.join(parts[:4])
 candidates=[]
 for x in byvendor.get(vendor,[]):
  p,r=flat(x.get('product')),flat(x.get('release'))
  if not p or not r:continue
  # Some inventory rows include trailing version; accept both but require version in section.
  pname,prel=split_identity(p,r)
  variants=(p,pname)
  for variant in variants:
   if re.search(r'(?<![A-Za-z0-9])'+re.escape(variant)+r'\s+(?:v)?'+re.escape(r.lstrip('vV'))+r'(?![0-9]|\.[0-9])',head,re.I):
    candidates.append((len(variant),pname,r))
 if candidates:
  _,p,r=max(candidates)
  return p,r
 # Section may have a product heading but not an inventory match; preserve printed label.
 if parts:
  m=VER_RE.match(parts[0].split('Fix Category:')[0].strip())
  if m:return flat(m.group(1)),m.group(2)
 return '',''

def safe_install_status(s):
 """Only clear completion statements; never 'need to be installed'."""
 t=flat(s).casefold()
 if re.search(r'\b(?:not|never|haven.t|hasn.t|isn.t|wasn.t)\s+(?:been\s+)?(?:installed|applied)\b|\b(?:missing|not yet installed|not yet applied)\b',t):return 'Not installed (source-reported)'
 if re.search(r'\b(?:needs? to|must|should|required to|to be|will be|can be|please)\s+(?:be\s+)?(?:installed|applied)\b',t):return 'Unknown'
 if re.search(r'\b(?:already|successfully|currently|has been|have been|was|were)\s+(?:installed|applied)\b|\b(?:installed and verified|ptfs? installed)\b',t):return 'Installed/applied (source-reported)'
 return 'Unknown'

def extract_linked(soup,vendor,url,byvendor,stamp):
 out=[];seen=set()
 for a in soup.find_all('a',href=True):
  href=flat(a.get('href'))
  resolved=urljoin(url,href)
  page,ident=urldefrag(resolved)
  if not ident or urldefrag(page)[0].rstrip('/')!=urldefrag(url)[0].rstrip('/'):continue
  if not ident or ident in seen:continue
  seen.add(ident)
  tag=soup.find(id=ident) or soup.find('a',attrs={'name':ident})
  if tag is None:continue
  label=flat(a.get_text(' ',strip=True)).lower()
  if not any(x in (label+' '+ident.lower()) for x in ('ptf','apar','usermod','sysmod','maintenance','additional')):continue
  parts=section_nodes(tag)
  if not parts:continue
  p,r=explicit_section_identity(parts,vendor,byvendor)
  # If section isn't independently identifiable, do not assign to an arbitrary product.
  if not p or not r:continue
  # If the section accidentally spans the next product heading, cut it there.
  # This is safer than assigning its PTFs to the preceding product.
  truncated=[]
  for idx,piece in enumerate(parts):
   if idx and any(
      re.search(r'(?<![A-Za-z0-9])'+re.escape(split_identity(x.get('product',''),x.get('release',''))[0])+r'\s+v?'+re.escape(flat(x.get('release','')).lstrip('vV'))+r'(?![0-9]|\.[0-9])',piece,re.I)
      for x in byvendor.get(vendor,[])
      if flat(x.get('release')) and match_label(vendor,x.get('product'),x.get('release'),byvendor)=='Exact inventory match'
      and match_key(vendor,x.get('product'),x.get('release'))!=match_key(vendor,p,r)
   ):break
   truncated.append(piece)
  parts=truncated
  # Split at every FIXCAT, including JES3plus and other non-z/OS scopes.
  # Otherwise PTFs from a non-z/OS category can inherit a previous z/OS.
  segment=[];current_os=[]
  def flush():
   if not segment:return
   chunk=' '.join(segment)
   ids=ptf_ids(chunk)
   if not ids:return
   for version in current_os or ['Not stated']:
    for ident in ids:
     out.append(dict(vendor=vendor,product=p,release=r,zos_version=version,ptf_id=ident,
       maintenance_type='Linked maintenance section',publication_status=maintenance_availability(chunk),
       installation_status=safe_install_status(chunk),component='',source_url=urljoin(url,href),
       source_excerpt=chunk[:700],source_timestamp=stamp,
       evidence_level='Bounded named section; FIXCAT-scoped when stated',
       match_status=match_label(vendor,p,r,byvendor)))
  marker_re=re.compile(r'(?i)(?:Fix\s+Category\s*:\s*)?(?:[A-Z]{2}\.)?TargetSystem-RequiredService\.')
  for piece in parts:
   markers=list(marker_re.finditer(piece))
   if not markers:
    segment.append(piece)
    continue
   prefix=piece[:markers[0].start()].strip()
   if prefix:segment.append(prefix)
   for idx,marker in enumerate(markers):
    flush()
    end=markers[idx+1].start() if idx+1<len(markers) else len(piece)
    segment=[piece[marker.start():end]]
    current_os,_=scoped_fixcat_version(segment[0])
  flush()
 return out

def explicit_line_identity(vendor,chunk,byvendor):
 """Return an inventory identity only if the PDF line names the release explicitly."""
 candidates=[]
 for item in byvendor.get(vendor,[]):
  product=flat(item.get('product'));release=flat(item.get('release'))
  if not product or not release:continue
  base,embedded=split_identity(product)
  if not embedded:base=product
  expr=r'(?<![A-Za-z0-9])'+re.escape(base)+r'\s+(?:v)?'+re.escape(release.lstrip('vV'))+r'(?![0-9]|\.[0-9])'
  if re.search(expr,chunk,re.I):candidates.append((len(base),base,release))
 if not candidates:return '',''
 _,product,release=max(candidates)
 return product,release

def extract_html_safe(body,vendor,url,byvendor,contexts,stamp):
 soup=BeautifulSoup(body,'lxml')
 for node in soup(['script','style','nav','footer']):node.decompose()
 digest=hashlib.sha256(body).hexdigest()
 comps=parse_tables(soup,vendor,url,byvendor,stamp,digest)
 comps+=extract_ibm_product_os_table(soup,vendor,url,byvendor,stamp,digest)
 ptfs=extract_linked(soup,vendor,url,byvendor,stamp)
 # Explicit, self-contained product + version + z/OS statement only (never vague context).
 for ptag in soup.find_all(['p','li']):
  if ptag.find_parent('table'):continue
  phrase=flat(ptag.get_text(' ',strip=True))
  if not ptf_ids(phrase) or len(phrase)>900:continue
  matches=[]
  for record in byvendor.get(vendor,[]):
   product,release=flat(record.get('product')),flat(record.get('release'))
   if not product or not release:continue
   label,_=split_identity(product)
   if label==product:label,_=split_identity(product,release)
   if re.search(r'(?<![A-Za-z0-9])'+re.escape(label)+r'\s+(?:v)?'+re.escape(release.lstrip('vV'))+r'(?![0-9]|\.[0-9])',phrase,re.I):matches.append((product,release))
  if len(matches)!=1:continue
  product,release=matches[0]
  scoped,has_cat=scoped_fixcat_version(phrase)
  applicable=scoped if has_cat else os_versions(phrase)
  for ver in applicable or ['Not stated']:
   for ident in ptf_ids(phrase):
    ptfs.append(dict(vendor=vendor,product=product,release=release,zos_version=ver,ptf_id=ident,
       maintenance_type='Local product-specific statement',publication_status=maintenance_availability(phrase),
       installation_status=safe_install_status(phrase),component='',source_url=url,
       source_excerpt=phrase[:700],source_timestamp=stamp,evidence_level='Explicit product/release in local statement',
       match_status=match_label(vendor,product,release,byvendor)))
 # Avoid auto-promoting generic adapter assertions; table rows remain the certifiable source.
 def uniq(rows,fields):
  vals={}
  for x in rows:vals[tuple(x.get(f,'') for f in fields)]=x
  return list(vals.values())
 comps=[x for x in comps if valid_product_name(x['product'])]
 comps=uniq(comps,['vendor','product','release','zos_version','compatibility','source_url','source_excerpt'])
 ptfs=uniq(ptfs,['vendor','product','release','zos_version','ptf_id','source_url','source_excerpt'])
 ev=[]
 if vendor=='IBM':
  for tag in soup.find_all(['p','li','h1','h2','h3','title']):
   if tag.find_parent('table'):continue
   phrase=flat(tag.get_text(' ',strip=True))
   if not 8<len(phrase)<=700:continue
   ids=ptf_ids(phrase)
   if not ids:continue
   # Evidence-only: this is NOT a confirmed requirement or installed PTF.
   for ident in ids:
    if any(ident==p['ptf_id'] and phrase[:100] in p['source_excerpt'] for p in ptfs):continue
    ev.append(dict(vendor=vendor,product='',release='',zos_version='Not stated',
       evidence_kind='Unassigned IBM maintenance mention '+ident,source_url=url,
       source_excerpt=phrase[:700],source_timestamp=stamp,document_sha256=digest,
       match_status='Review: product/release not established'))
 for c in comps:ev.append(dict(vendor=vendor,product=c['product'],release=c['release'],zos_version=c['zos_version'],evidence_kind='Compatibility table',source_url=c['source_url'],source_excerpt=c['source_excerpt'],source_timestamp=stamp,document_sha256=digest,match_status=c['match_status']))
 for p in ptfs:ev.append(dict(vendor=vendor,product=p['product'],release=p['release'],zos_version=p['zos_version'],evidence_kind='Maintenance ID '+p['ptf_id'],source_url=p['source_url'],source_excerpt=p['source_excerpt'],source_timestamp=stamp,document_sha256=digest,match_status=p['match_status']))
 return comps,ptfs,ev,len(soup.find_all('table')),soup
