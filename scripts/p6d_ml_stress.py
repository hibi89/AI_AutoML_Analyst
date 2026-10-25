"""P6D dedicated near-cap synthetic model training benchmark.

Time and memory measurements are CI runner observations, not customer SLAs.
No sensitive or downloaded data, only fixed-seed generated 50-column tables.
"""
from __future__ import annotations

import json
import platform
import resource
import time
from pathlib import Path

import numpy as np
import pandas as pd

from backend.app.services.standard_engine import run_standard


def make_data(n_rows: int) -> pd.DataFrame:
    gen = np.random.default_rng(20261026)
    latent = gen.normal(size=n_rows)
    d = {}
    for i in range(44):
        d[f"측정_{i:02d}"] = latent * (.3 + (i % 5) / 5) + gen.normal(size=n_rows)
    for i in range(5):
        d[f"구분_{i:02d}"] = [
            f"category_{i}_{k % 5}" for k in range(n_rows)
        ]
    y = (latent + gen.normal(scale=.7, size=n_rows) > 0).astype(int)
    d["target"] = y
    assert len(d) == 50
    return pd.DataFrame(d)


def main():
    cases = []
    for n_rows, challengers in ((5000, 3), (3000, 5)):
        frame = make_data(n_rows)
        start = time.perf_counter()
        evaluation = run_standard(
            frame, "target", "classification", cv=3,
            max_challengers=challengers,
        )
        seconds = round(time.perf_counter() - start, 2)
        budget = evaluation["resource_budget"]
        assert budget["estimated_encoded_features"] <= budget["encoded_feature_limit"]
        assert evaluation["train_rows"] + evaluation["holdout_rows"] == n_rows
        assert evaluation["holdout_used_in_selection"] is False
        case = {
            "tier": evaluation["tier"],
            "rows": n_rows,
            "total_columns": len(frame.columns),
            "estimated_ohe_columns": budget["estimated_encoded_features"],
            "model_candidates_including_dummy": len(evaluation["models"]),
            "tuning_experiments": len(evaluation["tuning_experiments"]),
            "full_cv_holdout_seconds": seconds,
            "peak_process_rss_kib_linux": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
            if platform.system() == "Linux" else None,
            "all_data_synthetic": True,
        }
        cases.append(case)
        print("P6D ML STRESS", json.dumps(case, ensure_ascii=False), flush=True)
    folder = Path("ci-benchmarks")
    folder.mkdir(exist_ok=True)
    (folder / "p6d_near_capacity.json").write_text(
        json.dumps({"cases": cases, "platform": platform.platform(),
                    "scope": "Only same runner, synthetic binary classification",
                    "not_customer_sla": True}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
