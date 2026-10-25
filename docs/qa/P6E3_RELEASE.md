# P6E3 — security remediation, resource boundaries, release blocking QA
Updated: 2026-10-26 KST. Branch `feature/kmong-v1`. **No external deployment or real customer data.**

## Executed changes
- Added `scripts/p6e3_dependency_audit.py` and `.github/workflows/p6e3-dependency-audit.yml`. This records installed **direct and transitive** distributions, exact versions, available license metadata and a `pip-audit --no-deps` JSON report. The security workflow fails if vulnerabilities or audit errors are detected; failed-run artifacts are retained for triage. No customer inputs or font binaries uploaded.
- Added `tests/test_p6e3_limits.py`: exactly 20,000 CSV rows accepted; 20,001 rejected without silent truncation; 50-column ragged XLSX preserved; 20,001-data-row XLSX rejected; oversized local upload returns 413; overlong header returns 400 without reflecting content.
- Initial [dependency audit 40213847811](https://github.com/hibi89/AI_AutoML_Analyst/actions/runs/40213847811) **FAILED deliberately** (security gate), detecting 40 advisory entries across `Pillow==12.3.0` (37) and `setuptools==79.0.1` (3). These are scanner-reported entries, not necessarily unique CVEs.
- Remediation: `requirements-verified-py311.txt` now pins `Pillow==13.0.0` for Python 3.11; `requirements-ci.txt` broad CI range aligned to `Pillow>=13.0,<14`; audit workflow upgrades **only its own build-time setuptools** to `84.2.1` before freezing dependencies. The owner's global Windows Python or unrelated environments were not modified. Pillow 13 is a major upgrade: full Python/PDF/browser regression was required.
- [Patched audit 40214000184](https://github.com/hibi89/AI_AutoML_Analyst/actions/runs/40214000184) **SUCCESS** at `c7b5123e4ceae3d2693df4ccbce1d6a3ef9ae654`: 52 pinned packages, `Pillow==13.0.0`, `setuptools==84.2.1`, **0 known vulnerabilities reported** by the accessed PyPI advisory service. Latest [license metadata refinement audit 40214119475](https://github.com/hibi89/AI_AutoML_Analyst/actions/runs/40214119475) at `c8d02adcd1ad7bdb70f2800bd3b7bb625626551f` also **SUCCESS** with zero reported vulnerabilities, and now correctly flags **skops** because its metadata has only generic "OSI Approved", not a specific SPDX identifier. A successful audit does NOT certify absence of all vulnerabilities or commercial license compliance.
- [P6E3 limits pre-upgrade 40213893265](https://github.com/hibi89/AI_AutoML_Analyst/actions/runs/40213893265): **105 PASS / 1 Windows-only SKIP / 41 warnings**.
- [Pillow13 Linux regression 40214031425](https://github.com/hibi89/AI_AutoML_Analyst/actions/runs/40214031425), implementation SHA `5f94e026f31d17f625857ff934cb3b81693c6173`: **105 PASS /1 Windows-only SKIP /41 warnings**, generated BASIC 6, STANDARD 9, PREMIUM 11 page synthetic PDFs/ZIPs.
- [Pillow13 Windows no-GUI 40214031452](https://github.com/hibi89/AI_AutoML_Analyst/actions/runs/40214031452) same implementation SHA: **50 PASS /9 warnings**, includes Python native and CMD model checks. This is not the owner's Windows machine. [Chromium UI 40214031501](https://github.com/hibi89/AI_AutoML_Analyst/actions/runs/40214031501) was still running at this report's evidence capture; check observed conclusion before advertising full latest-browser success.
- [Pillow13 near-cap ML stress 40213990294](https://github.com/hibi89/AI_AutoML_Analyst/actions/runs/40213990294) SUCCESS (synthetic runner only).

## Actual synthetic PDF inspection
Downloaded `basic-synthetic-pdf-review` from successful Pillow13 Linux run 40213990379 and examined 11-page PREMIUM raster contact sheet. No obvious Hangul corruption/overlap/clipping at this scale, but **p5, p6, p7, p10, p11 have notable unused white space**. No professional client or owner layout approval, no claim of pixel-perfect design.

## Operational and legal caveats
- The scanner checks a Linux Python3.11 installed package set against a time-varying vulnerability database. It does not audit OS packages, model supply-chain provenance, Windows transitive dependencies, or future vulnerabilities.
- Generic `skops` "OSI Approved" classification is not sufficient license proof. Exact license terms/redistribution, NOTICE obligations, and 52-package transitive audit remain **LEGAL REVIEW PARTIAL**.
- `scripts/windows_release_qa.ps1 -OpenBrowser` has not been run on owner's real physical PC. Use `docs/qa/P6E3_WINDOWS_RELEASE_CHECKLIST.md` for evidence requirements. Customer-like Excel variants and actual delivery are untested. Security ≠ sale readiness.
- Nonexistent public production/Vercel is `NOT APPLICABLE`, not a deployment failure. `main@c80c874476f8d5deb4bf611761d89c6d72ca0a2d` preserved.
- Sale GO/NO-GO **BASIC NO / STANDARD NO / PREMIUM NO**. Strict acceptance `P0–P6: 5/7 = 71%`. P1 owner Windows GUI and P6 final gate remain unaccepted.

## Next READY AUTO-KM-P6E4
1. Confirm latest Chromium 40214031501 and latest full audit artifacts on tested SHAs; if failed diagnose and fix, not silently mark pass.
2. Refine blank-heavy report pages with **real aggregate content** only, preserve BASIC 6–8 / STANDARD 8–12 / PREMIUM 10–15 pages, render each changed tier and inspect for clipping.
3. Finalize exact skops source LICENSE and transitive license obligations; check Windows dependency environment as feasible. Do not certify legally without evidence.
4. Prepare tier-specific GO/NO-GO and physical Windows owner approval workflow. No main merge, public deployment or selling without approval.


### Post-capture final Chromium outcome (2026-10-26 KST)
- [Pillow13 Chromium 40214031501](https://github.com/hibi89/AI_AutoML_Analyst/actions/runs/40214031501) **SUCCESS** on executable SHA `5f94e026f31d17f625857ff934cb3b81693c6173`. Real Playwright Chromium selected file, clicked report/download and verified actual ZIP output: BASIC **479,693 bytes**, STANDARD **632,150 bytes**, PREMIUM **726,447 bytes**. These are synthetic CI-only artifacts, not a customer's Windows Chrome/Edge manual approval.
- Latest verified matrix therefore Linux **105 PASS/1 SKIP**, native Windows **50 PASS**, Chromium **3 SKUs PASS**, Linux all-installed direct+transitive audit **52 packages / 0 known CVE reports**; all on relevant tested code/dependency state. Strict release progress remains **5/7 (71%)**, all tiers NO-GO until physical Windows, licensed distribution and design signoff.
