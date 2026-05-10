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

## Run the analysis

```bash
python scripts/run_sem_analysis.py
```

To analyze an existing CSV with the same indicator columns, pass `--use-existing-data`:

```bash
python scripts/run_sem_analysis.py --data outputs/simulated_sem_data.csv --use-existing-data
```

## Notes

This script is intentionally implemented with the Python standard library so it runs in minimal environments. For production SEM with full-information maximum likelihood, global fit indices, and inferential statistics, use a dedicated SEM package such as `semopy` or `lavaan`.
