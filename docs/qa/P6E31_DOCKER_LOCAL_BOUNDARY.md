# P6E31 — Docker localhost boundary and pinned application image

**State:** implementation and local Compose configuration check complete; hosted container build/runtime CI pending. Branch `feature/kmong-v1`, 2026-10-27 KST.

## Reproduced issues

- `docker compose config` resolved the existing short mapping `8000:8000` without a host IP, meaning Docker could publish on all host interfaces.
- `docker-compose.yml` contained a developer-specific absolute `C:/Users/.../OneDrive/...` data mount for legacy folder scanning. Those filesystem routes are now disabled, so the documented `/data` workflow was both stale and unnecessarily exposed a personal host path.
- The documented Docker image installed only five floating package ranges and omitted current PDF, chart, XLSX and model-artifact dependencies. It was not built from the repository's tested pinned dependency manifest.

## Changes

- Compose publishes `127.0.0.1:8000:8000`, removes the fixed container name and user-specific `/data` mount, and keeps `experiments` plus an ignored, read-only `local-fonts` mount. The user supplies licensed `NanumGothic.ttf` and optional `Japanese.ttf`; no font is committed or copied into the image/ZIP.
- Dockerfile installs `requirements-verified-py311.txt` instead of an incomplete unpinned package list.
- README now documents the actual tier pages, pinned local setup, disabled legacy file browsing and localhost-only Compose use.
- A regression checks the local-only mapping, absence of personal path mounts, and use of the verified dependency manifest. A dedicated GitHub Actions smoke builds the image, checks the resolved host IP, and requests health plus all three tier pages.

The container's internal Uvicorn listener remains `0.0.0.0` so Docker networking can reach it; the supported Compose host port is loopback-only. Do not publish the image openly or bypass Compose with a wildcard host-port mapping.

## Verification

- Local `docker compose config --format json`: **PASS**, resolved host IP `127.0.0.1`; `./experiments` is the only writable bind mount and `./local-fonts` is read-only.
- Focused new regression: **PASS** (1 passed, 5 deselected; 1 Starlette deprecation warning).
- Docker daemon is unavailable in the local environment, so local image build/runtime: **NOT RUN**.
- Hosted Docker build/runtime workflow: **PENDING** until commit and observed run.

## Release state

This is a localhost and dependency correctness fix, not Docker release approval. BASIC/STANDARD/PREMIUM remain **NO-GO** pending owner review of each PDF's visual quality, applicable font/source licenses, and explicit commercial approval. No customer data, model, ZIP, font binary, or local absolute path was committed.
