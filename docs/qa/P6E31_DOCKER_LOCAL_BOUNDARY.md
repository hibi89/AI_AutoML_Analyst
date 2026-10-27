# P6E31 — Docker localhost boundary and pinned application image

**State:** VERIFIED on branch `feature/kmong-v1`, 2026-10-27 KST. Tested source SHA: `0afef7c15022486f33ad665716e08651eae420c8`.

## Reproduced issues

- `docker compose config` resolved the existing short mapping `8000:8000` without a host IP, meaning Docker could publish on all host interfaces.
- `docker-compose.yml` contained a developer-specific absolute `C:/Users/.../OneDrive/...` data mount for legacy folder scanning. Those filesystem routes are now disabled, so the documented `/data` workflow was both stale and unnecessarily exposed a personal host path.
- The documented Docker image installed only five floating package ranges and omitted current PDF, chart, XLSX and model-artifact dependencies. It was not built from the repository's tested pinned dependency manifest.

## Changes

- Compose publishes `127.0.0.1:8000:8000`, removes the fixed container name and user-specific `/data` mount, and keeps `experiments` plus an ignored, read-only `local-fonts` mount. The user supplies licensed `NanumGothic.ttf` and optional `Japanese.ttf`; no font is committed or copied into the image/ZIP.
- Dockerfile installs `requirements-verified-py311.txt` instead of an incomplete unpinned package list.
- First Docker CI [40501048122](https://github.com/hibi89/AI_AutoML_Analyst/actions/runs/40501048122) built the image and validated loopback Compose config, then health/UI returned 403. The forwarded client peer is the Docker bridge gateway, not loopback. Added an explicit Compose-only mode that trusts only the exact Linux default-route gateway from `/proc/net/route`; the host port remains bound to `127.0.0.1`, and Host/Origin checks plus disabled filesystem routes remain in force.
- The constrained correction passed [Docker build/health/tier-page CI 40501689796](https://github.com/hibi89/AI_AutoML_Analyst/actions/runs/40501689796). The job built the image, verified host binding/mounts, and fetched `/health` and all three tier pages through the published loopback port.
- README now documents the actual tier pages, pinned local setup, disabled legacy file browsing and localhost-only Compose use.
- Regressions check the local-only mapping, no personal path mount, pinned dependency manifest, and that only the explicit Compose gateway is trusted (loopback works by default; other peers remain rejected). A dedicated GitHub Actions smoke builds the image, checks the resolved host IP, and requests health plus all three tier pages.

The container's internal Uvicorn listener remains `0.0.0.0` so Docker networking can reach it; the supported Compose host port is loopback-only. Do not publish the image openly or bypass Compose with a wildcard host-port mapping.

## Verification

- Local `docker compose config --format json`: **PASS**, resolved host IP `127.0.0.1`; `./experiments` is the only writable bind mount and `./local-fonts` is read-only.
- Focused gateway/Compose regression: **2 passed / 5 deselected / 1 Starlette deprecation warning**.
- Docker daemon is unavailable in the local environment, so local image build/runtime: **NOT RUN**.
- [Linux full suite 40501689831](https://github.com/hibi89/AI_AutoML_Analyst/actions/runs/40501689831): **203 passed / 3 skipped / 66 warnings**.
- [Windows native compatibility 40501689848](https://github.com/hibi89/AI_AutoML_Analyst/actions/runs/40501689848): **96 passed / 9 warnings**.
- [Windows Chromium 40501689755](https://github.com/hibi89/AI_AutoML_Analyst/actions/runs/40501689755) and [Linux Chromium 40501689853](https://github.com/hibi89/AI_AutoML_Analyst/actions/runs/40501689853): **6/6 real upload/download ZIP checks per OS**, including auto and CP932 CSV encodings.
- `git diff --check`: **PASS** before the tested source commit.

## Release state

This is a localhost and dependency correctness fix, not Docker release approval. BASIC/STANDARD/PREMIUM remain **NO-GO** pending owner review of each PDF's visual quality, applicable font/source licenses, and explicit commercial approval. No customer data, model, ZIP, font binary, or local absolute path was committed.

No independent code, feature, security, reliability, or compatibility finding remains. The shared license review includes the 11 P6E30 dependency notice/license triage items and missing `skops` license metadata. These and the per-SKU visual and commercial approvals are owner review gates, not CI conclusions.
