# V9 backend changes

- Parser: `safe_extract_v8.py` tightened for valid product labels, exact full releases, multi-FIXCAT scoping and IBM evidence treatment.
- Parser: `deep_scraper.py` PDF line extraction now requires product/release before promoting PTF records; unmatched references remain evidence-only. PTF claims deduped per product/release/zOS/ID/source URL.
- Audit: `audit_v9_exports.py` checks previously downloaded reports without rewriting them.
- Tests: `tests/test_v9_accuracy.py` covers bogus product rows, mixed FIXCAT scopes, IBM product-scoped tables, unspecified IBM references, deduplication and version boundaries.
- No dashboard or frontend redesign.
