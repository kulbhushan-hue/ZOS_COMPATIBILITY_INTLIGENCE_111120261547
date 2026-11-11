# z/OS deep scraping V8 — safe product matching and PTF applicability

## What changed (backend only)

The existing Streamlit UI is intentionally unchanged. `deep_scraper.py` now delegates HTML extraction to `safe_extract_v8.py`:

1. **Product isolation:** A compatibility status comes from the product name and release in the *same explicit HTML table row*, not from the inventory URL or adjacent rows. Unknown row identities are not guessed.
2. **Maintenance isolation:** PTF identifiers from anchor-linked sections are bounded to the section, scoped by explicitly stated FIXCAT/z/OS where present, and assigned to a product only when the section names that exact release. Local paragraphs need an explicit product and release. IDs with no release identity are conservatively skipped rather than misattributed.
3. **Installation semantics:** Phrases such as “needs to be installed”, “must be applied”, “to be installed” no longer imply installation completed. If no affirmative evidence exists, installation status is `Unknown`. Vendor statements are *never* proof of what is installed on your own mainframe.
4. **Conflict output:** `vendor_conflicting_claims.csv` flags multiple published statuses for the same vendor/product/release/z/OS combination. The underlying evidence remains available but is not arbitrarily resolved.
5. **PDF line extraction:** Uses the corrected installation wording rule. PDF references still require review for product/version applicability.
6. **Source fidelity:** Rows retain their original URL and excerpt. Partial/uncertain results are not promoted as verified compatibility.

**Tradeoff:** The conservative V8 parser may return *fewer* PTF records than the faulty V7 parser. A smaller but attributable result is preferable to assigning another product's PTFs. Some complex proprietary vendor table layouts need dedicated adapters and validated HTML fixtures.

## Run locally

Python 3.11+ recommended. Open a terminal in the folder containing `deep_scraper.py`.

```bash
python -m pip install -r requirements.txt
python -m unittest discover -s tests -q
```

Run a **fresh crawl** so the V7 incorrect evidence is not reused:

```bash
python deep_scraper.py --fresh --max-pages 200 --depth 2 --output exports/deep
```

To continue if URLs remain in the checkpoint queue:

```bash
python deep_scraper.py --max-pages 200 --depth 2 --output exports/deep
```

To inspect coverage and conflicts:

```bash
python validate_deep_exports.py --output exports/deep
```

### Files in `exports/deep/`

- `all_vendor_extracted_compatibility.csv`: Source-supported table-cell compatibility claims with product/release matching labels.
- `all_vendor_extracted_ptfs.csv`: Conservatively scoped identifiers; `Not stated` means z/OS scope was not established.
- `vendor_conflicting_claims.csv`: Contradictory statements that require review.
- `vendor_source_evidence.csv`: Source excerpts and links.
- `vendor_scraping_results.csv`: URL outcomes.
- `vendor_failed_links.csv`: URLs that could not be processed.
- `deep_scrape_checkpoint.json`: Crawl progress.

The `--fresh` option archives old CSVs/checkpoint under `exports/deep/archive/` so they cannot contaminate the new run. **Do not merge the previously downloaded V7 exports into the V8 results.**

## Scope and limitations

- This is an extraction reliability fix, **not** proof that all 29 vendors can be scraped or that any particular PTF is installed.
- Some IBM SPCR reports are dynamic, BMC portals may require authorization, and some vendor sources provide PDF-only or nonstandard tables. Use authorized reports or purpose-built adapters where necessary.
- A source with HTTP 200 but zero extracted rows is not evidence of compatibility.
- The original Streamlit dashboard has not been reworked to consume this new backend's output automatically. The clean backend files are the validation target for this release.
- Offline regression tests do not replace a live crawl and manual spot-check of official vendor rows.
