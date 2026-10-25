"""P6E synthetic PDF overflow and header-privacy regression (no customer files)."""
from __future__ import annotations

from io import BytesIO

from pypdf import PdfReader

from backend.app.services.premium_delivery import _premium_page


def test_premium_handover_is_two_pages_with_long_korean_headers():
    long_column = "매우긴한글열이름" * 19  # under the 160-character input guard
    columns = [long_column] + [f"설명변수_{index:02d}" for index in range(49)]
    analysis = {
        "target_column": "분류대상", "task_type": "classification",
        "cv_splits": 3, "primary_metric": "f1_weighted",
        "train_rows": 2160, "holdout_rows": 540,
        "selected_holdout_metrics": {"f1_weighted": 0.61},
        "dummy_holdout_metrics": {"f1_weighted": 0.50},
        # Raw category values must not accidentally reach handover PDF.
        "training_private_category_value": "SECRET_CUSTOMER_CATEGORY_VALUE",
    }
    schema = {
        "raw_feature_columns": columns,
        "numeric_raw_columns": columns[1:40],
        "datetime_features": columns[40:42],
        "boolean_raw_columns": columns[42:44],
        "prepared_feature_columns": columns[1:],
    }
    pdf = _premium_page(analysis, "ridge_classifier", schema)
    pages = PdfReader(BytesIO(pdf)).pages
    assert len(pages) == 2, "Handover overflowed into a third PDF page"
    one = pages[0].extract_text()
    two = pages[1].extract_text()
    assert "모델 검증 스냅샷" in one
    assert "0.6100" in one and "0.5000" in one
    assert "입력 계약 요약" in two
    assert "50개" in two
    assert "model_schema.json" in two
    assert "SECRET_CUSTOMER_CATEGORY_VALUE" not in one + two
