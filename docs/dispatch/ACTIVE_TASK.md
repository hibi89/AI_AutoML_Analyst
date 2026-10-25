# ACTIVE TASK — AUTO-KM-P6 commercial release gate
Updated: 2026-10-26 KST
status: READY
task_id: AUTO-KM-P6
target_branch: feature/kmong-v1
role: lead-engineer, QA owner
predecessor: P0 DONE, P1 PARTIAL (real browser pending), P2 DONE, P3 DONE implementation, P4 DONE implementation, P5 DONE implementation with 59/59 CI; no tier sellable.
next_after_success: P7 Kmong listings only for truly verified sellable tiers.

## Priority 0: report/graph polish before listing — user explicitly requested
Current BASIC graphs are intentionally functional MVP plots and **not commercial-quality**. Rewrite visual design coherently across BASIC/STANDARD/PREMIUM:
- Korean title/axis/unit, consistent font/color and chart sizes, legible labels and dynamic ticks, sensible typography/layout and high-DPI PNG embedding.
- Only honest, schema-supported charts, no filler (5 charts when data supports, fewer otherwise), no unlabeled 'N1'/'Group 1' without a clear privacy explanation. Protect customer category identities where user hasn't approved export.
- Fix sparse pages and overlarge whitespace, improve executive summary and chart annotations, stronger insight-to-chart mapping, meaningful highlight/KPI boxes without fabricated causal claims.
- Render every page of representative CSVs, compare generated PNG/page previews visually, check Korean glyphs/overlap and chart accuracy. Show user polished sample before listing.

## Priority 1: release safety + public exposure hardening
- Legacy `/api/folders/browse`, `/api/folder/scan`, `/api/analyze-path`, original `/api/analyze` and `/api/results` currently have broad CORS / filesystem and unbounded work. Deny/disable dangerous routes for commercial interface or enforce local origin/host/method and explicit scoped filesystem access; avoid breaking original saved tests without replacement.
- Harden input parsing (CSV/XLSX if promised), formula injection, target/column duplicate, unknown dtypes, huge row/col sizes, incomplete CSV, path traversal and ZIP-bomb, file rename/collision, bounded processing and error redaction. Add adversarial, regression, concurrency and performance tests.
- Reject unsafe/untrusted model bundles, signed provenance if truly needed (SHA only integrity), model-size and version compatibility, do not accept arbitrary pickle. Review `skops` allowlist and package dependency/font licenses. Keep real data local.
- Untrusted user-owned CSV/XLSX handled only on localhost and never committed. No hosting, payments, external data transfer or main merge without user approval.

## Priority 2: Windows/browser/portability
- Test actual Windows Python 3.11 install/first-run for all three tiers, font detection, Chrome/Edge `fetch`/download ZIP and output files, PowerShell/CMD prediction runner on a fresh same-schema CSV, wrong-schema and tampered-artifact rejection.
- If actual physical Windows environment is unavailable to the assistant, do not fake it; prepare a deterministic one-command local QA script and report owner action needed as final blocker.
- CI with Windows runner when possible to exercise non-GUI checks, plus Linux Python3.11 full suite (currently **59** tests).

## Priority 3: frozen SKU alignment, go/no-go
- BASIC 60k: CSV/XLSX accepted or narrow listing claim; 6–8 page PDF on supported sample, 5–10 actual KPIs and justified graphs.
- STANDARD 150k: 3 challengers + Dummy, independent holdout, 8–12 page PDF and appropriate chart/CSV/ZIP.
- PREMIUM 300k: 5 challengers + Dummy, top-two limited CV tuning, 10–15 page PDF, trusted skops, exact-version predict CLI, sample input schema and real tested repeat predictions. No accuracy guarantee.
- Document actual QA evidence and remaining blockers in `docs/qa/P6_RELEASE.md`, update STATUS/HANDOFF/ACTIVE_TASK and verify CI. Allow P7 listing only after P6 evidence passes; do not self-declare release ready.
- Keep `main` unchanged until separately approved. Continue on `feature/kmong-v1`.

## Current evidence to recheck
P5 Python 3.11 Actions run: https://github.com/hibi89/AI_AutoML_Analyst/actions/runs/40205977563 — 59 PASS, 19 warnings, 11-page PREMIUM synthetic PDF with 5+Dummy and top-two CV tuning. QA details `docs/qa/PREMIUM_P5.md`. Generated preview is synthetic, not customer data.
