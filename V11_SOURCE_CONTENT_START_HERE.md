# V11 — Source-content-driven scraping (backend only)

V11 keeps the dashboard unchanged. It adds a raw response cache and offline replay so
vendor-specific parsers can be developed from *actual HTML/PDF responses*, not invented
example pages. Unit tests do not establish live vendor coverage.

## Run

```bash
python -m pip install -r requirements.txt
python -m unittest discover -s tests -q
python deep_scraper.py --fresh --max-pages 200 --depth 2
python inspect_source_cache.py --output exports/deep
```

`--fresh` archives the previous report CSVs and checkpoint. It **does not remove**
`source_cache/`, because old source bytes are useful for parser regression testing.
To reprocess the latest saved response for each URL without contacting a website:

```bash
python deep_scraper.py --reparse-cache
python inspect_source_cache.py --output exports/deep
```

Optional `--vendor IBM` on `--reparse-cache` limits replay to IBM. **This replaces
current structured extraction reports with the filtered replay results**, so use
another output directory when conducting limited experiments. Reports that depend on
all vendors are only complete when replay runs without a filter.

## New artifacts

- `exports/deep/source_cache/manifest.jsonl`: URL, vendor, fetch time, response hash,
  media type, original product contexts (no headers/cookies or credentials).
- `exports/deep/source_cache/objects/<sha256>`: immutable raw HTML/PDF response body.
- `exports/deep/vendor_page_diagnostics.csv`: page format, title, table counts, script
  counts, size, and possible client-side-rendering signal.
- `exports/deep/vendor_cache_inspection.csv`: no-network inspection combining page
  structure and parse result.
- `exports/deep/vendor_source_quality.csv`: separate raw parser counts from unique
  accepted per-URL compatibility/PTF counts, plus response hash and cache status.

Raw vendor content is not placed in the distributed ZIP and is cached only after your
own authorized crawl. Treat cache files as vendor documents and do not upload them
publicly without approval. Respect robots.txt, vendor terms and authentication.

## Important limitations

1. A successful HTTP 200 does not mean product compatibility was extracted.
2. For IBM SPCR reports, identify whether the report content is server-rendered,
   embedded in JSON, dynamically loaded, or absent in the cached response.
3. For BMC, release minimums in comments do not automatically certify the exact
   installed release. Capture the actual matrix and enforce the release boundary.
4. New vendor-specific extractors must be tested against saved, legally obtained
   HTML/PDF snapshots. JavaScript-only data requires an approved browser adapter.
5. `--reparse-cache` uses the latest cached content for each vendor/URL and is **not**
   a live refresh. Installation status is still unknown without inventory evidence.
6. Source quality is per URL. The same claim may exist at several URLs: do not sum
   per-URL counts to derive globally unique claims.
