#!/usr/bin/env python3
"""Run a small, reproducible SEM-style analysis using only the Python stdlib.

The model estimates four latent constructs from simulated survey indicators and
then fits the structural paths with standardized multiple regression:

    academic_performance ~ study_habits + sleep_quality + academic_stress

This is intentionally dependency-free so it can run in minimal Python
environments.  For production SEM work with full-information maximum likelihood,
fit indices, and standard errors, use a dedicated package such as semopy, lavaan,
or statsmodels once dependencies are available.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import random
import statistics
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATA = ROOT / "outputs" / "simulated_sem_data.csv"
DEFAULT_JSON = ROOT / "outputs" / "sem_results.json"
DEFAULT_REPORT = ROOT / "outputs" / "sem_report.md"
DEFAULT_ARCHIVE = ROOT / "outputs" / "sem_outputs.zip"

MODEL_SPEC = {
    "study_habits": ["study_plan", "focus_time", "assignment_pace"],
    "sleep_quality": ["sleep_duration", "sleep_consistency", "restedness"],
    "academic_stress": ["deadline_pressure", "test_anxiety", "overload"],
    "academic_performance": ["gpa_proxy", "exam_score", "project_score"],
}
PREDICTORS = ["study_habits", "sleep_quality", "academic_stress"]
OUTCOME = "academic_performance"


@dataclass(frozen=True)
class RegressionResult:
    intercept: float
    coefficients: dict[str, float]
    r_squared: float
    rmse: float


def mean(values: Iterable[float]) -> float:
    return statistics.fmean(values)


def sample_stdev(values: list[float]) -> float:
    return statistics.stdev(values)


def z_scores(values: list[float]) -> list[float]:
    avg = mean(values)
    sd = sample_stdev(values)
    if sd == 0:
        raise ValueError("Cannot standardize a constant column.")
    return [(value - avg) / sd for value in values]


def dot(left: list[float], right: list[float]) -> float:
    return sum(a * b for a, b in zip(left, right, strict=True))


def correlation(left: list[float], right: list[float]) -> float:
    z_left = z_scores(left)
    z_right = z_scores(right)
    return dot(z_left, z_right) / (len(left) - 1)


def solve_linear_system(matrix: list[list[float]], vector: list[float]) -> list[float]:
    """Solve Ax=b with Gaussian elimination and partial pivoting."""
    n = len(vector)
    augmented = [row[:] + [vector[i]] for i, row in enumerate(matrix)]

    for pivot_col in range(n):
        pivot_row = max(range(pivot_col, n), key=lambda row: abs(augmented[row][pivot_col]))
        if abs(augmented[pivot_row][pivot_col]) < 1e-12:
            raise ValueError("Regression matrix is singular.")
        augmented[pivot_col], augmented[pivot_row] = augmented[pivot_row], augmented[pivot_col]

        pivot = augmented[pivot_col][pivot_col]
        augmented[pivot_col] = [value / pivot for value in augmented[pivot_col]]

        for row in range(n):
            if row == pivot_col:
                continue
            factor = augmented[row][pivot_col]
            augmented[row] = [
                value - factor * augmented[pivot_col][col]
                for col, value in enumerate(augmented[row])
            ]

    return [augmented[row][-1] for row in range(n)]


def multiple_regression(rows: list[dict[str, float]], predictors: list[str], outcome: str) -> RegressionResult:
    y = [row[outcome] for row in rows]
    x_columns = [[1.0 for _ in rows]] + [[row[predictor] for row in rows] for predictor in predictors]
    xtx = [[dot(col_i, col_j) for col_j in x_columns] for col_i in x_columns]
    xty = [dot(col, y) for col in x_columns]
    beta = solve_linear_system(xtx, xty)

    fitted = [sum(beta[col] * x_columns[col][row] for col in range(len(beta))) for row in range(len(rows))]
    residuals = [actual - predicted for actual, predicted in zip(y, fitted, strict=True)]
    sse = sum(error * error for error in residuals)
    y_mean = mean(y)
    sst = sum((actual - y_mean) ** 2 for actual in y)
    rmse = math.sqrt(sse / len(rows))
    r_squared = 1 - (sse / sst)

    return RegressionResult(
        intercept=beta[0],
        coefficients={predictor: beta[i + 1] for i, predictor in enumerate(predictors)},
        r_squared=r_squared,
        rmse=rmse,
    )


def cronbach_alpha(indicator_rows: list[list[float]]) -> float:
    if len(indicator_rows[0]) < 2:
        raise ValueError("Cronbach alpha requires at least two indicators.")
    item_count = len(indicator_rows[0])
    columns = list(zip(*indicator_rows, strict=True))
    item_variance_sum = sum(statistics.variance(column) for column in columns)
    total_scores = [sum(row) for row in indicator_rows]
    total_variance = statistics.variance(total_scores)
    return (item_count / (item_count - 1)) * (1 - item_variance_sum / total_variance)


def clamp(value: float, low: float = 1.0, high: float = 7.0) -> float:
    return max(low, min(high, value))


def simulate_data(path: Path, sample_size: int, seed: int) -> list[dict[str, float]]:
    rng = random.Random(seed)
    rows: list[dict[str, float]] = []

    for respondent_id in range(1, sample_size + 1):
        study_habits = rng.gauss(0, 1)
        sleep_quality = 0.30 * study_habits + rng.gauss(0, 0.95)
        academic_stress = -0.35 * study_habits - 0.45 * sleep_quality + rng.gauss(0, 0.90)
        academic_performance = (
            0.52 * study_habits
            + 0.34 * sleep_quality
            - 0.41 * academic_stress
            + rng.gauss(0, 0.85)
        )

        latent_values = {
            "study_habits": study_habits,
            "sleep_quality": sleep_quality,
            "academic_stress": academic_stress,
            "academic_performance": academic_performance,
        }
        row: dict[str, float] = {"respondent_id": float(respondent_id)}
        for construct, indicators in MODEL_SPEC.items():
            for indicator in indicators:
                indicator_score = 4 + 0.85 * latent_values[construct] + rng.gauss(0, 0.55)
                row[indicator] = round(clamp(indicator_score), 3)
        rows.append(row)

    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as csv_file:
        fieldnames = ["respondent_id"] + [indicator for indicators in MODEL_SPEC.values() for indicator in indicators]
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    return rows


def read_csv(path: Path) -> list[dict[str, float]]:
    with path.open(newline="", encoding="utf-8") as csv_file:
        reader = csv.DictReader(csv_file)
        return [{key: float(value) for key, value in row.items()} for row in reader]


def estimate_construct_scores(rows: list[dict[str, float]]) -> tuple[list[dict[str, float]], dict[str, dict[str, float]]]:
    raw_scores: dict[str, list[float]] = {}
    measurement: dict[str, dict[str, float]] = {}

    for construct, indicators in MODEL_SPEC.items():
        standardized_items = {indicator: z_scores([row[indicator] for row in rows]) for indicator in indicators}
        construct_raw = [mean([standardized_items[indicator][i] for indicator in indicators]) for i in range(len(rows))]
        raw_scores[construct] = construct_raw

        indicator_rows = [[row[indicator] for indicator in indicators] for row in rows]
        measurement[construct] = {
            "cronbach_alpha": cronbach_alpha(indicator_rows),
            **{
                f"loading_{indicator}": correlation([row[indicator] for row in rows], construct_raw)
                for indicator in indicators
            },
        }

    standardized_constructs = {construct: z_scores(scores) for construct, scores in raw_scores.items()}
    construct_rows = [
        {construct: standardized_constructs[construct][i] for construct in MODEL_SPEC}
        for i in range(len(rows))
    ]
    return construct_rows, measurement


def write_outputs(
    json_path: Path,
    report_path: Path,
    archive_path: Path,
    data_path: Path,
    sample_size: int,
    seed: int,
    measurement: dict[str, dict[str, float]],
    regression: RegressionResult,
) -> None:
    payload = {
        "model": f"{OUTCOME} ~ {' + '.join(PREDICTORS)}",
        "sample_size": sample_size,
        "seed": seed,
        "measurement": measurement,
        "structural_model": {
            "intercept": regression.intercept,
            "standardized_paths": regression.coefficients,
            "r_squared": regression.r_squared,
            "rmse": regression.rmse,
        },
    }

    json_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    lines = [
        "# SEM Analysis Report",
        "",
        f"Model: `{payload['model']}`",
        f"Sample size: {sample_size}",
        f"Random seed: {seed}",
        "",
        "## Measurement model",
        "",
        "| Construct | Cronbach alpha | Indicator loadings |",
        "| --- | ---: | --- |",
    ]
    for construct, stats in measurement.items():
        loadings = ", ".join(
            f"{name.replace('loading_', '')}={value:.3f}"
            for name, value in stats.items()
            if name.startswith("loading_")
        )
        lines.append(f"| {construct} | {stats['cronbach_alpha']:.3f} | {loadings} |")

    lines.extend(
        [
            "",
            "## Structural model",
            "",
            "| Path | Standardized estimate |",
            "| --- | ---: |",
        ]
    )
    for predictor, coefficient in regression.coefficients.items():
        lines.append(f"| {predictor} → {OUTCOME} | {coefficient:.3f} |")
    lines.extend(
        [
            "",
            f"R²: {regression.r_squared:.3f}",
            f"RMSE: {regression.rmse:.3f}",
            "",
            "Interpretation: stronger study habits and sleep quality are associated with higher academic performance, while higher academic stress is associated with lower academic performance in this simulated dataset.",
        ]
    )
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    archive_path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(archive_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for artifact in (data_path, json_path, report_path):
            archive.write(artifact, arcname=artifact.name)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run a reproducible SEM-style analysis in Python.")
    parser.add_argument("--data", type=Path, default=DEFAULT_DATA, help="CSV input/output path.")
    parser.add_argument("--json", type=Path, default=DEFAULT_JSON, help="JSON results path.")
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT, help="Markdown report path.")
    parser.add_argument("--archive", type=Path, default=DEFAULT_ARCHIVE, help="ZIP archive path for downloadable outputs.")
    parser.add_argument("--sample-size", type=int, default=250, help="Simulated sample size when generating data.")
    parser.add_argument("--seed", type=int, default=20260510, help="Random seed for reproducibility.")
    parser.add_argument("--use-existing-data", action="store_true", help="Read --data instead of regenerating it.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.use_existing_data:
        rows = read_csv(args.data)
    else:
        rows = simulate_data(args.data, args.sample_size, args.seed)

    construct_rows, measurement = estimate_construct_scores(rows)
    regression = multiple_regression(construct_rows, PREDICTORS, OUTCOME)
    write_outputs(args.json, args.report, args.archive, args.data, len(rows), args.seed, measurement, regression)

    print(f"Wrote data to {args.data}")
    print(f"Wrote JSON results to {args.json}")
    print(f"Wrote report to {args.report}")
    print(f"Wrote downloadable archive to {args.archive}")
    print(f"R-squared: {regression.r_squared:.3f}")
    for predictor, coefficient in regression.coefficients.items():
        print(f"{predictor} -> {OUTCOME}: {coefficient:.3f}")


if __name__ == "__main__":
    main()
