# P6E6 — package-by-package license obligation and distribution-mode review
Review date: 2026-10-26 KST. Scope: the exact **52 installed Linux Python 3.11 packages** in [Actions 40216690129](https://github.com/hibi89/AI_AutoML_Analyst/actions/runs/40216690129), NOT every version/platform possible. Source artifact: `p6e5_notice_evidence.json`; no vendor source code or license bytes copied here.

## Delivery model — explicitly constrained
- **CURRENT BASIC / STANDARD**: end customer gets PDF, summary CSV/JSON, charts, README, manifest and for STANDARD model scores. **No Python wheel or trained model** shipped.
- **CURRENT PREMIUM**: end customer gets the same plus the owner's `predict.py`/`predict.cmd`, schema, trusted `model_pipeline.skops` and **requirements-premium.txt**; **no installed NumPy/Pandas/sklearn/skops distributions or wheel binaries** shipped. Customer follows instructions to install dependencies independently from their package index. This boundary is enforced by `scripts/p6e6_delivery_policy.py` with fail-closed ZIP member and manifest checks, integrated into `scripts/p6e5_windows_demo.py`.
- In all SKUs, **PDF-embedded NanumGothic** may constitute embedded font data. No standalone .ttf/.otf is bundled. The PDF/font license question is **distinct from** the Python-wheel redistribution question.
- **NOT APPROVED**: bundling Python executables/wheels, vendoring site-packages, desktop installers, frozen PyInstaller EXEs, external SaaS or supplying fonts as loose files without assessing actual third-party license terms. If delivery architecture changes, repeat audit and approvals.

## Exact ten flagged packages (not ten license violations)
| CI-installed package | Direct/transitive | Evidence read | Additional obligation if redistributed | Current assessment |
|---|---|---|---|---|
| certifi **2026.10.23** | Transitive | metadata MPL-2.0; LICENSE present/hash | MPL 2.0 notices and applicable covered-source obligations for distribution; analyze modified vs unmodified | **NOT bundled; customer pip install**, potential bundling obligations still OPEN |
| contourpy **1.3.3** | Transitive | BSD 3-Clause metadata; LICENSE hash | Copyright, license text and disclaimer for binary redistribution, check included third-party notices | **NOT bundled**, downstream notice bundle future OPEN |
| cycler **0.12.1** | Transitive | BSD-like text and BSD classifier, LICENSE hash | Preserve copyright and terms on redistribution | **NOT bundled**, future bundling OPEN |
| kiwisolver **1.5.1** | Transitive | modified BSD license text, LICENSE hash | Preserve BSD copyright and notices | **NOT bundled**, future bundling OPEN |
| matplotlib **3.11.2** | Direct app runtime (not in delivered PDF/PNG as a package) | PSF-style Matplotlib license agreement, LICENSE hash (long text) | Respect exact project license agreement, included third-party attribution and notices on distribution | **NOT bundled**, separate exact notice obligations OPEN |
| numpy **2.4.6** | Direct; Premium user-install dependency | `BSD-3-Clause AND 0BSD AND MIT AND Zlib AND CC0-1.0`; LICENSE and subcomponent license hashes | If bundling **wheel** its bundled/native component notices may differ by operating system and wheel; preserve all applicable notices | **NOT bundled**, future Windows-wheel license review OPEN |
| packaging **26.3** | Transitive | `Apache-2.0 OR BSD-2-Clause`; both license files present | Choose applicable license option if distributing, preserve its notices | **NOT bundled**, future bundling OPEN |
| pandas **2.3.3** | Direct; Premium user-install dependency | BSD 3-Clause metadata and long license file/hash | Preserve copyright/license notices; check included native extras if wheel redistributed | **NOT bundled**, future bundling OPEN |
| python-dateutil **3.0.0** | Transitive | Dual BSD-3-Clause / Apache 2.0; LICENSE hash | Old pre-2017 contributions may only be BSD-3-Clause licensed; follow exact distribution license notice instead of assuming everything dual licensed | **NOT bundled**, future bundling OPEN |
| scipy **1.17.1** | Transitive | BSD with extended third-party component license file hashes | Preserve all applicable license/copyright and vendored native math library notices if wheel redistributed | **NOT bundled**, future bundling OPEN |

**Precisely what is verified:** for all 10, the pinned Linux *installed distribution* reports a named license and locally available LICENSE/NOTICE files; the JSON audit records their relative names and SHA-256 (no third-party license source bytes). This supports identification and risk triage; it does **not** establish automatic legal clearance for hypothetical vendored wheels or every Windows binary component.

### Reference documents and license terms
- Naver official NanumGothic SIL OFL 1.1 & reserved font naming, commercial use: https://help.naver.com/service/30016/contents/18088
- Original skops 0.16.0 MIT source: https://github.com/skops-dev/skops/blob/bcc69da93df528e3c72993e5d623682dbfd1d443/LICENSE
- certifi pinned release: https://pypi.org/project/certifi/2026.10.23/
- contourpy: https://pypi.org/project/contourpy/1.3.3/
- cycler: https://pypi.org/project/cycler/0.12.1/
- kiwisolver: https://pypi.org/project/kiwisolver/1.5.1/
- Matplotlib: https://pypi.org/project/matplotlib/3.11.2/
- NumPy: https://pypi.org/project/numpy/2.4.6/
- packaging: https://pypi.org/project/packaging/26.3/
- pandas: https://pypi.org/project/pandas/2.3.3/
- python-dateutil version 3.0.0: https://pypi.org/project/python-dateutil/3.0.0/
- SciPy: https://pypi.org/project/scipy/1.17.1/

## PDF font special case
NAVER's official Nanum license states personal/corporate commercial use and bundled redistribution are allowed under the **SIL OFL 1.1** and stated license requirements. This app consumes an owner-installed NanumGothic.ttf and ReportLab may embed a font subset in PDFs. We have **not** shipped raw font software. Preserve the font attribution/official license link with any commercial report; do not modify reserved font names or repackage a modified font without separate review. **Verify exact installed font provenance and actual embedded PDF terms on the owner's machine before legal release signoff.**

## Release gate and proof limitations
- For the presently restricted PDF/ZIP + script + customer's independent pip installation **no third-party Python packages are intentionally redistributed**. This materially narrows packaging notice scope, but does **not** negate obligations for copyrighted documentation, embedded fonts, customer data or third-party package installation.
- If a future product bundles EXE, wheels, venv, Docker, redistributable fonts or JS dependencies: **FAIL CLOSED / new complete license audit required** (actual artifact, OS-dependent binaries, per-component copyright and LICENSE/NOTICE copies, review by owner/legal).
- `scripts/p6e6_delivery_policy.py` is structural verification **only**, not a legal certification or a parser for hostile ZIP uploads.
- Security 40216690129 showed **0 known advisories then**, not ongoing monitoring.
- Pending physical Windows/Edge/Chrome ZIP/PDF/font/real `predict.cmd` and owner aesthetic approval are **NOT RUN**. No paid listing, main merge or external deployment approved. Strict progress **5/7 (71%)**, BASIC/STANDARD/PREMIUM all **NO-GO**.
