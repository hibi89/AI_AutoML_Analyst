# P6E53 — Owner review output deletion race / P95 target (2026-11-12 KST)

## Decision

AI AutoML Analyst current **85% provisional engineering**; user-set target **95%**, not yet achieved. Formal P0–P6 acceptance remains **5/7=71%**; BASIC/STANDARD/PREMIUM are RELEASE HOLD / SALE NO-GO. Central kmong `[작업중]` must **not be cleared** until verified P95, including pause, room transition, or blocked owner-only gates.

P6E50 and P6E51 previously deleted newly created output paths with `Path.unlink(missing_ok=True)` on an error. A different local process can replace that pathname between `O_EXCL` create and cleanup, so deleting by name can remove a different owner's file.

- Option A: `lstat`/inode verification immediately before unlink. Rejected: check-to-unlink TOCTOU persists, especially across Windows reparse/path changes.
- Option B (selected): never automatically unlink a failed output pathname. Preserve the private partial JSON/HTML for explicit owner HOLD/manual cleanup. Retain existing `O_EXCL`, `0o600`, source digest and path bounds, and error exit status. No network, data transfer, model execution, or sales approval.

## Regression acceptance

1. P6E50 interrupted JSON write returns failure, does not delete partial output or alter the original ZIP.
2. P6E51 second HTML write failure retains the first JSON (still `every_sku_sale_approved=False`) without HTML.
3. P6E51 concurrent writer replaces the first JSON pathname before second output fails; the replacement survives and all source ZIPs remain unchanged.
4. Existing real archive/PDF/manifest, three-tier checks and Ubuntu/Windows CI on the exact source SHA must pass.
5. Actual buyer Windows10/11, all PDF pages and font rendering, font/software license originals, rights/NOTICE, real customer permission and individual SKU release signoff are **NOT VERIFIED**, not inferred by synthetic CI.

The product's original main and three SKU engines are preserved; no Vercel deployment, fee or customer files. Next: record exact CI SHA/status and reconcile the P95 target without inflating the completion rate from test counts.
