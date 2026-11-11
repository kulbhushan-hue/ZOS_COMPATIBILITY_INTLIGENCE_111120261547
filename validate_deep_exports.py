"""Summarize V8 extracted CSV quality without inventing or resolving evidence."""
import argparse
import csv
import json
from collections import Counter
from pathlib import Path

def read(path):
 if not path.is_file():return []
 with path.open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))

def summarize(folder):
 folder=Path(folder)
 comp=read(folder/'all_vendor_extracted_compatibility.csv')
 ptfs=read(folder/'all_vendor_extracted_ptfs.csv')
 jobs=read(folder/'vendor_scraping_results.csv')
 conflicts=read(folder/'vendor_conflicting_claims.csv')
 return {
  'source_urls_checked':len(jobs),
  'source_states':dict(Counter(r.get('state','') for r in jobs)),
  'compatibility_evidence_rows':len(comp),
  'compatibility_rows_with_exact_inventory_match':sum(r.get('match_status')=='Exact inventory match' for r in comp),
  'conflicting_product_release_os_groups':len(conflicts),
  'maintenance_evidence_rows':len(ptfs),
  'distinct_ptf_ids':len({r.get('ptf_id') for r in ptfs if r.get('ptf_id')}),
  'ptf_rows_with_explicit_zos_version':sum(r.get('zos_version') in ('3.2','3.1','2.5') for r in ptfs),
  'ptf_rows_installation_unknown':sum(r.get('installation_status')=='Unknown' for r in ptfs),
  'ptf_rows_without_product_release':sum(not r.get('product') or not r.get('release') for r in ptfs),
  'vendor_compatibility_rows':dict(Counter(r.get('vendor','') for r in comp)),
  'vendor_ptf_rows':dict(Counter(r.get('vendor','') for r in ptfs)),
 }

if __name__=='__main__':
 ap=argparse.ArgumentParser()
 ap.add_argument('--output',default='exports/deep')
 args=ap.parse_args()
 print(json.dumps(summarize(args.output),indent=2))
