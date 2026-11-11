# V19 — fixes based on user's Firefox screenshots

- Fixed icon fallback styling in Streamlit expanders to avoid visible `keyboard_arrow_right` ligature names when browser cannot load Material Symbols fonts.
- Replaced 29 tall vendor accordions with a compact vendor selector and clickable URL table.
- Source Monitor now reads the deep crawl checkpoint and shows visited/pending URLs, separate from actual verified compatibility claims.
- Clarified Broadcom snapshot job history versus all-vendor crawler progress.
- Clarified baseline rows (623) are not newly verified compatibility facts.
- Added explicit Streamlit light theme and improved label/button readability.
- Kept the two-command startup and existing background scraper unchanged.

Limitations: The updated UI was statically validated and 129 offline tests passed. It has not been visually tested inside Firefox, and a full live 29-vendor extraction remains unverified. Poll the Source Monitor by switching pages or refreshing it to see updated checkpoint values.
