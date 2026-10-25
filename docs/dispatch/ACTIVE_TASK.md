# ACTIVE TASK — P6D tier-specific last-mile release checks
Updated: 2026-10-26 KST
status: READY
task_id: AUTO-KM-P6D
target_branch: feature/kmong-v1
predecessor: P0/P2/P3/P4/P5 implementation DONE; P1 PARTIAL Linux Chromium real browser passed (owner Windows pending); P6A/P6B/P6C technical checks passed but P6 release **NOT ACCEPTED**.

## Authoritative P6C evidence
- [Linux Python 3.11 40210003500](https://github.com/hibi89/AI_AutoML_Analyst/actions/runs/40210003500): **78 PASS/1 Windows-only SKIP/25 warnings**; normal synthetic PDF+ZIP, all 14 direct dependency versions pinned and pip check clean.
- [Windows native 40210007786](https://github.com/hibi89/AI_AutoML_Analyst/actions/runs/40210007786): **39 PASS**, exact pinned Python3.11 deps; actual trusted skops `cmd.exe` `predict.cmd` and collision refusal.
- [Linux Chromium 40210012769](https://github.com/hibi89/AI_AutoML_Analyst/actions/runs/40210012769): **BASIC/STANDARD/PREMIUM real browser file picker→click→download→verify ZIP all PASS**. Browser runs headless on Linux only; not owner's Windows.
- [CI 40209596783](https://github.com/hibi89/AI_AutoML_Analyst/actions/runs/40209596783) full baseline/pip+license inventory artifact, model benchmark: 2,000-row synthetic STD **~1.92s**, PREMIUM **~5.58s** (7 input features), not upper-limit capacity or real customer SLA. Direct dependency list pinned in `requirements-verified-py311.txt`.
- Visually inspected 11-page PREMIUM PDF from final pinned preview artifact, Korean glyphs/plots visible; ML methodology now includes evidence table. Significant whitespace persists; cannot claim client design signoff.
- User-local PowerShell `scripts/windows_release_qa.ps1 -OpenBrowser` launches uvicorn locally and opens all three pages after non-GUI preflight, but **not actually run on owner's PC**. No main merge or hosting.
- Source documents `docs/qa/P6C_RELEASE.md`, `docs/qa/P6_RELEASE.md`, `STATUS.md`, `HANDOFF.md`. Strict accepted 5/7 = 71%; all SKUs NOT SELLABLE.

## P6D exact prioritized next execution
1. **Stress-test STANDARD/PREMIUM near plausible workload limits**: multiple category cardinalities/target classes, 5k–20k rows and 20–50 fields as allowed by system policy, record real time/RSS and early clean failure, do not overpromise 20k×50 model fit from prior 2k×7 result. Add explicit tier-specific resource guards if needed, communicate narrower listing scope before sale. Confirm no destructive cleanup or model trust bypass.
2. **Windows fresh GUI QA**: run the owner script on actual Windows (Nanum licensed font installed; Python 3.11), browser click and ZIP extraction for all 3 tiers, PREMIUM new CSV `predict.cmd`, wrong-schema/tamper/error behavior. Add CI PowerShell syntax/launch tests as possible; do NOT claim owner's PC GUI done without evidence. Send a concise one-command owner checklist when a physical action is unavoidable.
3. **Report and data issues**: remove excessive blank space from quality/ML pages without invented content, verify long legal/finance headers, Unicode and 50-column table overflow, share final report for user's subjective design approval; check charts' truthful labels, unit annotations, ML metric/feature importance if appropriate.
4. **Security and reproducibility**: reject pathological XLSX/CSV/corrupted zip/oversize multipart, benchmark peak RSS/cancellation, review exact Python direct and transitive licenses + vulnerabilities and font distribution terms; require locally trusted model source. Evaluate fixed ZIP contents against frozen SKU and verify safe CSV outputs.
5. **Tier-specific GO/NO-GO**: document actual runtime, Windows/GUI, font/legal, final asset contents, merchant claims/limits. Update `STATUS.md`, `HANDOFF.md`, `ACTIVE_TASK.md`, P6 QA docs with observed CI SHA. P6 accepted only when no critical gate remains; move to listings only with user approval.

## Safety invariants
All development on `feature/kmong-v1`, `main` unchanged, no public hosting, paid calls, real customer data or repo visibility changes. Missing proof == BLOCKED, not PASS. SHA-256 is an integrity check and does not authenticate model origin. CV leakage and customer data semantics still require human verification. The 71% milestone percentage is an evidence criterion and not an estimate of time.
