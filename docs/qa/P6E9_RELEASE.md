# P6E9 — Windows Python 3.11 launcher fallback preflight
Checked 2026-10-27 KST. Scope: local-first Windows owner release helper only; no hosted server or physical PC access.

## Problem / source evidence
`scripts/windows_release_qa.ps1` previously preferred any detected `py` command and immediately aborted when `py -3.11` failed. A usable Python 3.11 may still be reachable as `python` in PATH. The failure happens before `.venv-automl-qa`, fonts, tests or report generation. This was a static source-supported risk, **not** a recorded customer failure.

## Alternatives considered
1. **A — implemented:** validate `py -3.11` and then `python` in sequence using an explicit Python 3.11 version probe; fail closed if neither works. Provide `-ProbeOnly` for read-only CI checks prior to creating venvs or installing packages. No additional runtime dependencies or change in existing default and `-OpenBrowser` modes.
2. **B — not selected:** new Windows installer, environment manager or a separate Python discovery subsystem. Higher complexity/maintenance, no demonstrated necessity and may alter the user's global Python settings. No paid API or external data involved.

## Exact GitHub code changes
- [4358e8e](https://github.com/hibi89/AI_AutoML_Analyst/commit/4358e8e4a559faf1a9574114f099d6e210c2e7ad): `scripts/windows_release_qa.ps1` checks Python 3.11 on both launcher candidates, before all mutations. `-ProbeOnly` returns `PYTHON311_LAUNCHER=...` and stops without fonts, installs, venv creation or server launch.
- [d5fa54b](https://github.com/hibi89/AI_AutoML_Analyst/commit/d5fa54b489a30c808bfe7bd4df27f1f5742167c3): Windows Actions explicitly invokes the `-ProbeOnly` path, creates a temporary PATH-first broken `py.cmd`, verifies fallback to `python`, restores PATH in `finally`, then runs the existing native QA test suite. No global shell/python modification.
- This is only a launcher reliability fix. It does **not** prove the real owner's font, browser, ZIP extraction or PDF display.

## Verification ledger
- Previous verified baseline: [Windows 40458277827](https://github.com/hibi89/AI_AutoML_Analyst/actions/runs/40458277827) **67 PASS /9 warnings** on `45c6272`, [Linux 40458277791](https://github.com/hibi89/AI_AutoML_Analyst/actions/runs/40458277791) **125 PASS /2 Windows-only SKIP**, [Chromium 40458238868](https://github.com/hibi89/AI_AutoML_Analyst/actions/runs/40458238868) three SKU downloads on earlier app SHA.
- [Windows 40459009498](https://github.com/hibi89/AI_AutoML_Analyst/actions/runs/40459009498) on `4358e8e`: **IN PROGRESS** at initial record.
- [Windows 40459036865](https://github.com/hibi89/AI_AutoML_Analyst/actions/runs/40459036865) on `d5fa54b`: **IN PROGRESS** at initial record. This is the workflow that actually exercises `-ProbeOnly` and the broken `py.cmd` shim; final conclusion must be observed before declaring success.

## Release status / next
- Frozen objective: BASIC ₩60k, STANDARD ₩150k, PREMIUM ₩300k. P0–P6 acceptance **5/7 = 71%**; P1 physical Windows UX **PARTIAL**, P6 release **NOT ACCEPTED**; all tiers sale **NO-GO**.
- Only `feature/kmong-v1` is modified. Original `main@c80c874476f8d5deb4bf611761d89c6d72ca0a2d` remains unchanged; localhost-only product, Vercel/Production URL **NOT APPLICABLE**.
- **Next P6E10 candidate:** observe P6E9 CI; if failure occurs, inspect exact errors before at most one narrowed retry. After passing, continue other small source-supported preflight hardening if meaningful, otherwise leave owner physical QA as explicit blocked gate. Update `STATUS.md`, `HANDOFF.md`, ACTIVE_TASK.md and worker entrypoint with final fact-checked SHA. Do not merge, publicly deploy or list on Kmong without approval.

## Final P6E9 observed CI outcome — 2026-10-27 KST

- [Windows Actions 40459009498](https://github.com/hibi89/AI_AutoML_Analyst/actions/runs/40459009498): **SUCCESS** on launcher-code SHA `4358e8e4a559faf1a9574114f099d6e210c2e7ad`; **67 passed /9 warnings** from raw job log. This test executed existing regressions and a PowerShell parse, not the new fallback synthetic shim.
- [Windows Actions 40459036865](https://github.com/hibi89/AI_AutoML_Analyst/actions/runs/40459036865): **SUCCESS** on code+workflow SHA `d5fa54b489a30c808bfe7bd4df27f1f5742167c3`; raw Windows Python 3.11 test log **67 passed /9 warnings in 18.13s**. GitHub jobs separately confirmed successful **PowerShell parse**, **healthy Python 3.11 probe**, **temporary failing py.cmd fallback to valid python**, and **existing 67-test native QA**.
- This is evidence that a **CI-simulated failed `py` launcher** correctly falls back to another Python 3.11 executable; not proof of a real customer's first-install, font, PDF display, browser UI or configuration.
- No package versions, ML pipelines, customer-delivery archives, runtime routes, models, formats, global environment variables, external services, production settings or customer data changed. All modification belongs to development branch.
- **P6E9 code/CI complete. Next READY P6E10:** assess remaining independent no-owner QA opportunities or prepare the one physical Windows owner acceptance procedure; do not claim release GO without physical test and owner approval. P0–P6 **5/7=71%**, P1 PARTIAL, P6 IN PROGRESS, BASIC/STANDARD/PREMIUM **NO-GO**, Production/Vercel **N/A**, original main remains unchanged.
