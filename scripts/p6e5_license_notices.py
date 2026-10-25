"""P6E5 redistributable-package notice triage; no third-party files exported.

Runs in the exact pinned CI environment. Captures *names and hashes* of any
installed license/NOTICE files, not license text or packages. Missing or
ambiguous metadata is a manual-review finding, never an implicit approval.
"""
from __future__ import annotations

from hashlib import sha256
from importlib import metadata
import json
from pathlib import Path
import platform
import re

from scripts.p6e3_dependency_audit import DIRECT, normalize_name

_NOTICE = re.compile(
    r"(^|/)(license(?:[.-]|$)|licence(?:[.-]|$)|copying(?:[.-]|$)|notice(?:[.-]|$)"
    r"|third[-_]?party(?:[.-]|$))", re.I
)
_MAX_NOTICE_BYTES = 1024 * 1024

# Upstream release provenance reviewed in docs/qa/P6E4_SKOPS_LICENSE.md.
# This is an evidence annotation, NOT a waiver of redistribution notices.
_UPSTREAM = {
    ("skops", "0.16.0"): {
        "upstream_license": "MIT",
        "review_source": (
            "https://github.com/skops-dev/skops/blob/"
            "bcc69da93df528e3c72993e5d623682dbfd1d443/LICENSE"
        ),
        "upstream_source_sha": "bcc69da93df528e3c72993e5d623682dbfd1d443",
        "notice_obligation": "Preserve copyright and permission notice if redistributing software.",
    }
}


def identify_license(expression: str, legacy: str, classifiers: list[str]) -> bool:
    """Require a specific name; 'OSI Approved' and 'UNKNOWN' aren't enough."""
    expression = expression.strip()
    legacy = legacy.strip()
    generic = {"", "unknown", "none", "n/a", "osi approved",
               "other/proprietary license", "license"}
    if expression.lower() not in generic:
        return True
    if legacy.lower() not in generic:
        return True
    return any(c.strip().lower() not in generic for c in classifiers)


def notice_candidates(dist) -> list[dict]:
    """Safe in-place hashing; avoid writing local file paths or license contents."""
    candidates = []
    for entry in dist.files or []:
        name = str(entry).replace("\\", "/")
        if not _NOTICE.search(name) or len(candidates) >= 25:
            continue
        item = dist.locate_file(entry)
        try:
            if not item.is_file():
                continue
            size = item.stat().st_size
            if not 0 < size <= _MAX_NOTICE_BYTES:
                candidates.append({"relative_path": name, "bytes": size,
                                   "status": "NOT_HASHED_SIZE_LIMIT"})
                continue
            content_digest = sha256(item.read_bytes()).hexdigest()
            candidates.append({"relative_path": name, "bytes": size,
                               "sha256": content_digest,
                               "status": "PRESENT_NOT_REDISTRIBUTED"})
        except (OSError, ValueError):
            candidates.append({"relative_path": name, "status": "NOT_READABLE"})
    return candidates


def build_inventory() -> dict:
    entries = []
    seen = set()
    for dist in metadata.distributions():
        name = dist.metadata.get("Name") or ""
        key = normalize_name(name)
        if not key or key in seen:
            continue
        seen.add(key)
        version = dist.version
        msg = dist.metadata
        expression = msg.get("License-Expression") or ""
        legacy = (msg.get("License") or "")[:240]
        classifiers = [
            line.removeprefix("License :: ").strip()
            for line in msg.get_all("Classifier", []) if line.startswith("License :: ")
        ]
        notices = notice_candidates(dist)
        upstream = _UPSTREAM.get((key, version))
        named = identify_license(expression, legacy, classifiers)
        reasons = []
        if not named and upstream is None:
            reasons.append("NO_SPECIFIC_LICENSE_IDENTIFIED")
        if not notices:
            reasons.append("NO_LOCAL_LICENSE_OR_NOTICE_FILE_IDENTIFIED")
        if any(row["status"] != "PRESENT_NOT_REDISTRIBUTED" for row in notices):
            reasons.append("NOTICE_FILE_NOT_HASHED")
        entries.append({
            "name": name, "version": version, "direct": key in DIRECT,
            "license_expression": expression, "legacy_license": legacy,
            "license_classifiers": classifiers, "notice_file_evidence": notices,
            "upstream_review": upstream, "manual_review_reasons": reasons,
            "requires_manual_redistribution_review": bool(reasons),
        })
    entries.sort(key=lambda row: row["name"].lower())
    return {
        "tool": "P6E5 license-notice evidence v1",
        "python": platform.python_version(),
        "installed_package_count": len(entries),
        "direct_packages_expected": len(DIRECT),
        "missing_direct_packages": sorted(DIRECT - {normalize_name(e["name"]) for e in entries}),
        "requires_manual_review_count": sum(bool(e["manual_review_reasons"]) for e in entries),
        "package_count_with_local_notice": sum(bool(e["notice_file_evidence"]) for e in entries),
        "items": entries,
        "scope": "CI Linux Python environment, including developer/test and transitive packages",
        "notices_copied": False,
        "legal_clearance": "NOT CERTIFIED",
        "note": "Installing by pip is not the same as bundling or redistributing wheels; review the actual delivery method.",
    }


def main() -> int:
    output = Path("ci-benchmarks/p6e5_notice_evidence.json")
    output.parent.mkdir(parents=True, exist_ok=True)
    result = build_inventory()
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print("Installed distributions:", result["installed_package_count"])
    print("Direct packages missing:", result["missing_direct_packages"])
    print("Local notice file evidence:", result["package_count_with_local_notice"])
    print("Manual license/notice triage:", result["requires_manual_review_count"])
    for row in result["items"]:
        if row["manual_review_reasons"]:
            print("REVIEW:", row["name"], row["version"], ",".join(row["manual_review_reasons"]))
    return 1 if result["missing_direct_packages"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
