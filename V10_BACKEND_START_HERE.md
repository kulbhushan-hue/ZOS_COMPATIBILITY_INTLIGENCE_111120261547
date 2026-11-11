# V10 — Vendor-specific scraping and evidence consolidation

This is **backend-only**. No Streamlit UI pages or dashboard code were redesigned.

## What changes

- `vendor_adapters_v10.py` supports an additional **z/OS rows / product columns** matrix format (such as BMC support matrices), with a separate **evidence-only** path for statements that do not establish the exact product release.
- IBM SPCR-style tables support **exact product + release heading + explicit OS support status**; OS listings without an explicit supported/unsupported status remain evidence-only. This does not guarantee every IBM dynamic SPCR page will render as parseable HTML.
- `vendor_consolidated_ptfs.csv` groups the same vendor/product/release/z/OS/PTF claim and keeps all distinct source URLs. Inconsistent publication or installation statements are flagged for review. It is a worklist, not installation verification.
- `vendor_source_quality.csv` distinguishes an accessible page from one that produced structured claims or only evidence-only observations.
- `vendor_release_observations.csv` stores source support statements without exact product/release applicability, rather than marking the inventory compatible.

## Setup

```bash
python -m pip install -r requirements.txt
python -m unittest discover -s tests -q
```

Start a **fresh** scrape (recommended after installing V10 because older exports contain parser output from V9):

```bash
python deep_scraper.py --fresh --max-pages 200 --depth 2
```

Continue remaining queued links:

```bash
python deep_scraper.py --max-pages 200 --depth 2
```

Re-check failures:

```bash
python deep_scraper.py --retry-failed --max-pages 200
```

Import authorized HTML/PDF documents without bypassing authentication:

```bash
python deep_scraper.py --max-pages 1 --documents-manifest documents.csv
```

`documents.csv` columns: `Vendor,Path,SourceURL,Product,Release`. **Note:** the command still checks up to one queued public URL; document import executes after that. For a document-only import, use `python -c "from deep_scraper import import_authorized_documents, inventory_and_queue; from pathlib import Path; r=Path('.').resolve(); _,inv=inventory_and_queue(r); print(import_authorized_documents(Path('documents.csv'),r/'exports/deep',inv))"`; then run the crawler command to rebuild derived reports.

## Generated reports

- `exports/deep/all_vendor_extracted_compatibility.csv`: source-backed, exact-release compatibility assertions
- `exports/deep/all_vendor_extracted_ptfs.csv`: source-level PTF/maintenance observations
- `exports/deep/vendor_consolidated_ptfs.csv`: one maintenance claim per product/release/OS/PTF, with **all source URLs**, flags for inconsistent status
- `exports/deep/vendor_release_observations.csv`: vendor claims with release uncertain, **not** promoted to the compatibility table
- `exports/deep/vendor_source_quality.csv`: per-URL read and structured extraction quality
- `exports/deep/vendor_source_evidence.csv`: source excerpts and document hashes
- `exports/deep/vendor_scraping_results.csv`: processed URLs and counts
- `exports/deep/vendor_failed_links.csv`: access, HTTP and parser failures
- `exports/deep/vendor_conflicting_claims.csv`: contradictory compatibility claims requiring review
- `exports/deep/deep_scrape_checkpoint.json`: resumable queue state

## Important limits

- The V9 dataset processed **100 URLs with 87 successful reads**, but its structured compatibility and assigned maintenance results were all Broadcom. That is a **baseline**, not a verified V10 result.
- Exact supported release is required for a certification-level claim. BMC notes like “Support started in version 2.5.00” provide useful vendor support evidence but do **not** automatically certify a record simply because it is version 2.5.00.
- IBM SPCR sites can depend on client-side rendering; if the fetched page lacks the OS report table, use a vendor-authorized export or build a source-specific adapter from the legally accessible machine-readable response.
- No automatic login bypass, anti-bot evasion, or invented compatibility statuses.
- Extracted PTFs are not proof that a fix is installed. Source-level matches can still require human applicability verification.
- Full live extraction across all 29 vendors was **not executed during packaging**. The newly added parsers have offline regression coverage; compare your fresh live outputs after running.
