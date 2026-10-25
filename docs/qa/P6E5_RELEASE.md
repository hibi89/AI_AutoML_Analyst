# P6E5 — local owner review pack and license obligation triage
Recorded 2026-10-26 KST. Local-first product, no Vercel deployment. **No customer data, no paid API, no production launch.**

## Actual implementation
- 'scripts/p6e5_license_notices.py': reproducible 52-distribution Linux inventory with declared licenses, license/NOTICE file names/sizes/SHA-256, exact skops-0.16.0 upstream MIT provenance. No third-party license file bytes uploaded. Distinguishes *a named license* from actual notice/redistribution obligations.
- 'tests/test_p6e5_license_notices.py': synthetic no-disclosure tests, MIT/upstream exact-version check, dual/MPL/compound license risk rules.
- Existing CVE audit CI now runs this script and retains an evidence JSON next to pinned dependency versions and 'pip-audit' results.
- 'scripts/windows_release_qa.ps1': Python 3.11 QA runs only in gitignored '.venv-automl-qa', not global pip, and launches a synthetic review pack. PowerShell syntax validated in Windows CI, but the actual owner's PC has **NOT** run it.
- 'scripts/p6e5_windows_demo.py': Linux-and-Windows compatible demo (no pdftoppm) creates 150-row synthetic basic and ML CSVs, ZIP/PDF for all three tiers, validates ZIP manifest hashes and page-count contracts, and replays three PREMIUM synthetic predictions. On **real Windows execution only** it additionally runs the shipped 'predict.cmd' and checks output; Linux summary accurately records this Windows step NOT_RUN.
- 'qa-preview/' and '.venv-automl-qa/' are gitignored. Review pack creates a **new** run directory and never replaces previous results. ZIP/model remains local; CI uploads only a synthetic JSON summary with hashes/status, not trained model/ZIP/data.
- Owner guide: 'docs/qa/P6E5_WINDOWS_OWNER_RUNBOOK.md'. No owner-machine action has occurred.
- Sparse PREMIUM instructional pages 10/11 retain deliberate breathing room: neither fabricated metrics nor filler chart was inserted. Aesthetic signoff still requires actual customer-owner review.

## Executed CI evidence
- [Latest full Linux with local owner pack 40216591008](https://github.com/hibi89/AI_AutoML_Analyst/actions/runs/40216591008) at workflow SHA '0a5988e0d847': **110 PASS /1 Windows-only SKIP/41 warnings**, original BASIC/STD/PREM PDF 6/9/11 page proofs, newly built synthetic pack 6/9/11 and manifest PASS, premium Python replay 3 synthetic rows. A subsequent purely Windows-conditional cmd replay source addition at 'a0741885e481' requires separate full Linux run evidence.
- [Windows 40216847015](https://github.com/hibi89/AI_AutoML_Analyst/actions/runs/40216847015) at source SHA 'a0741885e481': **52 PASS/9 warnings**, includes PowerShell script syntax parsing and synthetic pack base tests. It did **not** execute the full local owner flow (requires font/GUI); Windows packaged batch semantics have existing dedicated regression.
- [Full license and CVE audit 40216690129](https://github.com/hibi89/AI_AutoML_Analyst/actions/runs/40216690129): **52 installed package metadata entries**, 52 packages with local license/NOTICE file hash evidence, 0 missing direct dependencies and **0 known vulnerabilities reported** by the current database. **10 manual obligations** flagged, not cleared.

## Ten flagged NOTICE/redistribution review items
1. certifi 2026.10.23 — MPL-2.0 file-level conditions
2. contourpy 1.3.3 — nontrivial license/copyright text
3. cycler 0.12.1 — nontrivial license/copyright text
4. kiwisolver 1.5.1 — license agreement text
5. matplotlib 3.11.2 — license agreement text
6. numpy 2.4.6 — multiple SPDX licenses joined by AND
7. packaging 26.3 — multiple SPDX alternatives joined by OR
8. pandas 2.3.3 — long copyright and license text
9. python-dateutil 3.0.0 — dual license selection
10. scipy 1.17.1 — long copyright and license text

These **flags are not exploit findings, violations, or proof commercial use is prohibited**. Each package's actual terms must be reviewed in context of whether Python wheels are redistributed or customers install dependencies independently. The product currently distributes an analysis ZIP/model/script and requirements, **not vendored Python wheels**; confirm the final packaging before applying notice policy. Font embedding/install rights remain separate. A green scanner is not a legal release certificate.

## Commercial / deployment / blockers
- Required physical Windows first-use install and three actual Edge/Chrome file-upload/downloads: **NOT RUN**.
- Real owner visual signoff on Korean PDFs: **NOT APPROVED**; explicit signoff required, no filler claims.
- Actual Windows 'predict.cmd' inside owner-generated ZIP: **NOT RUN ON OWNER'S PC**. New automation is prepared for that machine; passing CI does not substitute.
- Legal/distribution assessment for 10 flagged third-party packages and embedded Korean font: **PARTIAL**.
- BASIC KRW 60k / STANDARD KRW 150k / PREMIUM KRW 300k: all **NO-GO** for sale. No main merge or public deployment approved. Production URL/SHA and Vercel status: **NOT APPLICABLE**.
- Strict P0–P6 acceptance remains **5/7 (71%)**: P1 PARTIAL (owner Windows gate), P6 IN PROGRESS (release design/licenses/security/packaging).
- Original main SHA 'c80c874476f8d5deb4bf611761d89c6d72ca0a2d' preserved. Dev SHA must be fetched live.

## Next READY AUTO-KM-P6E6
1. Confirm final latest Linux three-tier owner-pack CI after Windows-cmd script enhancement and reconcile actual SHA.
2. Complete targeted license NOTICE analysis for the 10 flagged packages and source terms, not a blanket zero-risk claim. Separate pip-installed components vs bundling from actual delivery design.
3. Prepare final versioned synthetic review evidence and owner-specific physical Windows signoff fields. Close only gates substantiated by tests/owner evidence. No manual GUI PASS without actual owner report.
4. If remaining PDF whitespace is reviewed and approved, preserve it; do not invent findings for page density. Keep all tiers NO-GO until full approval.
