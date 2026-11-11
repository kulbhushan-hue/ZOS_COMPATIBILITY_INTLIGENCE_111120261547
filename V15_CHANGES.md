# V15 backend changes

- Added auditable vendor and product extraction coverage exports; URL access no longer masquerades as successful product extraction.
- Expanded relevant-link discovery across official vendor subdomains under the existing domain allowlist.
- Optional Playwright rendering now tries installed Microsoft Edge, then Chrome, and then available Chromium; browser download is not triggered during UI startup.
- Startup reports the coverage CSV locations and preserves the original Streamlit dashboard and two-command launch.
- Added regression tests for dynamic source gaps, evidence-only source statements, product match status and IBM report shell recognition.

**Offline tests are not live end-to-end verification.** No change claims to bypass blocked vendor sites or confirm all 29 vendors.
