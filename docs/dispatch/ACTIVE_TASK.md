# ACTIVE TASK — AUTO-KM-P6E final product acceptance gate
Updated: 2026-10-26 KST
status: READY
target_branch: feature/kmong-v1
task_id: AUTO-KM-P6E6
predecessor: P0 P2 P3 P4 P5 implementation DONE, P1 PARTIAL (Linux Chromium real browser proven; owner Windows unverified), P6A/B/C/D engineering work verified, P6 release still IN PROGRESS.
next_after_success: P7 Kmong listing DRAFT only after tier-specific release criteria satisfied and owner approves.

## Exact latest proven P6D facts
- Linux full integration [40211592836](https://github.com/hibi89/AI_AutoML_Analyst/actions/runs/40211592836): **90 PASS, 1 Windows-only SKIP, 34 warnings**. BASIC/STANDARD/PREMIUM reports & PDF/ZIP generated with resource guards, confidential-category-safe ML feature ranking and explicit dropped input columns.
- Real Linux CI near-cap supervised stress [40211135507](https://github.com/hibi89/AI_AutoML_Analyst/actions/runs/40211135507): **STANDARD 5,000 rows × 50 columns 10.33 seconds peak 205,852 KiB; PREMIUM 3,000 × 50 10.79 seconds peak 215,136 KiB**, three-fold CV and independent holdout plus PREMIUM tuning, 69 estimated one-hot output features. Results limited to particular synthetic runner/data.
- ML operational caps: `ml_workload_policy.py` STANDARD <=5,000 rows, <=180 estimated encoded features, <=600,000 train cells; PREMIUM <=3,000 rows, <=140 features, <=360,000 train cells. BASIC keeps <=20,000 descriptive rows. Early transparent errors, **no silent sampling**. Legacy `/api/analyze` likewise row-guarded. UI discloses these.
- Latest successful Windows [40211572333](https://github.com/hibi89/AI_AutoML_Analyst/actions/runs/40211572333) and Chromium [40211572238](https://github.com/hibi89/AI_AutoML_Analyst/actions/runs/40211572238) for prior engine commit; actual Windows cmd.exe predict running tested in prior P6C. These are CI runner tests, NOT actual owner Windows Edge/Chrome.
- P6D PDF importance is train-fitted tree impurity/absolute coefficients, only when meaningfully available, OneHot category labels aggregated by original column to keep private values out of reports, no causality claims. Dropped high-cardinality identifier columns now disclosed.
- Preview from P6D PDF [40211407887](https://github.com/hibi89/AI_AutoML_Analyst/actions/runs/40211407887): 11 pages, Korean chart glyphs readable, **pages 5/7/10/11 visually too sparse**. Not user approved. `docs/qa/P6D_RELEASE.md` detailed.
- Direct dependency pins in `requirements-verified-py311.txt`; 14 direct license metadata entries and pip check clean. Full transitive vulnerability/licenses still review.
- **No tiers sale ready**, strict milestone completion P0–P6 **5/7=71%** until owner's Windows browser (P1) and final P6 signoff. Do not merge main or publish listing without approval.

## Next task P6E — PRIORITY ORDER
1. **Final report and chart design**: visually review all pages of actual BASIC (6), STANDARD (9), PREMIUM (11) sample and reduce excessive whitespace on pages 5/7/10/11 using real data-grounded content, not fake findings or blank padding. Preserve privacy and PDF page targets BASIC 6–8, STANDARD 8–12, PREMIUM 10–15 for representative rich data. Do PDF raster/overlap/long-name/Unicode tests; ask owner for style signoff only on actual improved sample.
2. **Physical Windows first-run**: owner must run `scripts/windows_release_qa.ps1 -OpenBrowser` on actual Windows Python3.11 with a licensed Nanum font, inspect actual Chrome/Edge downloaded ZIP for each SKU, unpack and execute PREMIUM `predict.cmd` new CSV, tamper and wrong-schema. If not physically available, record BLOCKED (not passed). GitHub Windows runner and Linux Chromium are separate evidence.
3. **Adversarial privacy/legal security**: audit all exported ZIP members and PDF for privacy-sensitive categories/raw rows; fail safely on malformed/oversized XLSX/CSV/formula injection; model `skops` trustworthy provenance; Python transitive license and package vulnerability checking; memory/time/row limits and error redaction. No public hosting.
4. **SKU specification diff & actual customer service boundaries**: claims and prices BASIC 60k STD150k PREM300k, number of models and charts only when data warrants; ML caps narrower than BASIC, communicate explicitly. Optional feature importance delivered only when valid; no unsupported importance or accuracy guarantees. Draft a tier-wise go/no-go based on verified evidence.
5. **Close P6 if and only if actual release gates succeed**. Update `STATUS.md`, `HANDOFF.md`, `ACTIVE_TASK.md`, `docs/qa/P6_RELEASE.md` and new P6E evidence. Main remains unchanged, no production deploy, credentials/data upload, paid API or real customer sale without approval.

## Reentry for next "ㄱ"
Fetch live GitHub dev HEAD, this ACTIVE_TASK, HANDOFF, STATUS, prior QA, code, actual latest CI runs. Execute next prioritized task directly; do not ask already-known details or claim asynchronous work. Maintain strict validation percentage rather than subjective impressions.


## P6E1 executed / P6E2 READY (2026-10-26 KST)
PREMIUM last two pages now use real model/CV/untouched-holdout/Dummy numbers and compact runbook, schema counts, ZIP inventory, privacy/provenance caveats; no invented customer scores. Added P6E Korean long-header/privacy/two-page layout regression. [Linux Actions 40212675598](https://github.com/hibi89/AI_AutoML_Analyst/actions/runs/40212675598) on code+test SHA `08dd90f244dc114f045284eb6d6f2b513d664b9b`: **91 PASS /1 Windows-only SKIP/34 warnings**, BASIC 6 / STANDARD 9 / PREMIUM 11 synthetic PDF pages generated. [Windows 40212557635](https://github.com/hibi89/AI_AutoML_Analyst/actions/runs/40212557635) and [Chromium 40212557611](https://github.com/hibi89/AI_AutoML_Analyst/actions/runs/40212557611) SUCCESS at executable SHA `38f68e9064acb3fc4d87193062748249a9026172`. PDF raster page creation verified; human visual signoff on these new pages NOT YET. Physical user's Windows Chrome/Edge/first-install/ZIP extraction still NOT TESTED. No external server deployment or customer data. P6E still IN PROGRESS; strict 5/7 (71%), all SKUs NO-GO. See `docs/qa/P6E_RELEASE.md`.

### Next actionable task: AUTO-KM-P6E2
1. Add negative tests for malicious/malformed CSV/XLSX, CSV formula escape, artifact member disclosure, model provenance warnings and safe failure; specifically distinguish safe synthetic categories from confidential labels. Inspect actual ZIP/PDF names rather than assume `no_raw_dataset=true` proves privacy.
2. Review the new 11-page PREMIUM synthetic PDF visually from the latest Actions artifact; test rich vs sparse datasets, long header rendering and layout. Do not mistake raster success for owner design approval.
3. Audit package transitive licenses/vulnerabilities where trustworthy evidence is accessible without sending customer data; record explicit not-checked fields.
4. Owner physical Windows/Chrome/Edge flow with `scripts/windows_release_qa.ps1 -OpenBrowser` is still NOT RUN. No production, sale, merge, or acceptance claim. Update docs and CI after implementation.


## P6E2 DONE / P6E3 READY (2026-10-26 KST)


## P6E2 verified security and visual QA (2026-10-26 KST)
- Code changes: CSV parser input bound + safe error redaction, model CV error private-string redaction, XLSX duplicate/case-variant macro/external-link rejection; new `tests/test_p6e_adversarial.py`. All synthetic.
- [Linux 40213253212](https://github.com/hibi89/AI_AutoML_Analyst/actions/runs/40213253212) at `801c4ddad9db2644604c79b7fde8277fad53a085`: **100 PASS /1 Windows-only SKIP/41 warnings**; BASIC 6/STANDARD 9/PREMIUM 11 PDF pages. [Windows 40213192384](https://github.com/hibi89/AI_AutoML_Analyst/actions/runs/40213192384) and [Chromium 40213192440](https://github.com/hibi89/AI_AutoML_Analyst/actions/runs/40213192440) SUCCESS at implementation SHA `76e60f256ff1c479dd815722b7aee58c1d26f913` (tests-only later).
- Downloaded/visually inspected 11-page P6E1 PREMIUM PDF: no obvious Korean glyph failure/clipping at montage resolution; page 5/6/7/10/11 whitespace persists, aesthetic signoff still pending. Checked CI pip freeze **46 packages**, direct license metadata only 14; actual CVE scanner NOT RUN; skops exact upstream license still review.
- Tier readiness **BASIC NO / STANDARD NO / PREMIUM NO**; P1 PARTIAL (owner physical Windows browser NOT RUN), P6 IN PROGRESS; strict **5/7=71%**. See `docs/qa/P6E2_RELEASE.md`.
- **Next READY AUTO-KM-P6E3:** free reproducible CVE/transitive-license scan and triage, malformed/wide/memory boundary QA, final PDF layout and owner Windows check. No public deploy, main merge, sales release, paid services, or customer data access.

Execution sequence for next `ㄱ`: 1) check exact live branch and CI, 2) version-scope third-party audit (do not guarantee zero vulnerabilities if tool not run), 3) adversarial near-boundary workload tests and truthful failure behavior, 4) new synthetic visual review, 5) update docs. Physical owner Windows/Chrome/Edge remains owner-action REQUIRED; P7 and P6 sale-go still blocked.


## P6E3 DONE / P6E4 READY (2026-10-26 KST)


## P6E3 verified: patched dependencies & boundary QA (2026-10-26 KST)
- Implemented full 52-package Linux inventory + free known-CVE audit, preserving audit evidence even when fail; first [40213847811](https://github.com/hibi89/AI_AutoML_Analyst/actions/runs/40213847811) **FAILED** with 37 Pillow + 3 setuptools advisory entries; fixed pinned `Pillow==13.0.0`, audit-runner `setuptools==84.2.1`.
- Re-audit [40214119475](https://github.com/hibi89/AI_AutoML_Analyst/actions/runs/40214119475) **SUCCESS / 0 known CVE entries reported** (scope: installed Linux Python3.11 packages). Specific skops license is **MANUAL REVIEW**, since its metadata only states "OSI Approved"; scan is not legal certification.
- Added 5 near-boundary CSV/XLSX/413/invalid-header regressions. Pillow13 [Linux 40214031425](https://github.com/hibi89/AI_AutoML_Analyst/actions/runs/40214031425) **105 PASS/1 Windows-only SKIP/41 warnings**, BASIC 6 / STD 9 / PREM 11 PDF pages; [Windows 40214031452](https://github.com/hibi89/AI_AutoML_Analyst/actions/runs/40214031452) **50 PASS/9 warnings**. [Chromium 40214031501](https://github.com/hibi89/AI_AutoML_Analyst/actions/runs/40214031501) pending observed completion at this doc update (previous Pillow13 Chromium [40213990390](https://github.com/hibi89/AI_AutoML_Analyst/actions/runs/40213990390) SUCCESS).
- Inspected actual Pillow13 PREMIUM 11-page synthetic raster: legible Korean/plots, but pages 5/6/7/10/11 sparse; owner design acceptance **NOT GIVEN**. Physical owner's Windows release QA **NOT RUN**. No sale/production/merge permitted; all tiers NO-GO, strict progress **P0–P6 = 5/7 (71%)**. No Vercel/Production for localhost-only app; original `main@c80c8744` unchanged.
- Detailed source `docs/qa/P6E3_RELEASE.md`; owner acceptance `docs/qa/P6E3_WINDOWS_RELEASE_CHECKLIST.md`. **Next READY AUTO-KM-P6E4**: verify latest Chromium, improve real-content PDF density, complete skops/third-party license and Windows manual readiness, tier-specific go/no-go. GitHub dev latest SHA should always be fetched live.

P6E4 success criteria: inspect latest real Chromium and CVE audit status; improve meaningful PDF report density without invented claims; run render/page-count/security regression; resolve exact skops license and owner-local Windows release evidence as feasible. Never mark manual gate passed by GitHub CI alone. All 3 SKU sales NO-GO, main untouched.


### Post-capture final Chromium outcome (2026-10-26 KST)
- [Pillow13 Chromium 40214031501](https://github.com/hibi89/AI_AutoML_Analyst/actions/runs/40214031501) **SUCCESS** on executable SHA `5f94e026f31d17f625857ff934cb3b81693c6173`. Real Playwright Chromium selected file, clicked report/download and verified actual ZIP output: BASIC **479,693 bytes**, STANDARD **632,150 bytes**, PREMIUM **726,447 bytes**. These are synthetic CI-only artifacts, not a customer's Windows Chrome/Edge manual approval.
- Latest verified matrix therefore Linux **105 PASS/1 SKIP**, native Windows **50 PASS**, Chromium **3 SKUs PASS**, Linux all-installed direct+transitive audit **52 packages / 0 known CVE reports**; all on relevant tested code/dependency state. Strict release progress remains **5/7 (71%)**, all tiers NO-GO until physical Windows, licensed distribution and design signoff.


## P6E4 DONE / P6E5 READY (2026-10-26 KST)


## P6E4 completed engineering increment (2026-10-26 KST)
- New source-grounded Q1/median/Q3 table on lone-chart PDF page, ML-column feasibility audit on BASIC final page, and actual model-success/CV-vs-Dummy panel on STANDARD methodology page. Edited `basic_p3.py`, `standard_delivery.py`, updated P3/P4 tests. No invented target choice, data points or model accuracy.
- Initial STANDARD report syntax error at `ec8d432...` caused CI collection failure ([40215234937](https://github.com/hibi89/AI_AutoML_Analyst/actions/runs/40215234937)), corrected; last **tested application SHA `62e3bdc4c3afe584f77f6b06cfe43a3a8a72b185`**. Full [Linux 40215434575](https://github.com/hibi89/AI_AutoML_Analyst/actions/runs/40215434575): **105 PASS/1 SKIP/41 warnings** and BASIC 6/STD 9/PREM 11 rasterized pages; [Windows 40215434541](https://github.com/hibi89/AI_AutoML_Analyst/actions/runs/40215434541): **50 PASS/9 warnings**; [Chromium 40215434538](https://github.com/hibi89/AI_AutoML_Analyst/actions/runs/40215434538): three actual SKU browser ZIP downloads PASS.
- Visually inspected final 11-page PREMIUM and BASIC/STD contact sheets: pages 5/6/7 denser, no obvious Korean clipping/overlap at montage scale; pages 2/10/11 remain spacious, customer aesthetic approval NOT GIVEN.
- Exact `skops 0.16.0` source license at attested release commit `bcc69da...` verified **MIT** (Hugging Face copyright notice conditions); all other transitive-license distribution obligations still PARTIAL. Docs: `docs/qa/P6E4_RELEASE.md`, `docs/qa/P6E4_SKOPS_LICENSE.md`, `docs/qa/P6E4_TIER_RELEASE_GATE.md`.
- Sale gate: **BASIC/STD/PREM all NO-GO** pending physical owner's Windows + browser + new-CSV model replay and remaining legal/design approval. `P0–P6 = 5/7 (71%)`, P1 PARTIAL, P6 IN PROGRESS. Original `main@c80c8744` unchanged. No production/Vercel (NOT APPLICABLE); no customer data, credentials, paid APIs, main merge.
- Next READY **AUTO-KM-P6E5**: final visual owner signoff and remaining explicit whitespace policy, transitive license NOTICE inventory and physical Windows release evidence; honest GO/NO-GO.

P6E5 acceptance: physical Windows owner tests/explicit approval if available, source licensing and real-client PDF visual quality; keep all SKU commercial GO/NO-GO closed until every applicable acceptance gate passes. Compare `docs/qa/P6E4_TIER_RELEASE_GATE.md` and update per-tier decisions from actual evidence, not optimism. No main merge, external deploy, visibility change, or payment.


## P6E5 implementation verified / P6E6 READY (2026-10-26 KST)

## P6E5 engineering verified / sale NOT approved (2026-10-26 KST)
- Full license/NOTICE inventory: 52 installed Linux packages with file metadata/hash evidence, 10 packages flagged for targeted legal notice analysis (MPL, dual, custom, compound terms), no source license bytes in artifacts. [Audit 40216690129](https://github.com/hibi89/AI_AutoML_Analyst/actions/runs/40216690129) SUCCESS, 0 known advisory findings in this scan. Metadata availability is NOT legal clearance.
- Windows owner preflight script now uses gitignored project-only '.venv-automl-qa' (no global pip installation), runs tests and generates a fresh synthetic three-tier pack. 'qa-preview/' ignored; generated model/ZIP not shared by CI.
- Portable 'scripts/p6e5_windows_demo.py' generates BASIC 6 / STANDARD 9 / PREMIUM 11 pages, verifies ZIP hashes and replays 3 synthetic PREMIUM rows; actual Windows predict.cmd replay is guarded by platform and requires execution on Windows.
- [Linux full 40216591008](https://github.com/hibi89/AI_AutoML_Analyst/actions/runs/40216591008) at '0a5988e0d847' **110 passed, 1 skipped**, synthetic ZIP/PDF and Python model replay PASS. [Windows 40216847015](https://github.com/hibi89/AI_AutoML_Analyst/actions/runs/40216847015) at code 'a0741885e481' **52 passed, 9 warnings**; static PowerShell parse/Windows tests PASS, NOT owner physical execution. The subsequent [Linux 40216846990](https://github.com/hibi89/AI_AutoML_Analyst/actions/runs/40216846990) on 'a0741885e481' was still running at evidence write; check conclusion before claiming final Linux PASS.
- 'docs/qa/P6E5_RELEASE.md' and 'docs/qa/P6E5_WINDOWS_OWNER_RUNBOOK.md' contain all evidence and user-machine procedure. P6E4's intentional whitespace remains; no fabricated fillers added; final aesthetic signoff NOT GIVEN.
- All three SKUs (60k/150k/300k KRW) still **NO-GO**, strict milestone progress **5/7 (71%)**. P1 owner Windows PARTIAL, P6 release IN PROGRESS. Original 'main@c80c8744' unchanged. No production/Vercel deployment (NOT APPLICABLE). No real customer data, secrets, payments or public model ZIP.
- Next READY: AUTO-KM-P6E6: finish ten targeted license obligations and actual selected delivery method; collect real physical Windows/Edge/Chrome + PDF owner approval only when available; no merge/listing until gates are passed.

P6E6 next acceptance work: actual version-scoped 10 package licensing/NOTICE obligations by distribution modality, final latest Linux CI confirmation, actual physical Windows owned browser/ZIP/PDF/command approval. Keep automated Windows runner distinct from physical owner. P7 listing and per-tier GO require owner permission. No customer data or global software changes.

### P6E5 final code-SHA evidence reconciled (2026-10-26 KST)
- [Latest full Linux 40216846990](https://github.com/hibi89/AI_AutoML_Analyst/actions/runs/40216846990) **SUCCESS** on code SHA 'a0741885e481d32914b039e92e729775073be1e1': **111 passed / 1 Windows-only skipped /41 warnings**. Generated/rasterized STANDARD 9 and PREMIUM 11 pages plus BASIC 6; generated local synthetic 3-tier review pack, manifest PASS, PREMIUM Python model replay PASS. Linux branch correctly records Windows predict.cmd step NOT_RUN_NON_WINDOWS.
- [Latest Windows native 40216847015](https://github.com/hibi89/AI_AutoML_Analyst/actions/runs/40216847015) **SUCCESS** on same code SHA: **52 passed /9 warnings**, including local review generator pure tests and PowerShell syntax. This CI did not run the complete GUI/font-dependent owner script.
- [License/NOTICE audit 40216690129](https://github.com/hibi89/AI_AutoML_Analyst/actions/runs/40216690129) SUCCESS on license-code SHA '7c99dd0b095deccc0861288a9dbeacdd90a6b774': 52 packages with NOTICE/license file metadata, **10 obligation-review flags**, and 0 known vulnerabilities reported at scan time. Named licenses do not equal redistribution authorization.
- Manual physical Windows 3-tier browser/ZIP/PDF, exact packaged cmd replay by owner and aesthetic/legal approval remain NOT RUN/NOT APPROVED. No public/Vercel deployment, all SKUs NO-GO, strict 5/7 (71%). Documentation-only later SHAs inherit this tested code history but are not separate application test runs.
