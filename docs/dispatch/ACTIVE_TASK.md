# ACTIVE TASK — P6C release-depth verification
Updated: 2026-10-26 KST
status: READY
task_id: AUTO-KM-P6C
target_branch: feature/kmong-v1
predecessor: P0/P2/P3/P4/P5 implementation DONE, P1 Windows-browser acceptance PARTIAL, P6A/P6B engineering progress verified but **P6 release NOT ACCEPTED**.
next_after_success: P6 release gate can close only with actual evidence; P7 Kmong listing requires user approval.

## Latest verified facts
- Development GitHub `hibi89/AI_AutoML_Analyst`, `feature/kmong-v1`; `main` unchanged. Re-fetch latest SHA on every task.
- Linux Python 3.11 [Actions 40208598555](https://github.com/hibi89/AI_AutoML_Analyst/actions/runs/40208598555): **77 passed, 1 Windows-only skipped, 25 warnings**; generated BASIC, STANDARD, PREMIUM synthetic output and 11-page PREMIUM PDF. Maximum supported BASIC 20k×50 synthetic generation **1.00 s / 177,312 KiB max RSS** in Linux process (not guaranteed for clients; STANDARD/PREMIUM NOT benchmarked at cap).
- Windows native Python 3.11 [Actions 40208598494](https://github.com/hibi89/AI_AutoML_Analyst/actions/runs/40208598494): **39 passed / 6 warnings**, including actual `cmd.exe` `predict.cmd` invocation on locally serialized trusted skops model, correct 3 output predictions and prevention of result overwrite. Fixed CLI quoted trailing-path bug. This **does not** replace user Windows Edge/Chrome/PDF/first-install validation.
- Date-aware report chooses monthly trend instead of redundant box (5-chart cap), with box fallback on no-date and sparse data no filler. Downloaded synthetic final PREMIUM page render and chart inspected, 11 pages; whitespace still excessive in ML/Premium appendices.
- NAVER official Nanum fonts OFL commercial embedding review: `docs/qa/FONT_LICENSE_REVIEW.md`. No font binaries distributed; package license/installation audit remains.
- Detailed P6B evidence in `docs/qa/P6_RELEASE.md`; STRICT PROGRESS **5/7 accepted milestones, 71%**, P6 still open, no product sellable.

## Next engineering tasks, in order
1. **Release-grade PDF/layout**. Inspect actual generated BASIC, STANDARD, PREMIUM complete-page renders, reduce empty whitespace on ML introduction/interpretation/usage pages using legitimate data-driven summary panels (not fake insights), handle long Korean and ASCII column headers, chart annotation accuracy/units and 50-column column-table overflow; add visual or extraction tests. Keep 6–8/8–12/10–15 pages on representative supported inputs. Do not claim subjective visual approval from owner until received.
2. **First-install/browser**. Best effort add an automated Chromium/Edge GUI upload→ZIP smoke, if tooling permits, on Windows or Linux CI; explicitly identify platform. The actual user's Windows browser, Nanum font, ZIP extraction and interactive first-run remain OWNER TEST REQUIRED without connected desktop control. Provide one easy local deterministic command and evidence checklist; do not mark P1 completed merely from HTTP TestClient.
3. **Model resource/performance and abuse**. Benchmark genuine STANDARD/PREMIUM training at multiple size tiers, measure RSS/time, refuse workloads likely to stall or exhaust RAM; add test for limits and early multipart checks, malformed XLSX, big ZIP, long label report and clean errors. Do not generate or expose sensitive real CSVs.
4. **Environment reliability**. Produce known-good Python3.11 reproducible pinned requirements/lock evidence, identify high-risk vulnerable or conflicting dependencies, validate Naver font usage and Python package licensing in customer-facing kit, Windows Python minor and exact numpy/skops version compatibility. Avoid shipping font binaries.
5. **P6 gate**. Document actual test outcomes with CI URLs, independent Windows native CLI evidence, browser manual limitations, PDF renders, model assumptions, true tier-specific go/no-go. Update `STATUS.md`, `HANDOFF.md`, `ACTIVE_TASK.md`, `docs/qa/P6_RELEASE.md`; preserve `main` untouched. Do not claim P6 DONE or proceed to sale/listing without verified gates and owner approval.

## Never silently assume
CV/group/time leakage depends on true customer data semantics. SHA-256 is only file integrity, not author proof. Windows GitHub runner is not owner's desktop. The 20k×50 benchmark covers BASIC report generation, **NOT** heavy AutoML hyperparameter tuning. All three SKU sale flags remain NO.
