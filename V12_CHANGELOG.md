# V12 changes

- Added optional IBM SPCR Playwright capture command (`dynamic_capture_v12.py`).
- Respects robots.txt, only tries IBM report URLs from successful standard crawls, uses public URLs, rate limits between visits, and does not use login or bypass mechanisms.
- Saves browser-rendered HTML in V11's hash-verified response cache, allowing existing offline reparse without refetching.
- Adds `vendor_browser_capture.csv` diagnostic report.
- Detects IBM report shells with scripts, little text, and no tables instead of incorrectly marking all such pages as non-dynamic.
- Five new offline tests for these changes, for a total of 96 passing tests.
- No Streamlit UI changes or new vendor compatibility assertions.

**Known limitations:** Actual cached V11 page bodies were not supplied, and no complete live browser crawl was performed. Dynamic report endpoints may remain unavailable, browser rendering may return no tables, and vendor-specific HTML parsing may still need refinement after inspecting permitted cached bodies.
