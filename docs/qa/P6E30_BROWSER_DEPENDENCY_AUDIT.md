# P6E30 — Browser dependency security and license audit coverage

**VERIFIED 2026-10-27 KST.** Branch `feature/kmong-v1`; tested code/workflow SHA `f28f11ca38780ce425160633ea7fd949ef331bad`.

## Finding

`requirements-browser.txt` pins Playwright separately from `requirements-verified-py311.txt`. The P6E3 workflow installed only the latter before freezing the installed environment, producing vulnerability and license evidence that omitted the browser automation dependency. The browser smoke workflows did install Playwright, but they did not run `pip-audit` or the full dependency/license inventory.

## Change

- P6E3 now triggers and invalidates its pip cache when `requirements-browser.txt` changes, then installs both pinned requirement files before freezing and scanning the environment.
- `scripts/p6e3_dependency_audit.py` includes Playwright in its direct dependency inventory so P6E3 and P6E5 evidence label it correctly.
- `tests/test_p6e5_license_notices.py` checks that the combined pinned manifests match the direct inventory and that the audit workflow installs both manifests.

The audit still records findings; it does not grant a license or certify legal/commercial redistribution rights. No font or customer files are copied.

## Verification

- Local focused regression: `tests/test_p6e5_license_notices.py` — **5 passed**.
- `git diff --check` — **PASS**.
- Hosted [P6E3 dependency/security CI 40498983817](https://github.com/hibi89/AI_AutoML_Analyst/actions/runs/40498983817): **SUCCESS**. The run installed both manifests, captured **55 distributions** including Playwright, reported no missing direct dependencies, and completed `pip-audit` with **no known vulnerabilities found; exit code 0** at scan time.
- The license inventory identified **11 manual license/notice triage items** and `skops` without usable specific license metadata. These are pending source-license review findings, not proof of an infringement; the CI does not certify redistribution rights.

## Release state

BASIC, STANDARD, and PREMIUM remain **NO-GO** for sale. Each SKU still needs owner review of its generated PDF/ZIP visual quality, applicable font and source-license obligations (including the 11 dependency triage items above), and explicit commercial approval. Existing successful application tests and browser downloads remain preserved; this audit change does not replace or repeat them. `pip-audit` only reflects the advisory database at this run and is not continuous monitoring.
