# SEMwork

This repository contains a dependency-free Python workflow for running a small structural equation modeling (SEM) style analysis. The example estimates a measurement model from survey-style indicators, creates standardized latent construct scores, and fits this structural model:

```text
academic_performance ~ study_habits + sleep_quality + academic_stress
```

## Files

- `scripts/run_sem_analysis.py` simulates reproducible survey data, estimates construct reliability/loadings, fits the structural paths with standardized multiple regression, and writes analysis artifacts.
- `outputs/simulated_sem_data.csv` is the generated example dataset.
- `outputs/sem_results.json` contains machine-readable SEM results.
- `outputs/sem_report.md` contains a readable summary of the measurement and structural model.
- `outputs/sem_outputs.zip` is generated locally when you run the analysis and contains the CSV, JSON, and Markdown outputs. This ZIP is intentionally not committed because PR systems often do not support binary file review.

## Run the analysis

```bash
python scripts/run_sem_analysis.py
```

To analyze an existing CSV with the same indicator columns, pass `--use-existing-data`:

```bash
python scripts/run_sem_analysis.py --data outputs/simulated_sem_data.csv --use-existing-data
```

## Download the output

After running the analysis, download or copy the locally generated `outputs/sem_outputs.zip` to get all outputs in one file. The ZIP is ignored by git so pull requests stay text-only and reviewable. If you only need a specific artifact, use `outputs/sem_report.md` for the readable report, `outputs/sem_results.json` for machine-readable results, or `outputs/simulated_sem_data.csv` for the generated dataset.

You can also choose a different ZIP location:

```bash
python scripts/run_sem_analysis.py --archive outputs/my_sem_outputs.zip
```

## Notes

This script is intentionally implemented with the Python standard library so it runs in minimal environments. For production SEM with full-information maximum likelihood, global fit indices, and inferential statistics, use a dedicated SEM package such as `semopy` or `lavaan`.
