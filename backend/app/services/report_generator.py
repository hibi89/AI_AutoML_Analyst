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
    AutoML 실행 결과를 Markdown 리포트로 변환한다.

    특정 모델을 절대적으로 추천하는 보고서가 아니라,
    현재 실험 조건에서의 모델 비교 결과와 해석을 정리하는 보고서다.
    """

    if analysis is None:
        analysis = analyze_automl_result(automl_result)

    output = automl_result.to_dict()
    prep = output["preprocessing_summary"]
    top_result = output["best_result"]

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

    model_selection = output.get("model_selection")
    if model_selection:
        lines.append("## 3. Model Selection Policy")
        lines.append("")
        lines.append(f"- Data size level: `{model_selection['data_size_level']}`")
        lines.append(f"- Selected models: `{len(model_selection['selected_model_names'])}`")
        lines.append(f"- Excluded models: `{len(model_selection['excluded_model_names'])}`")
        lines.append("")
        if model_selection.get("selected_model_names"):
            lines.append("### Selected Model Candidates")
            lines.append("")
            for model_name in model_selection["selected_model_names"]:
                lines.append(f"- `{model_name}`")
            lines.append("")
        if model_selection.get("policy", {}).get("rules"):
            lines.append("### Selection Notes")
            lines.append("")
            for rule in model_selection["policy"]["rules"]:
                lines.append(f"- {rule}")
            lines.append("")

    if prep["numeric_features"]:
        lines.append("## 4. Numeric Features")
        lines.append("")
        for col in prep["numeric_features"]:
            lines.append(f"- `{col}`")
        lines.append("")

    if prep["categorical_features"]:
        lines.append("## 5. Categorical Features")
        lines.append("")
        for col in prep["categorical_features"]:
            lines.append(f"- `{col}`")
        lines.append("")

    if prep["datetime_features"]:
        lines.append("## 6. Datetime Features")
        lines.append("")
        for col in prep["datetime_features"]:
            lines.append(f"- `{col}`")
        lines.append("")

    if prep["dropped_features"]:
        lines.append("## 7. Dropped Features")
        lines.append("")
        for col in prep["dropped_features"]:
            lines.append(f"- `{col}`")
        lines.append("")

    lines.append("## 8. Metric Interpretation")
    lines.append("")
    lines.append(analysis["metric_interpretation"])
    lines.append("")

    lines.append("## 9. Model Ranking")
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

    lines.append("## 10. Top Ranked Model")
    lines.append("")

    if top_result:
        lines.append(f"- Top ranked model: `{top_result['model_name']}`")
        lines.append(f"- Primary metric: `{top_result['primary_metric']}`")
        lines.append(f"- Mean score: `{_fmt(top_result['primary_score_mean'])}`")
        lines.append(f"- Score std: `{_fmt(top_result['primary_score_std'])}`")
        lines.append("")
        top_summary = analysis.get("top_model_summary") or analysis.get("best_model_summary")
        if top_summary:
            lines.append(top_summary["quality_comment"])
            lines.append("")
    else:
        lines.append("No successful model result was found.")
        lines.append("")

    lines.append("## 11. Top Model Result Summaries")
    lines.append("")

    top_summaries = analysis.get("top_model_summaries") or analysis.get("recommendations", [])

    for item in top_summaries:
        lines.append(f"### Rank {item['rank']} - {item['model_name']}")
        lines.append("")
        lines.append(f"- Score: `{_fmt(item['primary_score_mean'])}`")
        lines.append(f"- Std: `{_fmt(item['primary_score_std'])}`")

        observations = item.get("observations") or item.get("reasons") or []

        lines.append("- Observations:")
        for observation in observations:
            lines.append(f"  - {observation}")
        lines.append("")

    lines.append("## 12. Risks / Cautions")
    lines.append("")

    for risk in analysis["risks"]:
        lines.append(f"- {risk}")

    lines.append("")

    lines.append("## 13. Next Actions")
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