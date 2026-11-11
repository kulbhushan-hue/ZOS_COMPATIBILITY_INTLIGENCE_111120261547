# V21 — Baseline versus vendor-source evidence (Streamlit)

Run from this project folder:

```bash
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

## What changed

- **Overview**: prominent source-matched counts (support, no support, no exact match), separated from the original inventory baseline counts. The baseline chart uses the original imported statuses rather than an updated vendor claim.
- **Comparative Matrix**: individual z/OS 3.1 and 3.2 baseline and source-matched columns; official source links are clickable. Vendor, release text, source-match status filters and CSV download.
- **Compatibility Matrix**: source-only/baseline-only filter, easy-to-read evidence table and separate CSV export; detailed maintenance columns moved under a collapsible section.
- **Source provenance**: exact deep-source claims carry their URL, timestamp, and excerpt where provided by the crawler. Broadcom snapshot provenance is preserved in the merged data. Missing source URLs are not presented as verified.
- **Source collection indicator**: summarises collector status but never equates a successful crawl with comprehensive vendor coverage.
- Full original source collector and existing Source Monitor/Extraction Coverage remain unchanged.

## Data meaning and limits

- `Baseline status` is taken from the historical input CSV/workbook, not a fresh vendor check.
- `Vendor-verified status` means an existing persisted source assertion was exact-matched to vendor, product, release and target z/OS version **and** included a source URL. It does not verify installed maintenance or the ongoing availability of that URL.
- `Not verified` is **not** `No`.
- Source coverage still has the unresolved public source and product-specific gaps in V20. V21 does **not** claim that all 29 vendors have been scraped.
- `No AMXT match` means only that an Excel crosswalk did not match.
- Streamlit visual end-to-end testing on Firefox/Ubuntu is still required; this build was checked by unit tests and Python compilation only.
