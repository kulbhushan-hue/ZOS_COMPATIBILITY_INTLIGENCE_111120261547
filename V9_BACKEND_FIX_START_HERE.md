# z/OS Deep Scraping V9 — backend extraction accuracy

This release preserves the existing Streamlit dashboard. The deep scraper is a **separate backend process**; running Streamlit does not automatically execute a crawl. Do not treat an extracted PTF as installed, available, or required unless the source and applicability establish those facts.

## Requirements

- Python 3.11 or 3.12, internet access to approved official vendor sources.
- Optional: authorized vendor HTML/PDF exports for sources requiring sign-in.
- Persistent writable filesystem for checkpoint/results if running in a cloud container.

## Install

From the folder containing `deep_scraper.py`:

**Windows PowerShell**

```powershell
py -3.11 -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m unittest discover -s tests -q
```

**Linux / macOS**

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m unittest discover -s tests -q
```

## Run a fresh V9 crawl

**Do not resume the V8 checkpoint**: earlier CSVs contain incorrectly assigned PTF versions and invalid product rows.

```bash
python deep_scraper.py --fresh --max-pages 200 --depth 2 --output exports/deep
```

Continue pending URLs (checkpoint and existing results are reused):

```bash
python deep_scraper.py --max-pages 200 --depth 2 --output exports/deep
```

Each run processes up to `--max-pages` URLs. A fresh run archives earlier CSV/checkpoint files under `exports/deep/archive/`. If the checkpoint reports an empty queue, no more discovered/approved URLs remain in that run. This **does not** prove complete vendor coverage.

Check outputs:

```bash
python validate_deep_exports.py --output exports/deep
python audit_v9_exports.py --input exports/deep
```

For an offline audit of an existing export, place the exported compatibility and PTF CSVs in a folder, then run `python audit_v9_exports.py --input PATH_TO_FOLDER`.

## What changed in V9

1. Reject bogus product labels such as `YES`, `YES Info`, and `YES PTFs Info`.
2. Require exact full release boundaries: `12.5` cannot be automatically matched as `12`.
3. Split maintenance evidence **at every FIXCAT marker**, even when multiple FIXCATs occur in a single paragraph. Assign z/OS versions only from the applicable z/OS FIXCAT. JES3plus and other non-z/OS FIXCATs remain `Not stated` for z/OS compatibility.
4. Deduplicate identical PTF claims from one source while keeping other source URLs separate.
5. Allow an IBM compatibility assertion only if the page has exactly one matching product-and-release heading **and** an explicit OS support table. Unmatched IBM PTF mentions appear only in the source evidence report, never as confirmed requirements.
6. Preserve existing source evidence and conflicts; no dashboard UI changes.
7. `audit_v9_exports.py` reports suspicious product labels, cross-FIXCAT assignments, repeated claims and vendor-specific coverage.

## Output files

- `all_vendor_extracted_compatibility.csv`
- `all_vendor_extracted_ptfs.csv`
- `vendor_source_evidence.csv` (also contains **unassigned IBM maintenance mentions** for investigation)
- `vendor_conflicting_claims.csv`
- `vendor_scraping_results.csv`
- `vendor_failed_links.csv`
- `deep_scrape_checkpoint.json`

Use a fresh crawl to produce a new valid dataset. Do not mix previously exported V8 claims with fresh V9 evidence.

## Important limits

- A full live crawl was **not** executed in the packaging environment. Unit tests use synthetic HTML and offline regression fixtures.
- Some official vendor pages require authorized login or interactive rendering. Neither a 200 response nor a reference to z/OS proves compatibility. BMC 403/404 pages will not be bypassed.
- The IBM parser supports certain product-scoped HTML tables, not every interactive IBM SPCR report. Unmatched IBM identifiers remain research evidence.
- If V9 yields fewer compatibility/PTF rows than V8, this can be a result of deliberately rejecting ungrounded claims.
- For Streamlit UI (unchanged), run `python -m streamlit run app.py` separately.
