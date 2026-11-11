# V18 — Official-source Hybrid Extraction

## Run on Windows or Linux: only two commands

From the `zos_compatibility_intelligence` folder:

```bash
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

The Streamlit UI opens immediately; a background source collector starts automatically if a refresh is due. On Source Monitor, click **Refresh All Vendors** to force a new run. Do not run the separate CLI unless debugging. On Windows, optional rendered IBM capture will try an installed Edge/Chrome browser. Browsers, network access, and vendor terms can still impose requirements; browser capture is not guaranteed by pip installation alone. The existing dashboard pages are preserved.

### What changed from V17

1. Source registry expanded using the provided 29-vendor research audit: `reference/vendor_sources_v18.csv` contains **36 curated URLs for 24 vendors**, plus the existing workbooks and compatibility feeds. In the bundled inventory this produces **105 distinct starting URLs across 24 vendors**, instead of 80 across 12 vendors. Both figures are baseline counts measured offline, not HTTP successes. The exact source queue may change when workbooks are updated.
2. Added conservative, source-specific HTML extractors for public release/support/maintenance evidence from Action Software, Vanguard, BMC, Compute (CBL), Confluent, Dynatrace, PKWARE, and Systemware. Existing Broadcom and Precisely handling remains intact.
3. Results from product-family tables, minimum OS requirements, PTF *mentions*, and tested OS ranges remain **document facts**, not assertions that a particular inventory release is installed, patched or ready. The supported version being absent from a vendor table is **not** automatically an unsupported verdict.
4. `vendor_source_quality.csv` now has `document_fact_rows` and `exact_inventory_claims`. `vendor_extraction_coverage.csv` counts URLs with exact inventory evidence separately from generic source claims. Refresh status says **Partial** when some vendors lack exact evidence, even when all URLs were attempted.
5. Saved the original 29-vendor research checklist and historic URL crawl audit under `reference/` for traceability.

### Output files

Automatic collection writes to `exports/deep/`. Inspect:

- `vendor_document_facts.csv`: official support ranges, maintenance levels, EOS, minima, supported-feature descriptions and local source excerpts.
- `all_vendor_extracted_compatibility.csv`: product/release compatibility assertions with source and match status.
- `all_vendor_extracted_ptfs.csv`: extracted maintenance identifiers; these **do not** establish local installation.
- `vendor_extraction_coverage.csv`: 29-vendor status, including missing or inaccessible sources.
- `vendor_product_extraction_coverage.csv`: inventory-level source/match gaps.
- `vendor_source_quality.csv`: raw counts, accepted counts, exact inventory matches, fact counts.
- `vendor_failed_links.csv`: source failures, blocked sites, access problems.
- `source_cache/`: downloaded source documents for later offline replay.

### Important limits

**No claim of full 29-vendor success.** Five inventory vendors still lack a suitable confirmed first-party starting URL: Cincom Systems, Cisco Systems, FIS, Levi Ray & Shoup, and Quest Software. Some third-party historical references in the research audit were intentionally not made crawl targets. IBM SPCR may return a small JavaScript shell. BMC and other pages may return 403 or need authorization. No access controls are bypassed; no API key, hand-uploaded PDF, HTML file, or Docker container is required for the basic workflow.

Only **offline automated tests** and an offline crawler simulation were executed here. Live extraction must be measured in the resulting coverage reports. If a publisher does not publicly provide a release-specific compatibility/PTF detail, a trustworthy scraper cannot manufacture it.

### Optional developer tests

```bash
python -m unittest discover -s tests -q
```

Use `python deep_scraper.py --reparse-cache` only for debugging or after adding parser rules. It cannot create newly published data from previously fetched documents.
