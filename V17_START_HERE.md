# V17 — Fast, colorful Streamlit dashboard and all-vendor refresh

## Run (Windows or Linux)

From the folder containing `app.py`:

```bash
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

The same project works on Windows with a supported Python version. The standard scraper uses HTTP/HTML/PDF extraction; optional browser rendering may require a browser-compatible OS. No Docker command is required to start the UI.

## What's changed

- Light app canvas, dark navy sidebar, colored metric cards, clearer typography and spacing, and color-coded compatibility status chart.
- Source Monitor now starts with a prominent **Refresh All Vendors** button. It launches the multi-vendor deep extraction worker without blocking the Streamlit UI. Broadcom-specific refresh remains under an Advanced expander.
- Refresh All Vendors forces a **fresh source cycle**, archives prior CSV results, and reports progress through `exports/deep/auto_scrape_status.json`. Concurrent requests are suppressed.
- The expensive inventory/Broadcom/deep-evidence merge is cached until the underlying SQLite snapshot or deep CSV changes, reducing delays on page navigation and filter changes.
- Removed third-party web-font fetching so the UI can render without waiting for Google Fonts.
- Existing ten pages, original dataset, CSV exports and matching safeguards are preserved.

## Important distinctions

**Refresh All Vendors attempts every configured approved vendor URL**; it does not guarantee that every one of 29 inventory vendors has a product-specific source or usable evidence. The collector reports failures, missing data and product-level coverage. Blocked/login-required pages are not bypassed. A vendor website being readable does not establish compatibility or installed PTF status.

Open **Extraction Coverage** after the refresh completes to inspect `vendor_extraction_coverage.csv`, `vendor_product_extraction_coverage.csv` and `vendor_failed_links.csv`.

## Testing

120 offline tests pass and Python modules compile. Not visually browser-tested here, and no complete live 29-vendor crawl was run in this build environment.
