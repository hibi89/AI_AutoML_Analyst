# P6E3 — owner's physical Windows release checklist

**Status: NOT RUN. This is a future acceptance checklist, not evidence of approval.**

## Preconditions
- Use **Windows 10/11** with **Python 3.11**; preferably a dedicated venv for this project to avoid altering other Python projects.
- Obtain the reviewed `feature/kmong-v1` revision from GitHub and compare its commit SHA to the accepted CI SHA in `STATUS.md`.
- Install a legitimately obtained `NanumGothic.ttf` into Windows Fonts (do not bundle raw font files into ZIP or repository).
- Work with **synthetic/de-identified** examples only. No secrets, client records or raw CSVs in public GitHub.
- Before installing Python packages, check the version pins in `requirements-verified-py311.txt`, and the latest `docs/qa/P6E3_RELEASE.md` vulnerability status. **Stop if known CVE release gate remains open.**

## Execute locally in PowerShell at repository root
```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\windows_release_qa.ps1 -OpenBrowser
```
The existing helper runs local tests, opens the three localhost UI pages and prints a server PID. It does **not** automate human browser clicks and ZIP review. Do not expose port 8000 publicly.

## Manual acceptance, record PASS/FAIL and evidence
| Gate | Required owner observation | Outcome |
|---|---|---|
| First install | Python 3.11 + pinned dependencies, font discovery, no unexpected installers | NOT RUN |
| BASIC browser | Open `/basic-mvp`, upload synthetic CSV and XLSX, download/unzip BASIC ZIP; `report.pdf` is readable and charts legible | NOT RUN |
| STANDARD browser | Open `/standard-mvp`; select correct target/split, download/unzip ZIP and verify `model_scores.csv`, holdout disclaimers | NOT RUN |
| PREMIUM browser | Open `/premium-mvp`; obtain fresh ZIP (not older CMD-bug version), verify schema/model/manifest, use authorized test input | NOT RUN |
| Repeat prediction | In extracted PREMIUM folder run `predict.cmd new_data.csv predicted.csv` with actual synthetic matching-schema rows, check output count and header | NOT RUN |
| Rejection behavior | Try wrong column order, reused output path and modified `model_pipeline.skops` **on a disposable extracted copy**, verify safe error/no overwrite | NOT RUN |
| PDF visual | View/print Korean labels and visual content of every BASIC/STANDARD/PREMIUM PDF page; no clipping/overlap; owner design signoff | NOT RUN |
| Security boundary | External Host/Origin and remote access remain blocked; no customer files in generated public artifacts | NOT RUN |

## Record back
Record Windows version, Python version, repo SHA, selected browser/version, ZIP file hashes, and gate outcomes. **Never paste actual customer input rows, private category labels, tokens or model bundles into public issues.**

If a step fails: save *redacted* error message, identify exact failed step, preserve originals, and stop sale approval. It is acceptable to mark untested items **NOT RUN**; do not infer PASS from Linux CI.

No public Vercel/Production URL is part of the local-first product. Final tier-specific GO/NO-GO requires observed evidence; 10/28 is only a target.
