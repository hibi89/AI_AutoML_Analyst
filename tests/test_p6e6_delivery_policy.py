"""P6E6 no vendored dependencies/fonts and immutable delivery policy."""
from __future__ import annotations

from hashlib import sha256
from io import BytesIO
import json
from zipfile import ZIP_DEFLATED, ZipFile

import pytest

from scripts.p6e6_delivery_policy import verify_shipping_zip


def _make(tier: str, added: dict[str, bytes] | None = None, *, tamper: bool = False) -> bytes:
    files: dict[str, bytes] = {
        "report.pdf": b"%PDF-TEST-ONLY",
        "summary.csv": b"column,count\nage,9\n",
        "summary.json": b"{}",
        "README.txt": b"synthetic NAVER SIL Open Font License 1.1",
        "charts/01_distribution.png": b"\x89PNG",
    }
    if tier == "STANDARD":
        files.update({"standard_summary.json": b"{}", "model_scores.csv": b"model\nx\n",
                      "holdout_scores.csv": b"metric,selected,dummy\nf1_weighted,0.4,0.5\n"})
    if tier == "PREMIUM":
        files.update({
            "premium_summary.json": b"{}",
            "model_scores.csv": b"model\nx\n",
            "holdout_scores.csv": b"metric,selected,dummy\nf1_weighted,0.4,0.5\n",
            "model_pipeline.skops": b"SYNTHETIC-NOT-LOADABLE",
            "model_schema.json": b"{}",
            "predict.py": b"pass",
            "predict.cmd": b"@echo off",
            "requirements-premium.txt": b"skops==0.16.0",
            "sample_input.csv": b"a,b\n",
            "sample_predictions.csv": b"prediction\n",
        })
    files.update(added or {})
    manifest = {
        "format": tier.lower(),
        "files": [
            {"path": name, "sha256": sha256(value).hexdigest(), "size": len(value)}
            for name, value in files.items()
        ],
    }
    if tamper:
        manifest["files"][0]["sha256"] = "0" * 64
    files["manifest.json"] = json.dumps(manifest).encode()
    out = BytesIO()
    with ZipFile(out, "w", ZIP_DEFLATED) as archive:
        for name, value in files.items():
            archive.writestr(name, value)
    return out.getvalue()


@pytest.mark.parametrize("tier", ("BASIC", "STANDARD", "PREMIUM"))
def test_clean_customer_artifact_contains_no_third_party_package_or_raw_font(tier):
    result = verify_shipping_zip(_make(tier), tier)
    assert result["vendored_python_wheels"] == 0
    assert result["standalone_font_files"] == 0
    assert result["native_executables"] == 0
    assert result["fitted_model"] == (tier == "PREMIUM")
    assert result["legal_clearance"] == "NOT_CERTIFIED"
    assert result["pdf_embedded_font_license"] == "SEPARATE_REVIEW"


@pytest.mark.parametrize("name", [
    "dependencies/numpy-2.4.6-py3-none-any.whl",
    "fonts/NanumGothic.ttf",
    "vendor/matplotlib/__init__.py",
    "../secret.csv",
    "app.exe",
    "charts/07_unknown.png",
    "charts/../../copy.txt",
])
def test_fail_closed_on_unaudited_or_executable_members(name):
    with pytest.raises(ValueError, match="Unexpected or bundled"):
        verify_shipping_zip(_make("BASIC", {name: b"FAKE"}), "BASIC")


def test_premium_model_is_not_allowed_in_basic_or_standard():
    with pytest.raises(ValueError, match="Unexpected or bundled"):
        verify_shipping_zip(_make("BASIC", {"model_pipeline.skops": b"LEAK"}), "BASIC")


def test_missing_font_notice_blocks_shipping():
    with pytest.raises(ValueError, match="font attribution"):
        verify_shipping_zip(_make("BASIC", {"README.txt": b"notice-missing"}), "BASIC")


def test_manifest_sha_tampering_is_rejected():
    with pytest.raises(ValueError, match="integrity"):
        verify_shipping_zip(_make("PREMIUM", tamper=True), "PREMIUM")


def test_shipment_requires_exact_expected_members():
    # Missing a required customer deliverable fails even if the manifest
    # correctly covers everything remaining.
    import zipfile
    original = _make("STANDARD")
    with ZipFile(BytesIO(original)) as z:
        files = {name: z.read(name) for name in z.namelist() if name != "model_scores.csv"}
    payload = BytesIO()
    with ZipFile(payload, "w", zipfile.ZIP_DEFLATED) as z:
        for name, blob in files.items():
            z.writestr(name, blob)
    with pytest.raises(ValueError, match="Missing STANDARD"):
        verify_shipping_zip(payload.getvalue(), "STANDARD")


def test_optional_importance_csv_is_allowed_in_paid_tiers_but_not_basic():
    rows = b"feature,importance,method\namount,0.2,tree_impurity\n"
    for tier in ("STANDARD", "PREMIUM"):
        result = verify_shipping_zip(_make(tier, {"feature_importance.csv": rows}), tier)
        assert result["tier"] == tier
    with pytest.raises(ValueError, match="Unexpected or bundled"):
        verify_shipping_zip(_make("BASIC", {"feature_importance.csv": rows}), "BASIC")


@pytest.mark.parametrize("tier", ("STANDARD", "PREMIUM"))
def test_holdout_scores_missing_fails_closed_even_when_manifest_matches(tier):
    # Must not silently omit independent validation when delivering paid ML.
    original = _make(tier)
    with ZipFile(BytesIO(original)) as archive:
        members = {
            name: archive.read(name)
            for name in archive.namelist()
            if name not in {"holdout_scores.csv", "manifest.json"}
        }
    manifest = {
        "format": tier.lower(),
        "files": [{"path": name, "sha256": sha256(data).hexdigest(), "size": len(data)}
                  for name, data in members.items()],
    }
    members["manifest.json"] = json.dumps(manifest).encode()
    out = BytesIO()
    with ZipFile(out, "w", ZIP_DEFLATED) as archive:
        for name, data in members.items():
            archive.writestr(name, data)
    with pytest.raises(ValueError, match=f"Missing {tier}"):
        verify_shipping_zip(out.getvalue(), tier)
