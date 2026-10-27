"""P6E28: shipped README must report the actual document fonts and flags.

Synthetic input only. Does not treat OS/2 bits as a complete legal license.
"""
from __future__ import annotations

from io import BytesIO
import json
from pathlib import Path
from zipfile import ZipFile

import pandas as pd
import pytest

from backend.app.services import font_coverage
from backend.app.services.basic_report import build_basic_zip
from backend.app.services.standard_delivery import build_standard_zip
from backend.app.services.premium_delivery import build_premium_zip


def korean_frame() -> pd.DataFrame:
    n = 80
    return pd.DataFrame({
        "매출": [float(120 + i % 13 * 7) for i in range(n)],
        "방문": [i % 9 + 1 for i in range(n)],
        "고객유형": ["A", "B"] * (n // 2),
        "목표": [i % 2 for i in range(n)],
    })


def japanese_frame() -> pd.DataFrame:
    raw = korean_frame()
    return raw.rename(columns={"매출": "売上", "방문": "訪問数", "고객유형": "地域", "목표": "購入"})


@pytest.mark.parametrize("tier", ["BASIC", "STANDARD", "PREMIUM"])
@pytest.mark.parametrize("japanese", [False, True])
def test_shipped_zip_font_readme_tracks_japanese_fallback_and_manifest(tier, japanese):
    frame = japanese_frame() if japanese else korean_frame()
    target = "購入" if japanese else "목표"
    if tier == "BASIC":
        payload = build_basic_zip(frame)
    elif tier == "STANDARD":
        payload = build_standard_zip(frame, target, "classification")
    else:
        payload = build_premium_zip(frame, target, "classification")
    with ZipFile(BytesIO(payload)) as z:
        assert z.testzip() is None
        readme = z.read("README.txt").decode("utf-8")
        assert "PDF 글꼴 정보" in readme
        assert "TTF/TTC 글꼴 파일은 이 ZIP에 포함되지 않습니다" in readme
        assert "상업적 권리 승인서를 의미하지 않습니다" in readme
        assert "기본 글꼴:" in readme
        assert "Nanum Gothic" in readme
        if japanese:
            assert "보조 글꼴:" in readme
            assert "Arphic Public License" in readme
        else:
            assert "보조 글꼴:" not in readme
            assert "Arphic Public License" not in readme
        assert "C:/Windows/Fonts/" not in readme
        assert "/usr/share/fonts/" not in readme
        assert not any(x.lower().endswith((".ttf", ".ttc", ".otf")) for x in z.namelist())
        manifest = json.loads(z.read("manifest.json"))
        entry = next(item for item in manifest["files"] if item["path"] == "README.txt")
        assert entry["sha256"] == __import__("hashlib").sha256(z.read("README.txt")).hexdigest()


def test_unknown_local_font_never_claims_nanum_or_arphic_licensing(monkeypatch):
    monkeypatch.setattr(font_coverage, "_installed_font_family", lambda path: "Private Internal Font")
    notice = font_coverage.font_usage_notice("매출")
    assert "Private Internal Font" in notice
    assert "not verified" in notice
    assert "SIL Open Font License" not in notice


@pytest.mark.parametrize("flags", [0x0002, 0x0100, 0x0200, 0x0104])
def test_disallowed_document_embedding_flags_are_rejected(monkeypatch, flags):
    from fontTools import ttLib

    class FakeTTFont:
        def __init__(self, *args, **kwargs):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

        def __contains__(self, key):
            return key == "OS/2"

        def __getitem__(self, key):
            return type("OS2", (), {"fsType": flags})()

    monkeypatch.setattr(ttLib, "TTFont", FakeTTFont)
    with pytest.raises(ValueError, match="forbids this PDF subset"):
        font_coverage.embedding_rights_flags(Path("synthetic-only-font.ttf"))


def test_preview_print_embedding_not_automatically_claimed_as_full_license(monkeypatch):
    from fontTools import ttLib

    class FakeTTFont:
        def __init__(self, *args, **kwargs):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

        def __contains__(self, key):
            return key == "OS/2"

        def __getitem__(self, key):
            return type("OS2", (), {"fsType": 0x0004})()

    monkeypatch.setattr(ttLib, "TTFont", FakeTTFont)
    assert font_coverage.embedding_rights_flags(Path("synthetic-only-font.ttf")) == 0x0004
