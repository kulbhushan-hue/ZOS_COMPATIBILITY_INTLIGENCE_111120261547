# V16 — refreshed interface and extraction visibility

## Windows and Linux startup

From the extracted project folder:

```bash
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

The app launches its approved vendor source collector in the background when a refresh is due. No Docker or manual upload is required to *start* the app. Optional browser-based extraction may require a compatible installed browser and OS; static extraction remains available without it.

## New interface

- Updated visual styling, navigation, KPI cards and page headers.
- Dedicated **Extraction Coverage** workspace with 29-vendor and per-product reporting.
- Status feedback distinguishes running/completed/failed crawling from actual usable evidence.
- Search and filter by vendor, product, release and evidence status.
- Existing compatibility, PTF and workbook pages stay intact.

## Coverage caveat

This release does **not** certify that 29 vendors have been fully scraped. Some sites require dynamic rendering, login, or do not publish exact product-release maintenance publicly. Verified compatibility must not be inferred from HTTP 200 or a generic support announcement. The coverage reports explicitly show gaps.

## Tests

Run `python -m unittest discover -s tests -q`.
