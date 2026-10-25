"""P6E5 local synthetic data generator's non-report paths are safe to run anywhere."""
from __future__ import annotations

from pathlib import Path

from scripts.p6e5_windows_demo import _fresh_run_dir, synthetic_frame


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
