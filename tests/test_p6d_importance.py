"""P6D importance is based on fitted training model, not leaked categories."""
from io import BytesIO
from zipfile import ZipFile
import json

import pandas as pd
from pypdf import PdfReader

from backend.app.services.standard_engine import run_standard
from backend.app.services.standard_delivery import build_standard_zip


def test_training_feature_ranking_redacts_private_category_labels():
    n = 120
    frame = pd.DataFrame({
        "visits": [float((i % 11) * 2 + 1) for i in range(n)],
        "segments": [
            "SECRET_CUSTOMER_CATEGORY_ALPHA" if i % 2
            else "SECRET_CUSTOMER_CATEGORY_BETA"
            for i in range(n)
        ],
        "target": [i % 2 for i in range(n)],
    })
    outcome = run_standard(frame, target_column="target",
                           task_type="classification", cv=3)
    ranking = outcome["training_feature_importance"]
    assert len(ranking) >= 1
    assert all(x["method"] in ("tree_impurity", "absolute_coefficient")
               for x in ranking)
    serialized = json.dumps(ranking, ensure_ascii=False)
    assert "SECRET_CUSTOMER_CATEGORY_" not in serialized
    assert all(isinstance(item["importance"], float) for item in ranking)

    content = build_standard_zip(frame, "target", task_type="classification")
    with ZipFile(BytesIO(content)) as archive:
        pdf = PdfReader(BytesIO(archive.read("report.pdf")))
        document = "\n".join((page.extract_text() or "") for page in pdf.pages)
        assert "모델별 변수 기여도" in document
        assert "SECRET_CUSTOMER_CATEGORY_" not in document
