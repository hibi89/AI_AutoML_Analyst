"""P6E5 local synthetic data generator's non-report paths are safe to run anywhere."""
from __future__ import annotations

from pathlib import Path

from scripts.p6e5_windows_demo import _fresh_run_dir, synthetic_frame, _windows_cmd_failure_category


def test_replay_fixture_is_explicitly_synthetic():
    frame = synthetic_frame()
    assert frame.shape == (150, 5)
    assert set(frame["지역"].dropna()) == {"SYN_A", "SYN_B", "SYN_C"}
    assert frame["매출"].isna().sum() == 10


def test_review_pack_allocates_new_directory_without_overwrite(tmp_path):
    path = Path(tmp_path)
    first = _fresh_run_dir(path)
    (first / "PRESERVE.txt").write_text("existing-review-evidence")
    second = _fresh_run_dir(path)
    assert first != second
    assert (first / "PRESERVE.txt").read_text() == "existing-review-evidence"


def test_windows_batch_failure_classification_is_pathless():
    cases = [
        ("'python' is not recognized as an internal or external command", "PYTHON_NOT_ON_CMD_PATH"),
        ("ModuleNotFoundError: No module named 'skops'", "MISSING_PYTHON_MODULE"),
        ("ERROR: Dependency versions differ. Install requirements.", "DEPENDENCY_VERSION_MISMATCH"),
        ("ERROR: Input header mismatch. Use the exact ordered columns.", "CSV_SCHEMA_MISMATCH"),
        ("ERROR: Model checksum mismatch. Stop.", "MODEL_INTEGRITY_REJECTED"),
        ("FileNotFoundError: [Errno 2] No such file in C:\\Private", "MISSING_LOCAL_FILE_OR_PATH"),
        ("PermissionError: permission denied", "FILE_PERMISSION_ERROR"),
        ("ERROR: Output path exists. Choose a new name.", "OUTPUT_ALREADY_EXISTS"),
        ("Traceback (most recent call last): local_path_in_private_data", "PYTHON_EXECUTION_ERROR"),
        ("unrecognized local error E:\\Private\\customer.csv", "UNCLASSIFIED_CMD_FAILURE"),
    ]
    for output, category in cases:
        classified = _windows_cmd_failure_category(output)
        assert classified == category
        assert "Private" not in classified
        assert "customer" not in classified
