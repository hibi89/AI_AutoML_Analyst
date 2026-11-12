"""P6E51 separate 3-SKU owner evidence: no data, model or license bytes exported."""
from __future__ import annotations

from hashlib import sha256
from html.parser import HTMLParser
import json
import os
from pathlib import Path
from unittest.mock import patch

import pytest

from scripts.p6e51_owner_three_tier_review import (
    HUMAN_GATES, TIERS, create_three_tier_review, main,
)
from test_p6e50_owner_zip_review import _archive


def _sources(tmp_path: Path) -> dict:
    result = {}
    for tier in TIERS:
        payload = _archive(tier)
        file = tmp_path / (tier + "_CUSTOMER_PRIVATE_SYNTHETIC.zip")
        file.write_bytes(payload)
        result[tier] = (file, sha256(payload).hexdigest())
    return result


def _run(tmp_path, sources=None):
    result = sources or _sources(tmp_path)
    output_json = tmp_path / "review.json"
    output_html = tmp_path / "review.html"
    report = create_three_tier_review(result, output_json, output_html)
    return report, result, output_json, output_html


def test_real_three_tier_hashes_pages_and_never_sale_approved(tmp_path):
    report, sources, j, h = _run(tmp_path)
    assert report["status"] == "THREE_TIER_STRUCTURE_VERIFIED_SEPARATE_HUMAN_REVIEW_REQUIRED"
    assert [x["tier"] for x in report["tiers"]] == list(TIERS)
    assert [x["pdf_pages"] for x in report["tiers"]] == [6, 9, 11]
    assert [x["zip_sha256"] for x in report["tiers"]] == [
        sources[tier][1] for tier in TIERS]
    assert len(report["human_gates"]) == len(HUMAN_GATES)
    assert all(v == "NOT_VERIFIED" for v in report["human_gates"].values())
    assert all(r["customer_sale_approved"] is False for r in report["tiers"])
    assert report["every_sku_sale_approved"] is False
    assert json.loads(j.read_text(encoding="utf-8")) == report
    assert "RELEASE HOLD" in h.read_text(encoding="utf-8")


def test_no_original_bytes_or_private_paths_written_or_printed(tmp_path):
    sources = _sources(tmp_path)
    old = {p: p.read_bytes() for p, digest in sources.values()}
    report, _, j, h = _run(tmp_path, sources)
    for p, raw in old.items():
        assert p.read_bytes() == raw
    joined = j.read_text(encoding="utf-8") + h.read_text(encoding="utf-8")
    assert str(tmp_path) not in joined
    assert "CUSTOMER_PRIVATE_SYNTHETIC" not in joined
    assert "model_pipeline.skops" not in joined
    assert "SYNTHETIC-NOT-LOADABLE" not in joined
    assert "source_data" not in joined


def test_review_html_has_strict_no_js_or_network_policy(tmp_path):
    _, _, _, path = _run(tmp_path)
    html = path.read_text(encoding="utf-8")
    assert "script-src 'none'" in html
    assert "connect-src 'none'" in html
    assert "img-src 'none'" in html
    assert "<script" not in html.lower()
    assert "http://" not in html
    assert "https://" not in html
    assert "<form" not in html.lower()
    class Counter(HTMLParser):
        def __init__(self): super().__init__(); self.rows = 0
        def handle_starttag(self, tag, attrs):
            if tag == "tr": self.rows += 1
    counter = Counter(); counter.feed(html)
    assert counter.rows == 4  # Header + three SKUs


def test_repeat_output_is_refused_without_overwrite(tmp_path):
    _, s, j, h = _run(tmp_path)
    original_j, original_h = j.read_bytes(), h.read_bytes()
    with pytest.raises(ValueError):
        create_three_tier_review(s, j, h)
    assert j.read_bytes() == original_j
    assert h.read_bytes() == original_h


@pytest.mark.parametrize("target", ["out_json", "out_html"])
def test_preexisting_customer_report_is_not_overwritten(tmp_path, target):
    s = _sources(tmp_path)
    j, h = tmp_path / "owner.json", tmp_path / "owner.html"
    existing = j if target == "out_json" else h
    existing.write_bytes(b"OWNER EXISTING")
    with pytest.raises(ValueError):
        create_three_tier_review(s, j, h)
    assert existing.read_bytes() == b"OWNER EXISTING"
    assert not (h if target == "out_json" else j).exists()


def test_mixed_wrong_sku_package_blocked_before_outputs(tmp_path):
    sources = _sources(tmp_path)
    sources["STANDARD"] = sources["BASIC"]
    with pytest.raises(ValueError):
        create_three_tier_review(sources, tmp_path / "report.json", tmp_path / "report.html")
    assert not (tmp_path / "report.json").exists()


def test_bad_external_sha_stops_before_outputs(tmp_path):
    sources = _sources(tmp_path)
    file, _ = sources["PREMIUM"]
    sources["PREMIUM"] = (file, "0" * 64)
    with pytest.raises(ValueError):
        create_three_tier_review(sources, tmp_path / "report.json", tmp_path / "report.html")
    assert not (tmp_path / "report.json").exists()
    assert not (tmp_path / "report.html").exists()


def test_corrupted_zip_pays_no_cost_to_existing_outputs(tmp_path):
    sources = _sources(tmp_path)
    path, sha = sources["PREMIUM"]
    path.write_bytes(b"INVALID ZIP")
    sources["PREMIUM"] = (path, sha256(path.read_bytes()).hexdigest())
    with pytest.raises(Exception):
        create_three_tier_review(sources, tmp_path / "report.json", tmp_path / "report.html")
    assert not (tmp_path / "report.json").exists()


def test_wrong_object_schema_or_shared_source_refused(tmp_path):
    sources = _sources(tmp_path)
    with pytest.raises(ValueError):
        create_three_tier_review({"BASIC": sources["BASIC"]},
                                 tmp_path / "report.json", tmp_path / "report.html")
    sources["STANDARD"] = sources["BASIC"]
    with pytest.raises(ValueError):
        create_three_tier_review(sources, tmp_path / "report.json", tmp_path / "report.html")


def test_output_parent_symlink_is_blocked(tmp_path):
    if os.name == "nt":
        pytest.skip("Windows junction requires owner native test")
    sources = _sources(tmp_path)
    alias = tmp_path / "link"
    try:
        alias.symlink_to(tmp_path, target_is_directory=True)
    except OSError:
        pytest.skip("symlinks unavailable")
    with pytest.raises(ValueError):
        create_three_tier_review(sources, alias / "report.json", tmp_path / "report.html")


def test_failed_second_output_write_preserves_partial_first_output(tmp_path):
    from scripts import p6e51_owner_three_tier_review as mod
    sources = _sources(tmp_path)
    j, h = tmp_path / "report.json", tmp_path / "report.html"
    real_open = os.open
    def fail_second(path, flags, mode=0o777):
        if Path(path) == h and flags & os.O_CREAT:
            raise OSError("synthetic permission denied")
        return real_open(path, flags, mode)
    with patch.object(mod.os, "open", side_effect=fail_second):
        with pytest.raises(OSError):
            mod.create_three_tier_review(sources, j, h)
    assert json.loads(j.read_text(encoding="utf-8"))["every_sku_sale_approved"] is False
    assert not h.exists()
    assert all(p.exists() for p, digest in sources.values())


def test_cli_prints_sha_only_and_does_not_grant_approval(tmp_path, capsys):
    sources = _sources(tmp_path)
    argv = []
    for tier in TIERS:
        path, digest = sources[tier]
        argv += ["--" + tier.lower(), str(path),
                 "--" + tier.lower() + "-sha256", digest]
    out_j, out_h = tmp_path / "result.json", tmp_path / "result.html"
    argv += ["--out-json", str(out_j), "--out-html", str(out_h)]
    assert main(argv) == 0
    captured = capsys.readouterr().out
    assert "EVERY_SKU_SALE_APPROVED=False" in captured
    assert str(tmp_path) not in captured
    assert "CUSTOMER_PRIVATE_SYNTHETIC" not in captured
    assert json.loads(out_j.read_text(encoding="utf-8"))["every_sku_sale_approved"] is False
    assert main(argv) == 1


def test_changed_zip_after_inspection_is_rejected_without_outputs(tmp_path):
    from scripts import p6e51_owner_three_tier_review as mod
    sources = _sources(tmp_path)
    original = mod._read_bounded_original
    def swapped(path):
        raw = original(path)
        if path == sources["PREMIUM"][0]:
            return b"x" + raw[1:]
        return raw
    with patch.object(mod, "_read_bounded_original", side_effect=swapped):
        with pytest.raises(ValueError):
            create_three_tier_review(sources, tmp_path / "report.json",
                                     tmp_path / "report.html")
    assert not (tmp_path / "report.json").exists()


def test_failed_html_cannot_delete_a_concurrent_owner_replacement(tmp_path):
    from scripts import p6e51_owner_three_tier_review as mod
    sources = _sources(tmp_path)
    j, h = tmp_path / "review.json", tmp_path / "review.html"
    moved = tmp_path / "created-by-reviewer.json"
    owner_bytes = b"OWNER REPLACED PATH; NOT REVIEW OUTPUT"
    real_open = os.open

    def swap_after_first_output(path, flags, mode=0o777):
        if Path(path) == h and flags & os.O_CREAT:
            os.replace(j, moved)
            j.write_bytes(owner_bytes)
            raise OSError("synthetic later output failure")
        return real_open(path, flags, mode)

    with patch.object(mod.os, "open", side_effect=swap_after_first_output):
        with pytest.raises(OSError):
            mod.create_three_tier_review(sources, j, h)
    assert moved.is_file()
    assert j.read_bytes() == owner_bytes
    assert not h.exists()
    assert all(p.exists() for p, digest in sources.values())
