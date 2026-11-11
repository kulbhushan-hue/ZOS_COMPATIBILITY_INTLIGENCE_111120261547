# V12 — Backend-only IBM SPCR browser capture

**Scope:** The existing dashboard, Broadcom extractor, and existing export schemas are unchanged. This release adds a separate, optional way to capture *rendered* IBM SPCR pages so they can be inspected and replayed. This feature does **not** mean IBM compatibility records are verified or extracted automatically.

## Reason
V11 diagnostics showed that many IBM SPCR URLs returned a small HTML shell (~3–4 KB), scripts, and no tables. This can mean dynamic rendering. Ordinary HTTP 200 is not proof of a data-bearing page.

## Install

```bash
python -m pip install -r requirements.txt
```

For optional IBM browser capture, install Playwright separately:

```bash
python -m pip install playwright
python -m playwright install chromium
```

Playwright is **not** needed for ordinary scraping or the existing dashboard.

## Run a fresh scrape

```bash
python deep_scraper.py --fresh --max-pages 200 --depth 2
python inspect_source_cache.py --output exports/deep
```

## Capture dynamic IBM reports

```bash
python dynamic_capture_v12.py --output exports/deep --limit 40 --delay 2
```

The browser mode uses only **IBM SPCR URLs already successfully visited** by the standard crawler, checks robots.txt, does not use login credentials, and does not bypass inaccessible vendor sources. It saves HTML snapshots into the content-addressed `exports/deep/source_cache` and reports outcome in `exports/deep/vendor_browser_capture.csv`. Browser code must be run in a machine where Chromium can access IBM's reports; it was not run against live vendor pages in the development environment.

### Replay captured snapshots without network access

```bash
python deep_scraper.py --reparse-cache
python inspect_source_cache.py --output exports/deep
python validate_deep_exports.py --output exports/deep
```

The offline replay re-evaluates the saved rendered HTML using the existing conservative parser. **A snapshot containing a support matrix does not automatically certify the inventory release.** Unsupported or ambiguous statements remain evidence-only.

## What to share for exact parser improvements

1. `vendor_browser_capture.csv`
2. `vendor_cache_inspection.csv`
3. `vendor_source_quality.csv`
4. A ZIP of the authorized `exports/deep/source_cache` directory (if sharing the source documents is permitted).

Without the cached HTML bodies, it is not possible to develop reliable vendor-specific parsers against the actual returned markup. The prior diagnostic CSVs contain metadata, not that markup.

## Tests

```bash
python -m unittest discover -s tests -q
```

The new V12 regression cases test shell detection, source selection, and replay using synthetic examples. They do not demonstrate live IBM extraction.
