# ACTIVE TASK — AUTO-KM-P6E final product acceptance gate
Updated: 2026-10-26 KST
status: READY
target_branch: feature/kmong-v1
task_id: AUTO-KM-P6E
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
