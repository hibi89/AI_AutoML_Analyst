"""Record exact tested dependencies and declared licenses for release review.

This is an inventory, not a legal or vulnerability-certification system.
No license binaries or fonts are copied to artifacts.
"""
from __future__ import annotations

from importlib import metadata
import json
from pathlib import Path
import platform
import subprocess
import sys


DIRECT = [
    "fastapi", "uvicorn", "pandas", "numpy", "scikit-learn",
    "python-multipart", "httpx", "pytest", "matplotlib",
    "reportlab", "pypdf", "Pillow", "skops", "openpyxl",
]


def main():
    entries = []
    for name in DIRECT:
        dist = metadata.distribution(name)
        meta = dist.metadata
        licenses = [
            line.removeprefix("License :: ").strip()
            for line in meta.get_all("Classifier", [])
            if line.startswith("License :: ")
        ]
        declared = meta.get("License-Expression") or meta.get("License") or ""
        if len(declared) > 200:
            declared = declared[:200] + "..."
        entries.append({
            "name": dist.metadata.get("Name", name),
            "version": dist.version,
            "license_expression_or_text": declared,
            "license_classifiers": licenses,
            "requires_manual_license_review": not (declared or licenses),
        })
    folder = Path("ci-benchmarks")
    folder.mkdir(exist_ok=True)
    full = {
        "python": platform.python_version(),
        "platform": platform.platform(),
        "distributions": entries,
        "scope": "Direct CI dependencies only; transitive licensing must be separately reviewed",
        "not_security_certification": True,
    }
    (folder / "p6c_dependency_inventory.json").write_text(
        json.dumps(full, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    freeze = subprocess.run(
        [sys.executable, "-m", "pip", "freeze"],
        capture_output=True, text=True, check=True, timeout=90,
    )
    (folder / "p6c_resolved_requirements.txt").write_text(
        freeze.stdout, encoding="utf-8",
    )
    check = subprocess.run(
        [sys.executable, "-m", "pip", "check"],
        capture_output=True, text=True, check=True, timeout=90,
    )
    print("Dependency consistency:", check.stdout.strip())
    print("Direct packages inventoried:", len(entries))
    print("Needs license metadata manual review:",
          [row["name"] for row in entries if row["requires_manual_license_review"]])


if __name__ == "__main__":
    main()
