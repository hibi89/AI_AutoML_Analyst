"""P6E50 bounded owner ZIP/PDF review: synthetic in-memory samples only."""
from __future__ import annotations

from hashlib import sha256
from io import BytesIO
import json
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

import pytest
from reportlab.pdfgen.canvas import Canvas

from scripts.p6e50_owner_zip_review import inspect_owner_zip, main


def _pdf(pages: int, *, size=(595, 842)) -> bytes:
    out = BytesIO()
    doc = Canvas(out, pagesize=size, pageCompression=1)
    for i in range(pages):
        doc.drawString(40, 40, "SYNTHETIC QA PAGE " + str(i + 1))
        doc.showPage()
    doc.save()
    return out.getvalue()


def _archive(tier: str = "BASIC", *, pages: int | None = None,
             extra: dict[str, bytes] | None = None,
             omit: set[str] | None = None,
             wrong_manifest: bool = False, duplicate: str | None = None,
             page_size=(595, 842)) -> bytes:
    files: dict[str, bytes] = {
        "report.pdf": _pdf(pages or {"BASIC": 6, "STANDARD": 9, "PREMIUM": 11}[tier],
                           size=page_size),
        "summary.csv": b"metric,count\nrows,100\n",
        "summary.json": b'{"synthetic":true}',
        "README.txt": b"SYNTHETIC, NOT A LICENSE: NAVER SIL Open Font License 1.1",
        "charts/01_distribution.png": b"\x89PNG\r\n\x1a\nsynthetic",
    }
    if tier == "STANDARD":
        files.update({
            "standard_summary.json": b"{}",
            "model_scores.csv": b"model,metric\nbaseline,0\n",
            "holdout_scores.csv": b"metric,score\nf1_weighted,0\n",
        })
    if tier == "PREMIUM":
        files.update({
            "premium_summary.json": b"{}",
            "model_scores.csv": b"model,metric\nbaseline,0\n",
            "holdout_scores.csv": b"metric,score\nf1_weighted,0\n",
            "model_pipeline.skops": b"SYNTHETIC MODEL NEVER LOAD",
            "model_schema.json": b"{}",
            "predict.py": b"NEVER RUN SYNTHETIC",
            "predict.cmd": b"NEVER RUN SYNTHETIC",
            "requirements-premium.txt": b"skops==0.16.0",
            "sample_input.csv": b"code\nSYN\n",
            "sample_predictions.csv": b"prediction\n0\n",
        })
    files.update(extra or {})
    for key in omit or set():
        files.pop(key, None)
    records = [
        {"path": key, "sha256": sha256(value).hexdigest(), "size": len(value)}
        for key, value in files.items()
    ]
    if wrong_manifest:
        records[0]["sha256"] = "0" * 64
    files["manifest.json"] = json.dumps({"files": records}).encode()
    out = BytesIO()
    with ZipFile(out, "w", ZIP_DEFLATED) as z:
        for name, data in files.items():
            z.writestr(name, data)
        if duplicate is not None:
            z.writestr(duplicate, files[duplicate])
    return out.getvalue()


def _inspect(tmp_path: Path, payload: bytes, *, tier="BASIC") -> dict:
    file = tmp_path / "owner-synthetic.zip"
    file.write_bytes(payload)
    return inspect_owner_zip(file, tier, sha256(payload).hexdigest())


@pytest.mark.parametrize("tier,pages", [("BASIC", 6), ("STANDARD", 9), ("PREMIUM", 11)])
def test_three_tiers_report_structural_integrity_but_never_grant_sale(tmp_path, tier, pages):
    data = _archive(tier)
    result = _inspect(tmp_path, data, tier=tier)
    assert result["tier"] == tier
    assert result["pdf_pages"] == pages
    assert result["zip_sha256"] == sha256(data).hexdigest()
    assert result["manifest_member_checksums"] == "VERIFIED"
    assert result["status"].endswith("HUMAN_REVIEW_REQUIRED")
    assert result["customer_sale_approved"] is False
    assert all(result[gate] == "NOT_VERIFIED" for gate in (
        "pdf_visual_readability", "pdf_embedded_font_original_rights",
        "third_party_license_notice_rights", "owner_data_authorization",
        "physical_windows_customer_qa", "human_sku_acceptance"))
    assert "synthetic" not in json.dumps(result).lower()
    assert data == (tmp_path / "owner-synthetic.zip").read_bytes()


def test_reject_mismatched_external_zip_sha_without_side_effect(tmp_path):
    raw = _archive()
    path = tmp_path / "a.zip"
    path.write_bytes(raw)
    with pytest.raises(ValueError):
        inspect_owner_zip(path, "BASIC", "0" * 64)
    assert path.read_bytes() == raw


def test_reject_wrong_tier_even_if_archive_is_structurally_sound(tmp_path):
    with pytest.raises(ValueError):
        _inspect(tmp_path, _archive("BASIC"), tier="STANDARD")


@pytest.mark.parametrize("pages", [1, 5, 9])
def test_basic_pdf_requires_sku_page_range(tmp_path, pages):
    with pytest.raises(ValueError):
        _inspect(tmp_path, _archive("BASIC", pages=pages))


def test_unbounded_pdf_page_media_box_fails(tmp_path):
    with pytest.raises(ValueError):
        _inspect(tmp_path, _archive(page_size=(30, 30)))


def test_manifest_checksum_tamper_is_rejected(tmp_path):
    with pytest.raises(ValueError):
        _inspect(tmp_path, _archive(wrong_manifest=True))


def test_pdf_header_corruption_rejected_even_if_manifest_hash_matches(tmp_path):
    with pytest.raises(ValueError):
        _inspect(tmp_path, _archive(extra={"report.pdf": b"NOT A PDF"}))


@pytest.mark.parametrize("member", ["vendors/unsafe.dll", "../escape.txt", "charts/99_unknown.png"])
def test_unexpected_or_executable_member_rejected(tmp_path, member):
    with pytest.raises(ValueError):
        _inspect(tmp_path, _archive(extra={member: b"synthetic"}))


def test_duplicate_exact_member_is_rejected(tmp_path):
    with pytest.raises(ValueError):
        _inspect(tmp_path, _archive(duplicate="summary.csv"))


def test_duplicate_casefold_member_is_rejected(tmp_path):
    with pytest.raises(ValueError):
        _inspect(tmp_path, _archive(extra={"SUMMARY.csv": b"other"}))


def test_high_compression_ratio_is_rejected_before_unpack(tmp_path):
    with pytest.raises(ValueError):
        _inspect(tmp_path, _archive(extra={"summary.csv": b"A" * 1024 * 1024}))


def test_missing_required_tier_evidence_rejected(tmp_path):
    with pytest.raises(ValueError):
        _inspect(tmp_path, _archive("PREMIUM", omit={"holdout_scores.csv"}), tier="PREMIUM")


def test_symlinked_source_rejected(tmp_path):
    source = tmp_path / "original.zip"
    raw = _archive()
    source.write_bytes(raw)
    link = tmp_path / "linked.zip"
    try:
        link.symlink_to(source)
    except OSError:
        pytest.skip("file symlink unavailable")
    with pytest.raises(ValueError):
        inspect_owner_zip(link, "BASIC", sha256(raw).hexdigest())


def test_cli_writes_new_metadata_only_and_refuses_overwrite(tmp_path, capsys):
    payload = _archive()
    source = tmp_path / "buyer-owned-synthetic.zip"
    source.write_bytes(payload)
    out = tmp_path / "review.json"
    argv = ["--zip", str(source), "--tier", "BASIC",
            "--expected-sha256", sha256(payload).hexdigest(), "--out", str(out)]
    assert main(argv) == 0
    result = json.loads(out.read_text(encoding="utf-8"))
    assert result["customer_sale_approved"] is False
    assert str(tmp_path) not in out.read_text(encoding="utf-8")
    stdout = capsys.readouterr().out
    assert "CUSTOMER_SALE_APPROVED=False" in stdout
    assert str(tmp_path) not in stdout
    before = out.read_bytes()
    assert main(argv) == 1
    assert out.read_bytes() == before
    assert source.read_bytes() == payload


def test_cli_bad_archive_leaves_existing_sources_and_no_new_review(tmp_path):
    source = tmp_path / "bad.zip"
    source.write_bytes(b"SYNTHETIC INVALID ZIP")
    out = tmp_path / "no-review.json"
    argv = ["--zip", str(source), "--tier", "BASIC",
            "--expected-sha256", sha256(source.read_bytes()).hexdigest(),
            "--out", str(out)]
    assert main(argv) == 1
    assert not out.exists()
    assert source.read_bytes() == b"SYNTHETIC INVALID ZIP"


def test_review_path_must_be_absolute_and_json(tmp_path):
    data = _archive()
    p = tmp_path / "a.zip"
    p.write_bytes(data)
    with pytest.raises(ValueError):
        inspect_owner_zip(Path("relative.zip"), "BASIC", sha256(data).hexdigest())
    out = tmp_path / "changed.txt"
    assert main(["--zip", str(p), "--tier", "BASIC",
                 "--expected-sha256", sha256(data).hexdigest(),
                 "--out", str(out)]) == 1
    assert not out.exists()
