# Three-day MVP-first execution roadmap
Owner: AI AutoML Analyst lead. Original code on main; approved dev ref: `feature/kmong-v1`.
Start target: 2026-10-26 KST; candidate checkpoint: 2026-10-28. **Aspirational; no promise of asynchronous work or release without testing.**

| ID | Priority | Sprint target | Acceptance / output |
|---|---|---|---|
| P0 | Critical | Day 1 early | Audit source and test availability; run original FastAPI + standalone smoke via trustworthy environment (GitHub Actions if local GitHub networking restricted); preserve main, establish real baseline failures. |
| P1 | Critical | Day 1 | One-file MVP: CSV -> profiling -> chart(s) -> report/export; one functioning classifier or regressor path; safe localhost handling. |
| P2 | High | Day 1/2 | Fix task detection, baseline challenger separation, candidate selection/truncation and CV edge cases. |
| P3 | High | Day 2 | BASIC SKU: 5 suitable visualizations, KPI/insights, branded Korean PDF 6–8 pages, CSV/XLSX summary, ZIP. |
| P4 | High | Day 2 | STANDARD: max 3 challengers + Dummy, scientifically appropriate splits, scoring, explanation & PDF 8–12p, results ZIP. |
| P5 | High | Day 3 | PREMIUM: max 5 challengers, trusted saved pipeline, reproducible new CSV predictions, report, Windows script, ZIP. |
| P6 | Release-gate | Day 3 | Valid input, missing target, unbalanced, group/time leakage, unsafe paths, size controls, Korean font, Windows prediction, artifact manifests, regression and security checks; fix blockers, don't claim ready otherwise. |
| P7 | Low | After gates | Sales demo + sample report with synthetic data, listing text/screenshots, version/tag only if approved and verified. |

## Method
- MVP FIRST. Do not stall on architecture docs; implement vertical slice P1 immediately once P0 validates or identifies the precise blocker.
- After each vertical slice, compare to `REQUIREMENTS.md` + `docs/product/SKU_MATRIX.md`; mark missing acceptance items explicitly.
- Keep one integration branch. Avoid branch proliferation. Commit small changes with tests and handoff notes.
- If one execution path fails twice without progress, pivot: repo CI, connected GitHub workflows, container from supplied ZIP, or write runnable tests and explicitly report execution blocker. Do not fabricate pass status.
- At each work boundary compute progress from actual accepted work items: denominator P0–P6 (7 items), rather than inflated hours/subjective points. Identify partially implemented separately.
- End-of-day status: BASIC sale ready? STANDARD sale ready? PREMIUM sale ready? Separate code complete vs passed QA vs commercial launch.
- Owner action only when truly needed (credentials, GitHub Actions policy, new paid services, external deployment, sensitive data approvals). Otherwise continue code work.

## Future expansion backlog — NOT in first release
CatBoost/XGBoost optional, advanced time-series, multi-file join/SQLite ingestion, background queue/cancellation, React UI, hosted SaaS, PostgreSQL, advanced MLOps, installer packaging.
