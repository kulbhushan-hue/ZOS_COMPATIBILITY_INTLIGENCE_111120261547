# V18 validation notes

Checks executed in build environment:

- Unit and regression suite: run `python -m unittest discover -s tests -q`.
- Python compilation: `python -m compileall -q .`.
- Offline inventory/source seed scan: 29 vendors, 623 unique inventory vendor/product/release entries, 105 distinct approved starting URLs across 24 vendors.
- Offline simulated network-run using three different vendor HTML fixtures: 3/3 reads, 11 publication-fact rows in `vendor_document_facts.csv`, 0 invented exact compatibility assertions, 0 PTF-installation assertions.
- Curated sources are taken from the previous 29-vendor public-source audit and validated against first-party host allowlists. Third-party or unconfirmed URLs were not promoted to official.

**Not verified:** a live end-to-end crawl for 29 vendors, every HTTP URL's current status, IBM SPCR browser rendering, full Windows graphical end-to-end execution, or complete availability/installation of any PTF. These are source- and environment-dependent and are explicitly reported as gaps rather than being marked successful.
