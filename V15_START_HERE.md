# z/OS Compatibility Intelligence — V15 Hybrid Backend

## Windows / Linux: start with only two commands

Open a terminal or PowerShell **inside the extracted project folder**:

```bash
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

The normal vendor crawler starts automatically in the background when its 24-hour refresh window is due. You do not need Docker, API keys, or manual vendor PDF/HTML uploads for public sources. The dashboard remains unchanged. `exports/deep/auto_scrape_status.json` reports progress. Windows uses installed Edge/Chrome for *optional* IBM browser capture when supported; an additional browser download is not required to launch Streamlit. On older Linux systems, Chromium/Playwright may be unavailable: ordinary HTTP and PDF collection still runs.

## What is automatic

1. Load the workbook and built-in vendor references; deduplicate the source URLs.
2. Retrieve accessible official vendor HTML, text, and PDF sources with bounded navigation.
3. Parse Broadcom compatibility/PTF data and support evidence for known non-Broadcom document layouts.
4. Optionally render IBM SPCR report shells on compatible Windows systems.
5. Preserve source URLs and cache body hashes. Do **not** infer PTF installation or certify a release from a general announcement.
6. Export results and source quality / product coverage reports. Refresh again when due, while the application is running.

## Most important outputs

- `exports/deep/vendor_extraction_coverage.csv`: **per-vendor** number of configured/fetched/read sources, actual structured claims, document facts and dynamic-page gaps.
- `exports/deep/vendor_product_extraction_coverage.csv`: **per-product** sources, evidence and exact match status.
- `exports/deep/vendor_document_facts.csv`: published facts not sufficient to prove an installed release is compatible.
- `exports/deep/all_vendor_extracted_compatibility.csv`: extracted exact compatibility assertions; check inventory match status.
- `exports/deep/all_vendor_extracted_ptfs.csv`: scoped PTF references; installation is not assumed.
- `exports/deep/vendor_failed_links.csv`: failed sources, blocks and errors.
- `exports/deep/source_cache/`: automatically downloaded raw responses (no uploads needed).

## Known limitations (important)

- **Not verified as a complete 29-vendor scraper.** The supplied inventory references 29 vendors, but official approved source URLs are configured for fewer vendors. `vendor_extraction_coverage.csv` shows the difference.
- IBM SPCR can deliver JavaScript shells rather than populated data to a static HTTP client; Edge rendering may still fail if reports use unavailable endpoints.
- BMC support data can be protected or blocked; public website access in a normal browser is not a guarantee that automation is permitted or can read the same data.
- Some PTF applicability and installed maintenance status are not public. No API or scraper can accurately infer installed fixes without system/inventory data.
- A local computer must remain on with the app running for periodic refreshes. An always-on host/scheduler is needed for unattended 24/7 updates.

## Troubleshooting

If the scraper is still processing, let it finish. Review `auto_scrape_status.json` and the two coverage CSVs rather than assuming HTTP 200 means successful extraction.

To run local regression tests (optional):

```bash
python -m unittest discover -s tests -q
```

Use the existing exported archive for past results. Do not use historical rows as newly verified live claims.
