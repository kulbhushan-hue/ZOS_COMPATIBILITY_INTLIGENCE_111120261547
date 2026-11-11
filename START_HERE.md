# START HERE — z/OS Compatibility Intelligence (PTF evidence & quality release)

This is the COMPLETE nine-page application. It includes the original six vendor CSVs,
the `ISV Compatibility assessment -Data.xlsx` workbook (all three sheets), the Broadcom
scraper, SQLite snapshot storage, the PTF worklist, and automated tests.

## 1. Unzip and find the application folder

Extract `zos_compatibility_intelligence_quality_fixed_20261109.zip`. Open the folder
`zos_compatibility_intelligence` **that contains `app.py`, `requirements.txt`, `data/`, and the Excel workbook**.
Do not run commands from the ZIP file itself or from its parent directory.

## 2. Install Python

Use Python **3.11 or 3.12** (64-bit) and ensure `python` or `py` works in the terminal.
Check with `python --version` (Windows may use `py -3.11 --version`).

## 3. Install and run — Windows PowerShell

```powershell
cd "C:\path\to\zos_compatibility_intelligence"
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m unittest discover -s tests -v
python -m streamlit run app.py
```

If PowerShell blocks the activation script, use `.venv\Scripts\python.exe` instead of `python` for the three Python commands; e.g. `.venv\Scripts\python.exe -m streamlit run app.py`.

## 4. Install and run — macOS/Linux/Ubuntu

```bash
cd /path/to/zos_compatibility_intelligence
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m unittest discover -s tests -v
python -m streamlit run app.py
```

If `python3.11` is not installed, use your installed Python 3.12 (`python3.12`).
On Ubuntu, the `python3.11-venv` package may be required.

Open **http://localhost:8501** if the browser doesn't launch automatically.
Stop the server with `Ctrl+C`.

## 5. Verify the two requested fixes

1. Open **PTF Intelligence**: the **Excel AMXT — PTFs / USERMODs worklist** and
   **Combined PTF / USERMOD worklist** show PTF IDs and source comments *before any live refresh*.
   Search for **Allocate DASD Space and Placement**: the workbook has
   `LU17113`, `LU19858` for the corresponding assessment row.
2. Open **Source Monitor** and click **Refresh Broadcom now**. This is a REAL
   request to the public vendor website, not a simulated refresh. Enable
   **Follow approved external detail pages** only if needed.
3. After a successful refresh, look at **Live PTF extraction coverage** on Source Monitor.
   It reports how many links yielded actual PTF identifiers and which require review.
4. Open **Compatibility Matrix**, filter to **Broadcom**, and inspect
   **Extracted PTF IDs**, **PTF availability**, **PTF ID source**, **PTF source URL**, **Last live scrape (UTC)**, and **PTF verification** columns.
5. Open **PTF Intelligence → Live Broadcom source evidence** for exact source links,
   PTFs and vendor text.

**What happens on failure?** The dashboard shows the real error and the last successful
snapshot is preserved. The `ptf_links_present` field is persisted and migrated for
existing databases, avoiding the earlier refresh `KeyError`. A PTF hyperlink by itself
is *not* treated as an actual PTF identifier, and missing live IDs do not erase known
workbook values.

## 6. Streamlit Community Cloud deployment (GitHub)

1. Unzip. Copy the CONTENTS of `zos_compatibility_intelligence` to a GitHub repository
   (not the outer ZIP). Commit `app.py`, `crawler.py`, `store.py`, `maintenance.py`,
   `workbook_data.py`, `data/`, the reference workbook, `requirements.txt`, and other files.
2. In [share.streamlit.io](https://share.streamlit.io/), choose **Create app**,
   your GitHub repository and branch, and main file path **`app.py`**.
3. Keep **Python 3.11 or 3.12** where the deployment option is available.
4. Deploy, then open **PTF Intelligence** first to check workbook values.
5. Open **Source Monitor → Refresh Broadcom now**; inspect any errors and extraction
   coverage in the app. If Cloud reports an HTTP timeout, rate limit, or vendor block,
   the website has not been successfully scraped. Check deployment logs.
6. **Cloud storage warning:** SQLite snapshots live under `state/` by default.
   Streamlit Community Cloud files can be lost when the app restarts or redeploys.
   For durable production history, use an external persistent database or host
   with a persistent filesystem. Never commit a populated SQLite DB with confidential data.

## 7. Automation: is it automatic?

- Clicking **Refresh Broadcom now** automatically crawls the vendor table, follows
  same-page maintenance details, saves snapshot data and updates the pages.
- **This is MANUAL initiation** by design. No daemon runs continuously inside Streamlit.
- To enable a scheduled refresh, run `python refresh_once.py` using cron, a scheduled
  GitHub Action, or another reliable external scheduler, **with persistent storage**.
  Use `ZOS_DB_PATH` to point to the shared SQLite path, if appropriate. Note that
  Streamlit Community Cloud and an external scheduler do not automatically share files.
- Only **Broadcom** is live-crawled. Other vendors are represented by the original
  CSV data and the AMXT workbook; they have no live crawling adapter yet.

## 8. Troubleshooting

| Symptom | What to check |
|---|---|
| `ModuleNotFoundError` | Activate the venv, rerun `python -m pip install -r requirements.txt` |
| Workbook not found | Keep `ISV Compatibility assessment -Data.xlsx` beside `app.py` |
| Missing vendors | Keep all six `data/*_compat.csv` files |
| `KeyError: ptf_links_present` | Ensure the newest **app.py + store.py + maintenance.py** were deployed together; restart the app |
| PTF links shown, but not IDs | Source detail may be blocked or changed; check Source Monitor extraction coverage and source URL |
| No saved history on Cloud restart | Use a persistent database; Cloud local storage is ephemeral |
| No data immediately after refresh | Check the refresh success message; vendor access or parsing may have failed |
| Cloud app prompts for login | You may need owner-provided Streamlit app access permissions |

## 9. Data accuracy

The `AMXT` sheet contains z/OS 3.2 assessments; its z/OS 3.1 values are **not guessed**.
PTF IDs in Excel are **workbook assertions**. Live PTF IDs are **vendor source observations**.
Neither verifies which PTFs are installed on your own mainframe. Always confirm
maintenance with your systems team and the vendor's current official documentation.

## 10. Offline validation

```bash
python -m unittest discover -s tests -v
python -m compileall -q .
```

Offline tests include older database migrations, preventing `ptf_links_present`
refresh errors, preserving workbook PTFs when a source detail is missing, and
parsing PTF IDs from nested tables and DOM elements after Broadcom detail anchors, without mixing products or z/OS releases.

**Limitations:** This release was statically compiled and exercised against the supplied
project and offline HTML fixtures. A real Broadcom crawl and a full Streamlit browser
session cannot be verified from the build environment because outbound access to
Broadcom and the Streamlit server are unavailable here. The testing-app URL redirects
unauthenticated viewers to Streamlit sign-in, so pixel-perfect visual parity cannot be
confirmed without accessible screenshots.

## 11. Why the previous downloaded CSV showed 0 IDs

Your `broadcom_scraped_ptfs.csv` contained 89 PTF-linked observations but no actual
PTF identifiers. The earlier crawler stopped reading at the next HTML row or at
an ordinary element ID. On Broadcom, the anchor can point to a detail section
with multiple nested tables and FMIDs beyond that boundary.

The parser now walks forward through the linked anchor's text nodes until the
next Broadcom detail anchor, collecting the PTF identifiers only from that
section. It includes regression fixtures for the published ACF2 16.0 and
Dispatch 11.6 layouts. These fixtures test code behavior, not a live crawl.

**After deployment:** a previous failed snapshot stays in SQLite until you
click Refresh Broadcom again. A fresh *successful* crawl is required before
the Source Monitor and exported CSV show newly scraped PTF IDs. If the live
site changes its structure, the monitor will still report unresolved IDs
instead of inventing values.

## 12. Data quality improvements — November 9, 2026

- **Do not confuse PTF identity with availability.** If the vendor or workbook says
  "not available" or "superseded", a separate status column preserves that
  statement. IDs are never interpreted as proof of availability or installation.
- **Keep source generations separate.** The compatibility export includes both
  **Extracted PTF IDs** (from the selected source) and **Workbook-mentioned PTF IDs**
  (historical AMXT text); the two are never blindly unioned when a live vendor
  PTF list is available. Workbook raw statements remain present.
- **Deep-link evidence.** The PTF source URL preserves `#section` fragments,
  rather than pointing only to the top of the vendor matrix.
- **Correct joins.** Match on vendor + normalized exact product name + release
  AND apply only to the correct z/OS version. A product not matched to the
  existing inventory is added separately, not guessed to be another product.
- **Clear freshness.** The dashboard shows the last successful snapshot UTC time.
  Blank timestamp = no successful live scrape for that record/version.
- **No false claims.** Classification such as "Not stated / verify" means
  the source did not explicitly establish PTF availability. Mixed or conditional
  vendor text still requires human review.
- **Source Monitor CSV** now includes availability wording, verification level,
  source deep links and last successful snapshot timestamp.

### Checking the export after refresh

1. Refresh Broadcom in **Source Monitor**, confirm a successful new snapshot.
2. Open **Compatibility Matrix**, choose z/OS 3.2 and Broadcom, download Excel.
3. Check the new source, status, UTC timestamp, historical-workbook-ID columns.
4. Do not interpret a historic workbook reference to a superseded/unavailable PTF
   as a currently installable maintenance requirement.
5. Compare a few PTF records manually against their **PTF source URL** before
   using the data for change approvals or migration readiness.

### Build limitations

The offline tests cover source provenance, status classification, matching,
workbook fallback and the previous crawler/database regressions. The software
cannot verify installed PTFs without a mainframe inventory. Full browser UI
and live source access were not available in this build environment.
