# ACTIVE TASK — P6B remaining client-release checks
Updated: 2026-10-26 KST
status: READY
task_id: AUTO-KM-P6B
target_branch: feature/kmong-v1
predecessor: P0, P2, P3, P4, P5 implementation DONE; P1 PARTIAL, P6 IN PROGRESS (design and basic security improvements).
next_after_success: only if P1/P6 verified, consider P7 listing.

## Context — latest verified current results
- Full CI https://github.com/hibi89/AI_AutoML_Analyst/actions/runs/40207446007 (code SHA `7bee655575b060a32a2dea1a4d69283343b3f267`): **70 passed, 25 warnings**, Linux Python 3.11 with all P0–P6 code regressions, real Korean PDFs, safe XLSX fixture loads and MIME/route tests.
- P6 shared `chart_design.py` / report scorecards applied to all tiers. Full 11-page PREMIUM output and graph PNGs retrieved and visually reviewed. Chinese/Korean glyphs not known broken; report has lots of whitespace. Preview sample at prior assistant conversation sandbox and GitHub Actions synthetic artifacts.
- P6 legacy path APIs forbidden, local Host/IP/Origin only, wildcard CORS removed and legacy upload capped; not a public deployment security approval. Bounded 1st-sheet XLSX (cached values only, no execution) now accepted alongside CSV on commercial routes.
- `scripts/windows_release_qa.ps1` created; NOT actually executed on Windows. All tiers not yet sellable.

## NEXT TASK — practical final QA and remaining improvements (same P6 milestone)
1. **PDF/graphic release polish**: inspect latest generated full PDF/PNG (BASIC, STANDARD, PREMIUM) at readable per-page resolution. Reduce sparse-page whitespace, review high-cardinality, non-Korean headers and long labels, ensure no raw categorical values and no dishonest unit extrapolation. Preserve 6–8 / 8–12 / 10–15 pages for supported synthetic representative data, never insert filler. Add rendering/typography regression tests where feasible.
2. **True Windows browser and repeat CLI**: where Windows execution environment can be accessed, run `scripts/windows_release_qa.ps1`, use proper licensed NanumGothic font, manually click each BASIC/STANDARD/PREMIUM upload→ZIP download with Chrome/Edge, unzip, install pinned model dependencies and run `predict.cmd` on new aligned CSV, wrong-schema and altered model tests. If Windows access unavailable, record OWNER-VERIFICATION-REQUIRED not PASS; do not treat Linux CI as Windows proof.
3. **Performance, licensing, abuse**: benchmark representative and upper bound 20k x 50 dataset (time, memory, oversized XLSX, malformed files, model training stall). Confirm no client upload leak, correct multipart size controls before parsing, errors redacted, local-only middleware robust, exported ZIP integrity/CSV formula guards. Audit package exact versions, Nanum font embedding/redistribution and model trust/copy rights. Avoid altering main. No external hosting.
4. **Final go/no-go**: update `docs/qa/P6_RELEASE.md`, `STATUS.md`, `HANDOFF.md`, keep P6 IN PROGRESS if any substantive gate unverified. Report exact tested source SHA and CI. Never mark BASIC/STANDARD/PREMIUM sellable or create paid listings without necessary acceptance. No user confirmation needed for ordinary dev-branch changes.

## Important safeguards
- Allowed: incremental code/testing/docs only on `feature/kmong-v1`.
- Forbidden without user approval: `main` merge, public deployment, repo visibility, billable APIs, real sensitive data upload or live customer sales.
- Model ZIP from origin is trusted by recipient only if obtained directly from product owner. SHA-256 does NOT establish issuer identity. No arbitrary pickle/untrusted skops loads.
- ML group/time leakage decisions and tuned-CV bias cannot be eliminated by styling; explicitly preserve scientific limitations.
