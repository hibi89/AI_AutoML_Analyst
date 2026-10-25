"""P6E6 exact shipping-artifact composition and redistribution boundary.

Audit the *generated customer ZIP*, not only dependency metadata. Dependencies
are installed via pip on the operator/customer system; the ZIP must not vendor
third-party package binaries or fonts. PDF-embedded glyph/font subsets are a
separate font-license review, not equivalent to shipping raw TTF files.
"""
from __future__ import annotations

from hashlib import sha256
from io import BytesIO
import json
import re
from zipfile import ZipFile

_COMMON = frozenset({"report.pdf", "summary.csv", "summary.json", "README.txt", "manifest.json"})
_STANDARD = frozenset({"standard_summary.json", "model_scores.csv"})
_PREMIUM = frozenset({
    "premium_summary.json", "model_scores.csv", "model_pipeline.skops",
    "model_schema.json", "predict.py", "predict.cmd", "requirements-premium.txt",
    "sample_input.csv", "sample_predictions.csv",
})
_CHART = re.compile(r"charts/[0-9]{2}_(?:distribution|missing|correlation|categories|box|trend|ml_comparison)\.png\Z")
_FORBIDDEN = (".whl", ".ttf", ".otf", ".dll", ".pyd", ".so", ".dylib", ".exe", ".pickle", ".pkl")


def verify_shipping_zip(payload: bytes, tier: str) -> dict:
    """Fail closed on a new member until its legal/privacy purpose is reviewed.

    Intended for *our own* generated deliverables only. Do not feed untrusted
    ZIPs into this validator instead of a safe archive parser/sandbox.
    """
    if tier not in {"BASIC", "STANDARD", "PREMIUM"}:
        raise ValueError("Unknown tier")
    allowed = _COMMON | (_STANDARD if tier == "STANDARD" else
                        _PREMIUM if tier == "PREMIUM" else frozenset())
    with ZipFile(BytesIO(payload)) as archive:
        members = archive.namelist()
        if len(members) != len(set(members)):
            raise ValueError("Duplicate shipping members")
        for name in members:
            if (name.startswith(("/", "\\")) or "\\" in name or
                    ".." in name.split("/") or
                    any(name.casefold().endswith(suffix) for suffix in _FORBIDDEN) or
                    (name not in allowed and not _CHART.fullmatch(name))):
                raise ValueError("Unexpected or bundled dependency member in shipping ZIP")
        if not _COMMON.issubset(members):
            raise ValueError("Missing common delivery member")
        if tier == "STANDARD" and not _STANDARD.issubset(members):
            raise ValueError("Missing STANDARD delivery member")
        if tier == "PREMIUM" and not _PREMIUM.issubset(members):
            raise ValueError("Missing PREMIUM delivery member")
        if tier != "PREMIUM" and "model_pipeline.skops" in members:
            raise ValueError("Unexpected fitted model in lower tier")
        manifest = json.loads(archive.read("manifest.json"))
        records = manifest.get("files", [])
        recorded = [item.get("path") for item in records]
        if (len(recorded) != len(set(recorded)) or
                set(recorded) != set(members) - {"manifest.json"}):
            raise ValueError("Shipment manifest does not match archive members")
        for entry in records:
            actual = archive.read(entry["path"])
            if sha256(actual).hexdigest() != entry["sha256"]:
                raise ValueError("Shipment integrity failed")
            reported_length = entry.get("size", entry.get("bytes"))
            if reported_length != len(actual):
                raise ValueError("Shipment size mismatch")
        return {
            "tier": tier,
            "members": len(members),
            "vendored_python_wheels": 0,
            "standalone_font_files": 0,
            "native_executables": 0,
            "fitted_model": tier == "PREMIUM",
            "dependency_install_method": "pip from upstream, not bundled wheels",
            "pdf_embedded_font_license": "SEPARATE_REVIEW",
            "legal_clearance": "NOT_CERTIFIED",
        }
