# V14 — two-command installation (Windows or Linux)

From the extracted `zos_compatibility_intelligence` folder:

```bash
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

The dashboard automatically starts its backend crawl when due. It does not need
Docker or a third command. The first run needs working internet access and can
finish after the dashboard opens.

Check `exports/deep/auto_scrape_status.json` for current crawler status.
Check `exports/deep/vendor_document_facts.csv` for non-Broadcom source facts.
Check `exports/deep/vendor_failed_links.csv` for access failures.

**Data integrity:** Product-family support, minimum OS, service-pack publication,
and JS shell pages are *not* proof of the exact installed release's compatibility.
The `vendor_document_facts.csv` report is evidence-only. Nothing in it is
silently promoted to Yes or Installed in your dashboard.

Limitations: No guarantee every source is accessible, IBM SPCR reports can be
JavaScript shells, some BMC pages return 403, and authorized vendor sources
may require export. A working dashboard is not proof the data crawl completed.

Automatic refresh respects the existing 24-hour completion interval. For testing
on your own machine, after backing up exports, delete only the `auto_scrape_status.json`
file and run Streamlit again; a complete refresh may also require resetting the
crawler's checkpoint, or use the optional `--fresh` backend CLI.
