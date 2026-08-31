from __future__ import annotations

from pathlib import Path
from typing import Any

from backend.app.services.automl_runner import AutoMLRunResult
from backend.app.services.ai_analyst import analyze_automl_result


def _fmt(value: Any, digits: int = 4) -> str:
    if value is None:
        return "N/A"

    if isinstance(value, float):
        return f"{value:.{digits}f}"

    return str(value)


def generate_markdown_report(
    automl_result: AutoMLRunResult,
    analysis: dict[str, Any] | None = None,
) -> str:
    """
    AutoML 실행 결과를 Markdown 리포트로 변환.
    """

    if analysis is None:
        analysis = analyze_automl_result(automl_result)

    output = automl_result.to_dict()
    prep = output["preprocessing_summary"]
    best = output["best_result"]

    lines: list[str] = []

    lines.append("# AI AutoML Analyst Report")
    lines.append("")
    lines.append("## 1. Problem Summary")
    lines.append("")
    lines.append(f"- Target column: `{automl_result.target_column}`")
    lines.append(f"- Task type: `{automl_result.task_type}`")
    lines.append(f"- Interpretation: {analysis['task_interpretation']}")
    lines.append("")
    lines.append("## 2. Dataset / Preprocessing Summary")
    lines.append("")
    lines.append(f"- Rows used: `{prep['n_rows']}`")
    lines.append(f"- Features before encoding: `{prep['n_features_before_encoding']}`")
    lines.append(f"- Numeric features: `{len(prep['numeric_features'])}`")
    lines.append(f"- Categorical features: `{len(prep['categorical_features'])}`")
    lines.append(f"- Datetime features detected: `{len(prep['datetime_features'])}`")
    lines.append(f"- Dropped features: `{len(prep['dropped_features'])}`")
    lines.append("")

    if prep["numeric_features"]:
        lines.append("### Numeric Features")
        lines.append("")
        for col in prep["numeric_features"]:
            lines.append(f"- `{col}`")
        lines.append("")

    if prep["categorical_features"]:
        lines.append("### Categorical Features")
        lines.append("")
        for col in prep["categorical_features"]:
            lines.append(f"- `{col}`")
        lines.append("")

    if prep["datetime_features"]:
        lines.append("### Datetime Features")
        lines.append("")
        for col in prep["datetime_features"]:
            lines.append(f"- `{col}`")
        lines.append("")

    if prep["dropped_features"]:
        lines.append("### Dropped Features")
        lines.append("")
        for col in prep["dropped_features"]:
            lines.append(f"- `{col}`")
        lines.append("")

    lines.append("## 3. Metric Interpretation")
    lines.append("")
    lines.append(analysis["metric_interpretation"])
    lines.append("")

    lines.append("## 4. Model Ranking")
    lines.append("")
    lines.append("| Rank | Model | Primary Metric | Mean | Std | Fit Time |")
    lines.append("|---:|---|---|---:|---:|---:|")

    for item in output["ranked_results"]:
        lines.append(
            "| "
            f"{item['rank']} | "
            f"{item['model_name']} | "
            f"{item['primary_metric']} | "
            f"{_fmt(item['primary_score_mean'])} | "
            f"{_fmt(item['primary_score_std'])} | "
            f"{_fmt(item['fit_time_mean'])} |"
        )

    lines.append("")

    lines.append("## 5. Best Model")
    lines.append("")

    if best:
        lines.append(f"- Best model: `{best['model_name']}`")
        lines.append(f"- Primary metric: `{best['primary_metric']}`")
        lines.append(f"- Mean score: `{_fmt(best['primary_score_mean'])}`")
        lines.append(f"- Score std: `{_fmt(best['primary_score_std'])}`")
        lines.append("")
        if analysis["best_model_summary"]:
            lines.append(analysis["best_model_summary"]["quality_comment"])
            lines.append("")
    else:
        lines.append("No successful model was found.")
        lines.append("")

    lines.append("## 6. Model Recommendations")
    lines.append("")

    for rec in analysis["recommendations"]:
        lines.append(f"### Rank {rec['rank']} - {rec['model_name']}")
        lines.append("")
        lines.append(f"- Score: `{_fmt(rec['primary_score_mean'])}`")
        lines.append(f"- Std: `{_fmt(rec['primary_score_std'])}`")
        lines.append("- Reasons:")
        for reason in rec["reasons"]:
            lines.append(f"  - {reason}")
        lines.append("")

    lines.append("## 7. Risks / Cautions")
    lines.append("")

    for risk in analysis["risks"]:
        lines.append(f"- {risk}")

    lines.append("")

    lines.append("## 8. Next Actions")
    lines.append("")

    for action in analysis["next_actions"]:
        lines.append(f"- {action}")

    lines.append("")

    return "\n".join(lines)


def save_markdown_report(
    report: str,
    path: str | Path,
) -> Path:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(report, encoding="utf-8")
    return output_path