"""Timed synthetic STANDARD/PREMIUM model fit benchmark (CPU/RSS).

Never interpret as a promised user-PC or 20k-row runtime. Uses trained models,
real CV, holdout, PREMIUM limited tuning, and no uploaded customer data.
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


def dataset(rows: int) -> pd.DataFrame:
    rng = np.random.default_rng(20261026)
    base=rng.standard_normal(rows)
    data = {f"signal_{i:02d}": (base * (i % 3 + 1) + rng.normal(size=rows))
            for i in range(6)}
    data["category"] = np.array(["A", "B", "C"])[np.arange(rows) % 3]
    data["target"] = ((base + rng.normal(scale=.4,size=rows)) > 0).astype(int)
    return pd.DataFrame(data)


def main():
    outcomes=[]
    for rows, budget in ((120,3), (120,5), (400,3), (400,5), (2000,3), (2000,5)):
        frame=dataset(rows)
        began=time.perf_counter()
        outcome=run_standard(frame, target_column="target",
                             task_type="classification",
                             max_challengers=budget, cv=3)
        elapsed=time.perf_counter()-began
        assert len(outcome["models"]) == budget+1
        assert outcome["train_rows"] + outcome["holdout_rows"] == rows
        outcomes.append({
            "tier":"PREMIUM" if budget==5 else "STANDARD",
            "rows":rows,
            "feature_columns":len(frame.columns)-1,
            "seconds":round(elapsed,3),
            "models_including_dummy":len(outcome["models"]),
            "train_cv_folds":outcome["cv_splits"],
            "tuning_attempts":len(outcome.get("tuning_experiments", [])),
            "train_only_cv_and_untouched_holdout":not outcome["holdout_used_in_selection"],
        })
        print("P6C ML benchmark:",json.dumps(outcomes[-1]),flush=True)
    memory=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    payload={"scope":"CPU/CV/holdout evaluation of synthetic 120/400/2000-row tables only",
             "platform":platform.platform(),
             "peak_rss_kib_linux":memory if platform.system()=="Linux" else None,
             "results":outcomes, "customer_data_used":False,
             "does_not_prove_20000_row_mln":True}
    directory=Path("ci-benchmarks")
    directory.mkdir(exist_ok=True)
    (directory/"p6c_model_120_400_2000.json").write_text(
        json.dumps(payload,indent=2),encoding="utf-8")
    print("P6C synthetic model RSS KiB:",memory,flush=True)


if __name__=="__main__":
    main()
