"""P6E52: actual existing BASIC/STANDARD/PREMIUM generators, synthetic data only.

CI Linux integration evidence, NOT buyer Windows/print-quality/legal acceptance.
Never save model ZIP contents or customer files as CI artifacts.
"""
from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path

import pytest

from backend.app.services.basic_report import build_basic_zip
from backend.app.services.standard_delivery import build_standard_zip
from backend.app.services.premium_delivery import build_premium_zip
from scripts.p6e5_windows_demo import synthetic_frame
from scripts.p6e51_owner_three_tier_review import create_three_tier_review, TIERS


def test_real_existing_three_tier_packages_are_reviewable_without_release(tmp_path: Path):
    basic = synthetic_frame()
    ml = basic.copy()
    ml["구매"] = [i % 2 for i in range(len(ml))]
    packs = {
        "BASIC": build_basic_zip(basic),
        "STANDARD": build_standard_zip(
            ml, target_column="구매", task_type="classification", cv=3),
        "PREMIUM": build_premium_zip(
            ml, target_column="구매", task_type="classification", cv=3),
    }
    sources = {}
    for tier, payload in packs.items():
        path = tmp_path / (tier.lower() + "_local_synthetic.zip")
        path.write_bytes(payload)
        sources[tier] = (path, sha256(payload).hexdigest())
    out_json = tmp_path / "review.json"
    out_html = tmp_path / "review.html"
    report = create_three_tier_review(sources, out_json, out_html)
    assert [r["tier"] for r in report["tiers"]] == list(TIERS)
    for entry in report["tiers"]:
        lo, hi = {"BASIC": (6, 8), "STANDARD": (8, 12),
                  "PREMIUM": (10, 15)}[entry["tier"]]
        assert lo <= entry["pdf_pages"] <= hi
        assert entry["shipment_integrity"] == "VERIFIED"
        assert entry["customer_sale_approved"] is False
        assert entry["license_and_data_rights"] == "NOT_VERIFIED"
    assert report["every_sku_sale_approved"] is False
    assert json.loads(out_json.read_text(encoding="utf-8")) == report
    html = out_html.read_text(encoding="utf-8")
    assert "RELEASE HOLD" in html
    assert "script-src 'none'" in html
    assert "connect-src 'none'" in html
    assert str(tmp_path) not in out_json.read_text(encoding="utf-8") + html
    assert all(path.read_bytes() == packs[tier] for tier, (path, _) in sources.items())
