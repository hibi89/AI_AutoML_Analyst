"""License metadata inventory for the exact tested Python dependency environment.

This report is a triage aid, NOT a legal certification. It includes transitive
distributions and reports missing metadata instead of auto-approving it.
No user files, license binaries, credentials or licensed font files are copied.
"""
from __future__ import annotations

from importlib import metadata
import json
from pathlib import Path
import platform
import re
import sys


DIRECT = {
    "fastapi", "uvicorn", "pandas", "numpy", "scikit-learn",
    "python-multipart", "httpx", "pytest", "matplotlib",
    "reportlab", "pypdf", "pillow", "skops", "openpyxl", "playwright",
}


def normalize_name(name: str) -> str:
    return re.sub(r"[-_.]+", "-", name).lower()


def inventory() -> dict:
    rows = []
    seen = set()
    for dist in metadata.distributions():
        name = dist.metadata.get("Name") or ""
        normalized = normalize_name(name)
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        msg = dist.metadata
        expression = msg.get("License-Expression") or ""
        legacy = (msg.get("License") or "").strip()
        classifiers = [x.removeprefix("License :: ").strip()
                       for x in msg.get_all("Classifier", [])
                       if x.startswith("License :: ")]
        # License-File metadata may list files; we record only filenames,
        # never the referenced font or license binaries themselves.
        license_files = msg.get_all("License-File", [])
        # Generic classifiers such as "OSI Approved" do not identify which
        # license terms govern redistribution; treat them as manual review.
        specific_classifiers = [label for label in classifiers
                                if label not in {"OSI Approved", "Other/Proprietary License"}]
        identifiable = bool(expression or legacy or specific_classifiers)
        rows.append({
            "name": name,
            "version": dist.version,
            "direct": normalized in DIRECT,
            "license_expression": expression,
            "legacy_license": legacy[:240],
            "license_classifiers": classifiers,
            "license_file_names": license_files[:12],
            "requires_human_review": not identifiable,
        })
    rows.sort(key=lambda item: item["name"].lower())
    missing_direct = sorted(DIRECT - {normalize_name(r["name"]) for r in rows})
    return {
        "python": platform.python_version(),
        "platform": platform.platform(),
        "installed": len(rows),
        "expected_direct": len(DIRECT),
        "missing_direct": missing_direct,
        "unidentified_licenses": [row["name"] for row in rows
                                  if row["requires_human_review"]],
        "components": rows,
        "scope": "All installed distributions, including transitive dependencies",
        "legal_clearance": "NOT CERTIFIED; manual review needed for redistribution",
        "security_clearance": "NOT PROVIDED; see separate pip-audit JSON",
    }


def main() -> int:
    result = inventory()
    output = Path("ci-benchmarks/p6e3_full_dependency_inventory.json")
    output.parent.mkdir(exist_ok=True, parents=True)
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2),
                      encoding="utf-8")
    print("Installed packages:", result["installed"])
    print("Missing direct distributions:", result["missing_direct"])
    print("No usable license metadata:", result["unidentified_licenses"])
    if result["missing_direct"]:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
