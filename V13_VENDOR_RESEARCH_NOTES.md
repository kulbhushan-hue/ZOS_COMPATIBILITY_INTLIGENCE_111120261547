# V13 vendor reference verification notes (2026-11-10)

Public pages inspected during development; these are **source leads**, not claims that every site successfully scrapes from the user's machine.

| Vendor | Page / result | Structured use |
|---|---|---|
| Broadcom | ftpdocs.broadcom.com/WebInterface/phpdocs/0/MSPSaccount/COMPAT/zos_compat.HTML | Existing V12 compatibility and linked PTF extraction retained |
| BMC | https://docs.bmc.com/xwiki/bin/view/Mainframe/Ops/BMC-AMI-Capacity-Management/bacm263/Planning-and-installing/System-requirements-for-product-installation/Support-matrix/ | z/OS 3.2 matrix support and minimum product version 2.5.00; retains release caveat |
| BMC | https://docs.bmc.com/xwiki/bin/view/Mainframe/Ops/BMC-AMI-Ops-User-Interface/baoui31/Planning/Requirements/ | z/OS minimum software requirements, not z/OS 3.2 certification |
| Precisely | https://www.precisely.com/support/mfx-support-lifecycle-schedule/ | MFX 3.1.x and **minimum** z/OS, not 3.2 support certification |
| Precisely | https://community.precisely.com/discussion/ironstream-for-ibm-z-now-compatible-with-zos-32 | Product-family z/OS 3.2 support announcement, exact release unstated |
| Precisely | https://community.precisely.com/communities/community-home/digestviewer/viewthread?CommunityKey=7c7e9f48-d241-4b84-b51b-de5c87031097&GroupId=619&MessageKey=25d31b1d-a2e4-472b-a890-2b3975a6f533 | Ironstream 2.1.12 service pack publishes SDF21QS etc.; no installation claim |
| Vanguard | https://www.go2vanguard.com/product-support-eol-schedule/ | published min/max z/OS tested range per product release |
| Action Software International | https://actionsoftware.com/support-form/release-history/ | eventACTION/ussACTION release compatibility ranges, with separate EOS caveat |
| Rocket | https://www.rocketsoftware.com/en-us/events/tmon-modernization-2025-ai-and-data-streaming | TMON z/OS 3.2 support announcement without exact TMON version |
| IBM | https://www.ibm.com/software/reports/compatibility/clarity/index.html | SPCR report portal; product-specific reports frequently return JS shell or 'no product data' message, neither certifies compatibility |
| ASG / Rocket | https://www.rocketsoftware.com/sites/default/files/resource_files/tmon-zos.pdf | PDF source, requires actual readable PDF text for claims |

The project includes 29 workbook vendors, but not all 29 have reachable, product-specific documentation. One app cannot make an authentication-restricted source publicly readable. Some official sites return HTTP 403 or 404; such URLs remain unresolved instead of being automatically treated as support evidence.
