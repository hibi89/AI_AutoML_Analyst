# P6E4 — SKU-by-SKU release gate
Date: 2026-10-26 KST. Applies to `hibi89/AI_AutoML_Analyst@feature/kmong-v1`.

## Business boundaries and actual evidence
| SKU | Price | Implemented | Last proven automated evidence before P6E4 layout | Remaining release blocker | Sell? |
|---|---:|---|---|---|---|
| BASIC | KRW 60,000 | CSV/XLSX upload, data quality/KPI, grounded charts/insights, PDF & ZIP | Linux 105/1, Chromium actual ZIP, Windows non-GUI 50 PASS; synthetic 6-page PDF | Physical Windows Edge/Chrome, Korean licensed font, real ZIP and client-style visual approval | **NO-GO** |
| STANDARD | KRW 150,000 | BASIC + up to 3 non-Dummy models + Dummy, proper CV/holdout, model scores/plots, PDF & ZIP | Synthetic 9 pages, Windows headless/Chromium flows PASS | Same as BASIC plus target semantics/group-time leakage review and Windows realistic sample | **NO-GO** |
| PREMIUM | KRW 300,000 | Up to 5 non-Dummy + Dummy, limited tuning, trusted skops model, `predict.cmd`, fixed-schema repeat prediction | Synthetic 11 pages, tested Windows cmd.exe on CI runner + Chromium actual ZIP | Physical Windows extracted ZIP prediction/tamper/schema, private model delivery, library license/NOTICE and PDF approval | **NO-GO** |

Evidence pre-change:
- Linux [40214031425](https://github.com/hibi89/AI_AutoML_Analyst/actions/runs/40214031425) **105 passed /1 skipped**
- Windows runner [40214031452](https://github.com/hibi89/AI_AutoML_Analyst/actions/runs/40214031452) **50 passed**
- Chromium [40214031501](https://github.com/hibi89/AI_AutoML_Analyst/actions/runs/40214031501) **three file uploads/real ZIP downloads verified**
- Linux dependency CVE [40214119475](https://github.com/hibi89/AI_AutoML_Analyst/actions/runs/40214119475): installed 52 distributions; zero **known findings at time of scan**, **not a security warranty**.
- P6E4 PDF layout regression/results should be added only **after the CI finishes**, not assumed from prior green builds.

## Honest limits for customer-facing copy
- BASIC descriptive row limit: **20,000 rows / 50 original columns / 30 MiB upload**.
- STANDARD supervised row cap: **5,000 rows**, <=180 estimated encoded features and <=600,000 train cells.
- PREMIUM supervised row cap: **3,000 rows**, <=140 estimated encoded features and <=360,000 train cells.
- Never silently sample; no guaranteed chart count or ML accuracy/causation claim; explain non-representative, sparse/biased, target-leaked and future-label problems.
- The report is rule-based analysis (NOT a general-purpose LLM-generated report). Do not advertise as an LLM authored report.
- PREMIUM trained model retains category metadata and is not a public or anonymous deliverable.
- skops version 0.16.0 source license is MIT; see `docs/qa/P6E4_SKOPS_LICENSE.md`. Other transitive licenses, notices and actual distribution choices still require review.

## Necessary human steps before price/listing approval
Use `docs/qa/P6E3_WINDOWS_RELEASE_CHECKLIST.md` on a *physical* Windows machine with a licensed Nanum font: first installation; browser upload/download/unzip for each tier; new CSV repeat predictions; wrong schema/tamper/no overwrite; PDF visual signoff; confirm customer delivery terms. Record **PASS / FAIL / NOT RUN** and exact source SHA. GitHub runners cannot sign off those physical/UX gates.

## Completion metric
Strict P0–P6 milestone acceptance: **5/7 (71%)**, because P1 physical Windows remains PARTIAL and P6 final sale release remains IN PROGRESS. This figure is milestone completion, not percent of engineering hours remaining.

No Vercel deployment for local-first product, so production SHA/URL = NOT APPLICABLE. `main` preserved; no merger, public listing or sales authorization.

### P6E5 final code-SHA evidence reconciled (2026-10-26 KST)
- [Latest full Linux 40216846990](https://github.com/hibi89/AI_AutoML_Analyst/actions/runs/40216846990) **SUCCESS** on code SHA 'a0741885e481d32914b039e92e729775073be1e1': **111 passed / 1 Windows-only skipped /41 warnings**. Generated/rasterized STANDARD 9 and PREMIUM 11 pages plus BASIC 6; generated local synthetic 3-tier review pack, manifest PASS, PREMIUM Python model replay PASS. Linux branch correctly records Windows predict.cmd step NOT_RUN_NON_WINDOWS.
- [Latest Windows native 40216847015](https://github.com/hibi89/AI_AutoML_Analyst/actions/runs/40216847015) **SUCCESS** on same code SHA: **52 passed /9 warnings**, including local review generator pure tests and PowerShell syntax. This CI did not run the complete GUI/font-dependent owner script.
- [License/NOTICE audit 40216690129](https://github.com/hibi89/AI_AutoML_Analyst/actions/runs/40216690129) SUCCESS on license-code SHA '7c99dd0b095deccc0861288a9dbeacdd90a6b774': 52 packages with NOTICE/license file metadata, **10 obligation-review flags**, and 0 known vulnerabilities reported at scan time. Named licenses do not equal redistribution authorization.
- Manual physical Windows 3-tier browser/ZIP/PDF, exact packaged cmd replay by owner and aesthetic/legal approval remain NOT RUN/NOT APPROVED. No public/Vercel deployment, all SKUs NO-GO, strict 5/7 (71%). Documentation-only later SHAs inherit this tested code history but are not separate application test runs.
