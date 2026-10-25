# skops 0.16.0 — source license verification
Verified against official upstream repository on 2026-10-26 KST.

## Exact release provenance
- Locked Python requirement: `skops==0.16.0`.
- PyPI 0.16.0 source/wheel publishing attestation identifies upstream `skops-dev/skops` commit `bcc69da93df528e3c72993e5d623682dbfd1d443` for both artifacts (published 2026-09-24).
- Source tree at that **exact commit** includes top-level `LICENSE`.
- The official `LICENSE` at that commit states **MIT License (MIT)**; copyright **(C) 2021 Hugging Face Inc.** It permits use/copy/modification/distribution/sublicensing/sale, subject to keeping the copyright and permission notice in copies or substantial portions.
- Authoritative source: https://github.com/skops-dev/skops/blob/bcc69da93df528e3c72993e5d623682dbfd1d443/LICENSE
- Release: https://pypi.org/project/skops/0.16.0/
- Previously installed distribution metadata only said `License :: OSI Approved`, which alone is inadequate. Official source license resolves **skops identification** but does not prove bundled dependency legal compliance.

## Product implication
- The local PREMIUM delivered ZIP includes a trained `model_pipeline.skops` serialized artifact and the project's own `predict.py`, not a vendored copy of the skops package itself.
- Client installation via `requirements-premium.txt` retrieves `skops` from their package repository. If the software or substantial portions of it are redistributed, ensure MIT notices accompany it. Do not bundle font binaries or unpublished customer models in open repositories.
- The serialized model contains trained category metadata, potentially confidential to the customer. The zip must be delivered privately to an authorized recipient and loaded only if provenance is independently trusted; integrity SHA does not authenticate the sender.
- **Legal gate still PARTIAL:** transitive dependency licenses/NOTICE/OS package terms and actual distribution packaging require separate case-specific review. This is a factual engineering record, not legal advice or a release certificate.
