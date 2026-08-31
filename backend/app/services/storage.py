from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any
from uuid import uuid4


EXPERIMENTS_DIR = Path("experiments")


def create_job_id() -> str:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    short_uuid = uuid4().hex[:8]
    return f"run_{timestamp}_{short_uuid}"


def get_job_dir(job_id: str) -> Path:
    if not job_id or "/" in job_id or "\\" in job_id or ".." in job_id:
        raise ValueError("Invalid job_id.")

    return EXPERIMENTS_DIR / job_id


def save_analysis_result(
    result_payload: dict[str, Any],
    report_markdown: str,
) -> dict[str, Any]:
    """
    분석 결과와 Markdown 리포트를 experiments/{job_id}/ 아래 저장.
    """

    job_id = create_job_id()
    job_dir = get_job_dir(job_id)
    job_dir.mkdir(parents=True, exist_ok=True)

    result_path = job_dir / "result.json"
    report_path = job_dir / "report.md"

    job_info = {
        "job_id": job_id,
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "storage": {
            "job_dir": str(job_dir),
            "result_json": str(result_path),
            "report_markdown": str(report_path),
        },
    }

    payload_to_save = dict(result_payload)
    payload_to_save["job"] = job_info

    result_path.write_text(
        json.dumps(payload_to_save, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    report_path.write_text(
        report_markdown,
        encoding="utf-8",
    )

    return job_info


def load_result(job_id: str) -> dict[str, Any]:
    job_dir = get_job_dir(job_id)
    result_path = job_dir / "result.json"

    if not result_path.exists():
        raise FileNotFoundError(f"Result not found for job_id: {job_id}")

    return json.loads(result_path.read_text(encoding="utf-8"))


def load_report(job_id: str) -> str:
    job_dir = get_job_dir(job_id)
    report_path = job_dir / "report.md"

    if not report_path.exists():
        raise FileNotFoundError(f"Report not found for job_id: {job_id}")

    return report_path.read_text(encoding="utf-8")


def list_jobs(limit: int = 50) -> list[dict[str, Any]]:
    if not EXPERIMENTS_DIR.exists():
        return []

    jobs: list[dict[str, Any]] = []

    for job_dir in sorted(EXPERIMENTS_DIR.iterdir(), reverse=True):
        if not job_dir.is_dir():
            continue

        result_path = job_dir / "result.json"
        report_path = job_dir / "report.md"

        job_item: dict[str, Any] = {
            "job_id": job_dir.name,
            "has_result": result_path.exists(),
            "has_report": report_path.exists(),
            "result_path": str(result_path) if result_path.exists() else None,
            "report_path": str(report_path) if report_path.exists() else None,
        }

        if result_path.exists():
            try:
                data = json.loads(result_path.read_text(encoding="utf-8"))
                job_item["target_column"] = (
                    data.get("request", {}).get("target_column")
                    or data.get("automl_result", {}).get("target_column")
                )
                job_item["task_type"] = (
                    data.get("request", {}).get("task_type")
                    or data.get("automl_result", {}).get("task_type")
                )
                job_item["best_model"] = (
                    data.get("automl_result", {})
                    .get("best_result", {})
                    .get("model_name")
                )
            except Exception:
                pass

        jobs.append(job_item)

        if len(jobs) >= limit:
            break

    return jobs