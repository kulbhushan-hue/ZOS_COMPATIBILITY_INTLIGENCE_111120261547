# z/OS Compatibility Intelligence V13 — Windows and Linux

## Two commands only

Extract the project ZIP into a folder and open a terminal or PowerShell there.

```bash
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

The dashboard opens in your browser (normally http://localhost:8501). **No separate extraction command is required.** The app starts its vendor source refresh in a background thread when first opened. It saves evidence and progress under `exports/deep/`.

The refresh is not instantaneous: follow `exports/deep/auto_scrape_status.json` for `Scraping`, `Completed`, `Partial`, or `Failed`. You can continue using the dashboard while it runs. Refresh the browser after the extraction finishes to see newly matched, exact vendor statements. Only explicitly matched product/release/OS support claims can change dashboard compatibility; evidence-only rows cannot.

### Platforms

- **Windows 10/11:** works directly in a compatible Python environment. `pip install -r requirements.txt` also installs Playwright for Windows. On the first run the app can download Chromium automatically in the background to attempt IBM SPCR rendering. This requires extra disk space and network access; the normal scraper works if the browser download fails. Docker is **not** required.
- **Linux:** works directly with Python for ordinary HTML and PDF scraping. The optional IBM JavaScript browser step is not automatically attempted on Linux because some older distributions (e.g. Ubuntu 18.04) cannot run the modern Playwright driver. Docker is not required for the normal application.
- Prefer Python **3.10–3.12** and a writable project directory. A supported operating system and sufficient free disk space are important.

### Sources, exports and quality

The crawler processes distinct approved URLs from the bundled ISV workbook, product worklist, vendor CSV baseline, and additional reviewed vendor URLs in `reference/vendor_sources_v13.csv`. It respects robots and vendor-domain boundaries. It stores:

- `all_vendor_extracted_compatibility.csv` — exact-version evidence only
- `all_vendor_extracted_ptfs.csv` — PTF references tied to source evidence
- `vendor_release_observations.csv` — useful statements that cannot certify an exact installed version
- `vendor_consolidated_ptfs.csv`, `vendor_scraping_results.csv`, `vendor_source_quality.csv`, `vendor_failed_links.csv`
- `source_cache/` — cached public HTML/PDF responses and hashes
- `auto_scrape_status.json` — current refresh status

**Availability or publication of a PTF does not mean it is installed.** A source returning HTTP 200 does not guarantee compatible product-level data. IBM SPCR may require browser rendering, and some BMC/other vendor URLs may restrict access. This package does not claim verified compatibility for all 29 vendors.

### Administration (not required to launch)

Set `ZOS_AUTO_SCRAPE=0` to disable the automatic start. The app refreshes at startup and normally avoids repeating a completed refresh for 24 hours. To force a clean rerun intentionally, run the existing backend command `python deep_scraper.py --fresh --sources reference/vendor_sources_v13.csv --max-pages 200 --depth 2` (not needed for regular users). Never run `--fresh` merely to start the dashboard.

For troubleshooting, review `exports/deep/auto_scrape_status.json` and `vendor_failed_links.csv`. Windows browser-capture errors appear as `Partial` in the status file without breaking the dashboard.
