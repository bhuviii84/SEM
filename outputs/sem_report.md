# SEM Analysis Report

Model: `academic_performance ~ study_habits + sleep_quality + academic_stress`
Sample size: 250
Random seed: 20260510

## Measurement model

| Construct | Cronbach alpha | Indicator loadings |
| --- | ---: | --- |
| study_habits | 0.833 | study_plan=0.866, focus_time=0.864, assignment_pace=0.868 |
| sleep_quality | 0.874 | sleep_duration=0.889, sleep_consistency=0.892, restedness=0.901 |
| academic_stress | 0.905 | deadline_pressure=0.923, test_anxiety=0.920, overload=0.908 |
| academic_performance | 0.935 | gpa_proxy=0.945, exam_score=0.935, project_score=0.941 |

## Structural model

| Path | Standardized estimate |
| --- | ---: |
| study_habits → academic_performance | 0.340 |
| sleep_quality → academic_performance | 0.158 |
| academic_stress → academic_performance | -0.453 |

R²: 0.553
RMSE: 0.667

Interpretation: stronger study habits and sleep quality are associated with higher academic performance, while higher academic stress is associated with lower academic performance in this simulated dataset.
