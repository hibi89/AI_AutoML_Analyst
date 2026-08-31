import pandas as pd


def detect_task(
    df: pd.DataFrame,
    target_column: str,
) -> dict:
    if target_column not in df.columns:
        raise ValueError(
            f"Target column not found: {target_column}"
        )

    target = df[target_column]

    unique_count = target.nunique(dropna=True)

    if unique_count < 2:
        raise ValueError(
            "Target must contain at least two unique values."
        )

    if pd.api.types.is_numeric_dtype(target):
        if unique_count == 2:
            task_type = "classification"
            subtype = "binary_classification"

        elif unique_count <= 20:
            task_type = "classification"
            subtype = "multiclass_classification"

        else:
            task_type = "regression"
            subtype = "regression"

    else:
        task_type = "classification"

        if unique_count == 2:
            subtype = "binary_classification"
        else:
            subtype = "multiclass_classification"

    class_distribution = {}

    if task_type == "classification":
        distribution = target.value_counts(
            normalize=True,
            dropna=False,
        )

        class_distribution = {
            str(label): round(float(rate), 4)
            for label, rate in distribution.items()
        }

    return {
        "target": target_column,
        "unique_count": int(unique_count),
        "task_type": task_type,
        "subtype": subtype,
        "class_distribution": class_distribution,
    }