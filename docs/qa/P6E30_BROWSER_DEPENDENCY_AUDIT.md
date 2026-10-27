# P6E30 — Browser dependency security and license audit coverage

**State at implementation:** code and focused regression test complete; hosted dependency-audit CI pending. Branch `feature/kmong-v1`, 2026-10-27 KST.

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
- Hosted P6E3 dependency/security workflow: **PENDING** until the source change is pushed and its run is observed.

## Release state

BASIC, STANDARD, and PREMIUM remain **NO-GO** for sale. Their remaining owner approvals are the generated PDF/ZIP visual review, actual font/source license review, and explicit commercial approval for each SKU. Existing successful application tests and browser downloads remain preserved; this audit change does not replace or repeat them.
