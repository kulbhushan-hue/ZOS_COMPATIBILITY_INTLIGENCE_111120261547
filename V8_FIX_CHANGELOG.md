# V8 deep scraper corrections — November 9, 2026

- Fixed compatibility status leakage between table rows (reproduced ACF2 vs CA 7 defect).
- Removed URL-context fallback for claims about a product/release.
- Constrained PTF parsing to named product/release sections and their associated FIXCAT where possible.
- Corrected false `Installed` classification for “need to be installed”.
- Added conflict report and strict export validation utility.
- Retained all existing nine dashboard pages, Broadcom legacy crawler, source documentation, and workbooks.
- Added regression tests covering wrong-row assignment, missing product identities, local PTF scope, installation semantics, and status conflicts.

No live vendor crawl was executed in this build environment.
