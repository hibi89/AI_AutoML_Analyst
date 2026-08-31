import pandas as pd
from pprint import pprint

from backend.app.services.profiler import profile_csv
from backend.app.services.task_detector import detect_task


def main() -> None:
    file_path = "data/sample_customer.csv"

    result = profile_csv(file_path)

    df = pd.read_csv(file_path)

    target = result["target_candidates"][0]["column"]

    task = detect_task(
        df,
        target,
    )

    print("\n=== DATASET OVERVIEW ===")

    dataset = result["dataset"]

    print(f"Rows: {dataset['rows']:,}")
    print(f"Columns: {dataset['columns']}")
    print(f"Numeric: {dataset['numeric_columns']}")
    print(f"Categorical: {dataset['categorical_columns']}")
    print(f"Datetime: {dataset['datetime_columns']}")

    print("\n=== DATA QUALITY ===")

    quality = result["quality"]

    print(f"Duplicate rows: {quality['duplicate_rows']}")
    print(f"Constant columns: {quality['constant_columns']}")

    print("\n=== MISSING VALUES ===")

    if quality["missing_columns"]:
        pprint(quality["missing_columns"])
    else:
        print("No missing values.")

    print("\n=== TARGET CANDIDATES ===")

    for candidate in result["target_candidates"]:
        reasons = ", ".join(candidate["reasons"])

        print(
            f"{candidate['column']}: "
            f"{candidate['score']} → {reasons}"
        )

    print("\n=== ML TASK DETECTION ===")

    print(f"Target: {task['target']}")
    print(f"Task: {task['task_type']}")
    print(f"Subtype: {task['subtype']}")
    print(f"Unique values: {task['unique_count']}")

    if task["class_distribution"]:
        print("Class distribution:")

        for label, rate in task["class_distribution"].items():
            print(f"  {label}: {rate:.1%}")

    print("\n=== COLUMN PROFILES ===")

    for column, profile in result["columns"].items():
        print(f"\n[{column}]")
        pprint(profile)


if __name__ == "__main__":
    main()