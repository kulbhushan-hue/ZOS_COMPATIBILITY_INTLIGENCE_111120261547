"""Per-product acquisition and verification gap report.

Historical inventory is never upgraded to a vendor certification by merely
finding a link, name or a source page. This report makes source gaps actionable.
"""
from __future__ import annotations
from urllib.parse import urlsplit
import json
import re
import pandas as pd
from evidence_pipeline import latest_unique_observations, observation_match
from multi_vendor import safe_public_url, OFFICIAL
from workbook_data import vendor_name
from quality import match_key, ptf_ids


def _text(value):
    if value is None:return ''
    try:
        if pd.isna(value):return ''
    except (TypeError,ValueError):pass
    return str(value).strip()


def _latest_audits(audit_history):
    latest={}
    for row in audit_history:
        key=(vendor_name(row.get('vendor','')).casefold(),_text(row.get('source_url',row.get('url',''))))
        if key not in latest or _text(row.get('checked_at'))>_text(latest[key].get('checked_at')):
            latest[key]=row
    return latest


def product_source_worklist(inventory, audit_history=None, observations=None):
    """One row per input product, including source URL, last fetch result, data gaps.

    Does not invent verification results. A source read only establishes that the
    URL was fetched; a product-specific explicit release statement is separate.
    """
    if hasattr(inventory,'to_dict'):
        items=inventory.to_dict('records')
    else:items=list(inventory)
    audit_history=audit_history or []
    last=_latest_audits(audit_history)
    if observations is None:observations=latest_unique_observations(audit_history)
    index={}
    for obs in observations:
        if not _text(obs.get('vrm')) or _text(obs.get('vrm')).casefold() in ('not stated','unknown','nan'):continue
        key=match_key(vendor_name(obs.get('vendor')),obs.get('product'),obs.get('vrm'))
        index.setdefault(key,[]).append(obs)
    out=[]
    for item in items:
        vendor=vendor_name(item.get('vendor',''))
        product=_text(item.get('product'));version=_text(item.get('vrm'))
        url=_text(item.get('link'))
        valid=safe_public_url(url,vendor)
        approved=url if valid else ''
        scope='Approved vendor-domain URL' if valid else ('External/unapproved reference' if url.startswith(('http://','https://')) else 'Missing official product URL')
        relevant=index.get(match_key(vendor,product,version),[])
        explicit=[o for o in relevant if o.get('zos_version')=='3.2' and
                  _text(o.get('compatibility')) in ('Yes','No') and
                  'Explicit vendor table: product, release' in _text(o.get('evidence_level'))]
        audits=[row for (v,u),row in last.items() if v==vendor.casefold() and u==approved] if approved else []
        # A vendor domain check does not prove that this product-specific URL was checked.
        audit=max(audits,key=lambda r:_text(r.get('checked_at'))) if audits else None
        state=_text(audit.get('state')) if audit else ('Not checked' if approved else 'Not configured')
        ptf=ptf_ids(' '.join(_text(item.get(k)) for k in ('ptf_required','workbook_ptf_raw','workbook_comments')))
        decision=('Exact vendor/release evidence — manual review' if explicit else
                  ('Exact release reference, certification unverified' if relevant else
                   ('Approved source requires product-level extraction' if valid else 'Approved official source required')))
        if state=='Blocked / failed':decision='Source blocked/failed — authorized export required'
        out.append({'Vendor':vendor,'Product':product,'Release':version,
            'z/OS 3.2 baseline':_text(item.get('zos32')),'Approved source URL':approved,
            'Reference URL (unapproved)':url if not valid else '',
            'Source status':scope,'Last URL check':state,
            'Last URL checked at (UTC)':_text(audit.get('checked_at')) if audit else '',
            'Exact release observations':len(relevant),
            'Explicit z/OS 3.2 release claims':len(explicit),
            'Workbook/baseline PTF identifiers':', '.join(ptf),
            'Review action':decision,
            'Original workbook row':_text(item.get('workbook_row'))})
    return pd.DataFrame(out)


def coverage_summary(worklist):
    if worklist.empty:return {}
    return {'products':len(worklist),
            'approved_vendor_references':int((worklist['Source status']=='Approved vendor-domain URL').sum()),
            'missing_approved_sources':int((worklist['Source status']!='Approved vendor-domain URL').sum()),
            'exact_release_observations':int((worklist['Exact release observations']>0).sum()),
            'explicit_3_2_claims_for_review':int((worklist['Explicit z/OS 3.2 release claims']>0).sum()),
            'blocked_product_sources':int((worklist['Last URL check']=='Blocked / failed').sum())}
