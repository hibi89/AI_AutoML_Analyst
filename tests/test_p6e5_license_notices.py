"""P6E5 synthetic-only license audit tests (no customer/source license files)."""
from __future__ import annotations

from hashlib import sha256
from pathlib import Path

from scripts.p6e5_license_notices import (
    identify_license, license_complexity_flags, notice_candidates, _UPSTREAM,
)
from scripts.p6e3_dependency_audit import DIRECT, normalize_name


def test_direct_inventory_matches_pinned_runtime_and_browser_requirements():
    repo_root = Path(__file__).resolve().parents[1]
    declared = set()
    for filename in ("requirements-verified-py311.txt", "requirements-browser.txt"):
        for raw_line in (repo_root / filename).read_text(encoding="utf-8").splitlines():
            line = raw_line.split("#", 1)[0].strip()
            if line:
                name = line.split("==", 1)[0].strip()
                declared.add(normalize_name(name))

    assert declared == DIRECT
    workflow = (repo_root / ".github/workflows/p6e3-dependency-audit.yml").read_text(
        encoding="utf-8"
    )
    assert "-r requirements-verified-py311.txt -r requirements-browser.txt" in workflow


def test_generic_classifier_not_spdx_proof():
    assert not identify_license("", "", ["OSI Approved"])
    assert not identify_license("UNKNOWN", "", ["OSI Approved"])
    assert identify_license("MIT", "", [])
    assert identify_license("", "", ["OSI Approved :: MIT License"])
    assert identify_license("", "Apache-2.0", [])


def test_identified_license_may_still_require_obligation_review():
    assert "FILE_LEVEL_COPYLEFT_NOTICE_REVIEW" in license_complexity_flags(
        "MPL-2.0", "", []
    )
    assert "DUAL_LICENSE_CHOICE_REVIEW" in license_complexity_flags(
        "", "Dual License", []
    )
    assert "COMPOSITE_SPDX_OBLIGATION_REVIEW" in license_complexity_flags(
        "MIT OR Apache-2.0", "", []
    )
    assert "CUSTOM_OR_MULTIPART_LICENSE_TEXT_REVIEW" in license_complexity_flags(
        "", "License agreement for matplotlib", []
    )
    assert license_complexity_flags("MIT", "", []) == []


def test_skops_exact_version_upstream_evidence_not_unbounded_override():
    item = _UPSTREAM[("skops", "0.16.0")]
    assert item["upstream_license"] == "MIT"
    assert len(item["upstream_source_sha"]) == 40
    assert ("skops", "0.15.0") not in _UPSTREAM


def test_notice_scans_only_local_files_and_exports_hashes(tmp_path):
    class MockDist:
        files = [Path("licenses/LICENSE.txt"), Path("module/__init__.py"),
                 Path("NOTICE.md"), Path("missing/LICENSE.txt")]

        def locate_file(self, path):
            return tmp_path / path

    (tmp_path / "licenses").mkdir()
    (tmp_path / "module").mkdir()
    (tmp_path / "licenses" / "LICENSE.txt").write_text("synthetic-license-text", encoding="utf-8")
    (tmp_path / "module" / "__init__.py").write_text("do not publish code", encoding="utf-8")
    (tmp_path / "NOTICE.md").write_text("synthetic-notice", encoding="utf-8")
    notices = notice_candidates(MockDist())
    assert len(notices) == 2
    names = {row["relative_path"] for row in notices}
    assert names == {"licenses/LICENSE.txt", "NOTICE.md"}
    assert all(row["status"] == "PRESENT_NOT_REDISTRIBUTED" for row in notices)
    assert notices[0]["sha256"] == sha256(b"synthetic-license-text").hexdigest()
    assert "synthetic-license-text" not in str(notices)
    assert str(tmp_path) not in str(notices)
