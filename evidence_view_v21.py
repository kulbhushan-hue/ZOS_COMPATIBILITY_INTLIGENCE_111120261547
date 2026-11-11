"""UI-only evidence presentation: never infer certification from inventory.

An exact vendor assertion is distinguished from an imported CSV/Excel status.
No claim is made about installed PTFs or coverage of unvisited vendor URLs.
"""
from __future__ import annotations
import json
from pathlib import Path
from urllib.parse import urlparse

import pandas as pd
from compatibility_db import VER


def _text(value):
    if pd.isna(value):
        return ''
    return str(value).strip()


def _official_link(url):
    text=_text(url)
    parsed=urlparse(text)
    return text if parsed.scheme in ('http','https') and parsed.netloc else ''


def _claim_status(provenance, raw_status, official_url):
    prov=_text(provenance).casefold()
    status=_text(raw_status)
    live=('vendor snapshot' in prov or 'exact vendor-source claim' in prov or 'exact live vendor source' in prov)
    if live and official_url and status in ('Yes','No','In Progress'):
        return status
    return 'Not verified'


def build_evidence_table(frame:pd.DataFrame, version:str)->pd.DataFrame:
    """Build a row-aligned table retaining the raw status but never calling it verified.

    Important: matches require positive provenance AND an actual HTTP(S) source URL.
    """
    if version not in VER:raise ValueError('Invalid z/OS release')
    status_col=VER[version][0]
    entries=[]
    for _,r in frame.iterrows():
        prov=_text(r.get('provenance_'+version,''))
        src=_official_link(r.get('verified_source_url_'+version,''))
        raw=_text(r.get(status_col,'')) or 'Unknown'
        baseline=_text(r.get('baseline_status_'+version,raw)) or 'Unknown'
        verified=_claim_status(prov,raw,src)
        type_name=('Exact vendor-source match' if verified!='Not verified' else
                   'Imported workbook baseline' if prov=='Excel AMXT' else
                   'Imported CSV baseline' if prov=='CSV baseline' else
                   'No verified source match')
        entries.append({'Vendor':_text(r.get('vendor','')),'Product':_text(r.get('product','')),
                        'Release':_text(r.get('vrm','')),'z/OS':version,
                        'Baseline status':baseline,
                        'Displayed compatibility':raw,'Vendor-verified status':verified,
                        'Evidence type':type_name,
                        'Official source':src,
                        'Source checked at':_text(r.get('verified_at_'+version,'')),
                        'Evidence excerpt':_text(r.get('verified_excerpt_'+version,'')),
                        'Maintenance installed':'Not checked',
                        'Source provenance':prov or 'Unknown'})
    return pd.DataFrame(entries,columns=['Vendor','Product','Release','z/OS','Baseline status','Displayed compatibility',
                 'Vendor-verified status','Evidence type','Official source','Source checked at',
                 'Evidence excerpt','Maintenance installed','Source provenance'])


def evidence_counts(rows:pd.DataFrame):
    if rows.empty:return {'verified':0,'yes':0,'no':0,'not_verified':0}
    statuses=rows['Vendor-verified status']
    return {'verified':int((statuses!='Not verified').sum()),
            'yes':int((statuses=='Yes').sum()),'no':int((statuses=='No').sum()),
            'not_verified':int((statuses=='Not verified').sum())}


def source_run_status(path):
    try:return json.loads(Path(path).read_text(encoding='utf-8'))
    except (OSError,ValueError,TypeError):return {}


def readable_source_status(status):
    if not status:return 'No collector status is recorded yet.'
    state=_text(status.get('state','Unknown'))
    stamp=_text(status.get('timestamp_utc','')) or 'unknown time'
    msg=_text(status.get('message',''))
    if state in ('Scraping','Running'):
        return f'Collection running (last status {stamp} UTC). Previous reports may be stale. {msg}'.strip()
    if state=='Completed':
        return f'Collection finished at {stamp} UTC. This does not mean all 29 vendors have extracted claims. {msg}'.strip()
    if state in ('Failed','Partial'):
        return f'Collection {state.lower()} at {stamp} UTC. Review Extraction Coverage and failed URLs. {msg}'.strip()
    return f'Collection state: {state}. Last update: {stamp} UTC. {msg}'.strip()
