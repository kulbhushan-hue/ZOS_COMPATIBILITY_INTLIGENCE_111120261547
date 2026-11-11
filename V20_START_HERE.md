# V20 — Five source classes and honest coverage reporting

Run after unzipping (from the project folder):

```
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

## What was actually implemented

- A method registry for **all 29 inventory vendors**, including Direct, Partial,
  Direct, limited, Dynamic, Conditional, Historical and Not confirmed.
- A source-by-source method outcome report: `exports/deep/vendor_method_coverage_v20.csv`.
  It is also displayed in the **Extraction Coverage** page.
- Official Rocket/ASG Zeke installation/release manuals and zopen package catalog
  added to approved sources. These are **not** z/OS 3.2 certifications.
- Evidence-only fact extraction from both HTML paragraphs/tables and automatically
  fetched vendor PDFs for named products (release and z/OS scope recorded only
  when explicitly stated within a local source passage).
- On machines where Playwright *and a compatible browser are already installed*,
  optional IBM SPCR browser rendering may be attempted on Linux or Windows.
  It respects robots and access controls. Browser installation is never
  silently attempted. On older Linux versions, including GLIBC 2.27, browser
  rendering may remain unavailable; static IBM data may remain empty.
- 29-vendor status stays honest: a source page that returns HTTP 200 is not a
  verified product/release compatibility claim.

## Not implemented / not guaranteed

This update is **not** proof of 29-vendor live extraction. Missing first-party
URLs, blocked 403 pages, product-only marketing pages, and IBM SPCR shells may
still have no exact compatibility or PTF claims. For Partial or Conditional
sources, the collector stores *published facts*, not guessed compatibility.
Older Rocket Zeke manuals do not prove support for z/OS 3.2.

## Output files to examine

1. `vendor_method_coverage_v20.csv`: category / access / facts / exact claims.
2. `vendor_document_facts.csv`: reviewable extracted evidence only.
3. `vendor_extraction_coverage.csv`: overall vendor coverage.
4. `vendor_product_extraction_coverage.csv`: exact inventory release gaps.
5. `vendor_failed_links.csv`: blocked/broken URLs.

All source texts remain subject to vendor website terms, robots restrictions,
permissions, and publication availability. No API credentials or document
uploads are required for publicly accessible sources.
