"""P6E2 adversarial input, export hygiene, and error-redaction regression.

All fixtures are synthetic. Schema/field names are customer-provided metadata;
the guarantee here is that individual categorical *values* and raw rows do
not appear in BASIC/STANDARD client-facing summaries or PDF text.
PREMIUM's trusted fitted model necessarily retains encoded categories.
"""
from __future__ import annotations

import csv
import json
from io import BytesIO, StringIO
from zipfile import ZIP_DEFLATED, ZipFile

import pandas as pd
import pytest
from fastapi.testclient import TestClient
from pypdf import PdfReader

from backend.app.main import app
from backend.app.services.basic_report import build_basic_zip
from backend.app.services.standard_delivery import build_standard_zip
from backend.app.services.tabular_input import read_xlsx_bounded


def _make_synthetic() -> pd.DataFrame:
    n = 120
    frame = pd.DataFrame({
        "income": [50.0 + i % 17 for i in range(n)],
        "visits": [i % 11 + 1 for i in range(n)],
        "market": ["SECRET_SYNTHETIC_CATEGORY_A" if i % 3 else
                   "SECRET_SYNTHETIC_CATEGORY_B" for i in range(n)],
        "target": [i % 2 for i in range(n)],
    })
    frame.loc[4, "income"] = float("nan")
    return frame


@pytest.mark.parametrize("tier", ["basic", "standard"])
def test_no_raw_category_values_in_public_report_members(tier):
    data = _make_synthetic()
    bundle = (build_basic_zip(data) if tier == "basic" else
              build_standard_zip(data, "target", "classification"))
    with ZipFile(BytesIO(bundle)) as archive:
        members = archive.namelist()
        assert "manifest.json" in members
        manifest = json.loads(archive.read("manifest.json"))
        assert manifest["no_raw_dataset"] is True
        import hashlib
        for entry in manifest["files"]:
            assert entry["path"] in members
            assert hashlib.sha256(archive.read(entry["path"])).hexdigest() == entry["sha256"]
        assert not any(name.endswith((".xlsx", ".skops")) for name in members)
        report_text = " ".join(page.extract_text() or ""
                               for page in PdfReader(BytesIO(archive.read("report.pdf"))).pages)
        for marker in ("SECRET_SYNTHETIC_CATEGORY_A", "SECRET_SYNTHETIC_CATEGORY_B"):
            assert marker not in report_text
            for name in members:
                if name.endswith((".csv", ".json", ".txt")):
                    assert marker.encode() not in archive.read(name)
        # Raw customer records are never copied as files; metadata/field names
        # and aggregate counts are deliberately included for client utility.
        assert not any("raw_dataset" in name for name in members)


def test_formula_shaped_header_is_inert_in_exported_csv():
    frame = pd.DataFrame({
        '=HYPERLINK("https://example.invalid","click")': [i for i in range(16)],
        "safe": [i % 3 for i in range(16)],
    })
    with ZipFile(BytesIO(build_basic_zip(frame))) as archive:
        reader = csv.reader(StringIO(archive.read("summary.csv").decode("utf-8-sig")))
        rows = list(reader)
        assert rows[1][0].startswith("'=HYPERLINK")
        # JSON is metadata, not an executable spreadsheet.
        assert "quality" in json.loads(archive.read("summary.json"))


@pytest.mark.parametrize("payload", [
    b"x,y\nA\x00B,1\n",
    b"left,right\n\"unclosed,1\n",
])
def test_malformed_csv_returns_client_error_without_raw_echo(payload):
    response = TestClient(app).post(
        "/api/basic-report",
        files={"file": ("malformed.csv", BytesIO(payload), "text/csv")},
    )
    assert response.status_code == 400, response.text
    assert "A\\u0000B" not in response.text
    assert "unclosed,1" not in response.text


def _archive(names: list[tuple[str, bytes]]) -> bytes:
    buffer = BytesIO()
    with ZipFile(buffer, "w", ZIP_DEFLATED) as z:
        for path, payload in names:
            z.writestr(path, payload)
    return buffer.getvalue()


@pytest.mark.parametrize("entries, message", [
    ([
        ("[Content_Types].xml", b"ok"),
        ("xl/workbook.xml", b"ok"),
        ("xl/vbaproject.bin", b"fake macro"),
    ], "Macro"),
    ([
        ("[Content_Types].xml", b"ok"),
        ("xl/workbook.xml", b"ok"),
        ("xl/externalLinks/externalLink1.xml", b"external URI"),
    ], "External-link"),
    ([
        ("[Content_Types].xml", b"ok"),
        ("xl/workbook.xml", b"ok"),
        ("xl/workbook.xml", b"duplicate"),
    ], "Duplicate"),
])
def test_hostile_xlsx_archive_parts_rejected_before_parse(entries, message):
    with pytest.raises(ValueError, match=message):
        read_xlsx_bounded(_archive(entries))


def test_internal_sklearn_errors_never_reach_standard_delivery(monkeypatch):
    from backend.app.services import standard_engine
    actual = standard_engine.cross_validate
    failed = [False]

    def synthetic_failure(pipeline, *args, **kwargs):
        if not failed[0] and not pipeline.named_steps["model"].__class__.__name__.startswith("Dummy"):
            failed[0] = True
            raise ValueError("PRIVATE_SYNTHETIC_ROW_VALUE must not leave server")
        return actual(pipeline, *args, **kwargs)

    monkeypatch.setattr(standard_engine, "cross_validate", synthetic_failure)
    analysis = standard_engine.run_standard(_make_synthetic(), "target", "classification")
    assert failed[0]
    excluded = [r for r in analysis["models"] if r["status"] == "failed"]
    assert len(excluded) == 1
    assert excluded[0]["error"].startswith("ValueError:")
    assert "PRIVATE_SYNTHETIC_ROW_VALUE" not in json.dumps(analysis)
