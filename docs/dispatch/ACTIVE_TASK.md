# ACTIVE TASK — authoritative next work item
Updated: 2026-10-25 KST
status: READY
task_id: AUTO-KM-P3
target_branch: feature/kmong-v1
role: lead-engineer-and-implementer
predecessor: P0 DONE (6 tests), P1 BASIC MVP API PASS (UI manual unverified), P2 DONE (36 tests Python 3.11).
next_after_success: AUTO-KM-P4 in docs/dispatch/ROADMAP.md

## Task — finish sale-quality BASIC report from existing working MVP
Retain `/basic-mvp`, `/api/basic-report`, and original FastAPI/ML behavior. Use `backend/app/services/basic_report.py` as starting point. BASIC product spec: `REQUIREMENTS.md` and `docs/product/SKU_MATRIX.md`.

### Immediate development
1. Re-fetch live SHA, `HANDOFF.md`, `STATUS.md`, original code, QA `docs/qa/{BASELINE,MVP_P1,ML_P2}.md`. Verify final Python 3.11 CI run [40200745818](https://github.com/hibi89/AI_AutoML_Analyst/actions/runs/40200745818): 36 passed, 6 warnings.
2. Extend descriptive chart chooser to approximately five **meaningful** plots in a sufficiently rich synthetic dataset. Choose among missingness, numeric distribution, numeric correlation (meaningful columns only), categories, trend (only valid parsed dates), numeric box distribution. Avoid pointless filler charts and avoid raw labels/data in exports unless customer permits.
3. Build **real Korean PDF**, professionally paginated around 6–8 pages for a representative supported input; handle sparse datasets gracefully without padding or invented insights. Confirm Korean glyphs/font licensing and PDF rendering, embed fonts only as permitted. A simple reliable template beats an unverified fancy one.
4. Include meaningful 5–10 KPIs when possible, 3–5 grounded findings and up to 3 conditional suggestions; avoid causal/unwarranted accuracy claims and ensure output values are derived from the exact input.
5. Package `report.pdf`, `summary.csv` or `summary.xlsx`, suitable `charts/*.png`, `README.txt`, optionally `summary.json` in ZIP with manifest and validated filenames. No raw CSV/sensitive values by default.
6. Add input/negative/empty dataset, Korean headers, encoding, PDF page/text/image inspection tests; consider actual browser/download validation if supported. Keep localhost and upload caps.
7. Execute GitHub Actions actual tests, inspect logs. Record empirical ZIP/PDF evidence + limitations. Update STATUS/HANDOFF/ACTIVE_TASK and commit before end.

### P3 acceptance (not just a pretty PDF)
- Original P0/P1 and new P2 tests remain PASS (36 baseline tests).
- Representative synthetic CSV -> HTTP upload -> ZIP with readable PDF, suitable charts, summary CSV, Korean insights. Structural ZIP contents / PDF rendering / page count actually inspected in trustworthy environment.
- No private real input or model secrets; original `main` untouched.
- Release gate P6 and real Windows browser remain independent. **BASIC is not sellable until P3+P6.**

### Explicit non-goals
No paid LLM, no React rewrite, no SaaS/Vercel, no package installer, no ML fitting in BASIC. STANDARD/PREMIUM remain P4/P5.
