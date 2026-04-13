# ml_rules.md — Competition Rules Template

> This file is authored by System_Architect at the start of each competition run and loaded verbatim into every Action Node's system prompt each loop. It is the dynamic layer of the two-layer prompt architecture.
>
> Fill in all `<...>` placeholders. Delete this header block before saving the live version.

---

## Competition Context

**Name:** <competition name>
**Task type:** <binary classification | multiclass | regression | ranking | ...>
**Evaluation metric:** <AUC-ROC | RMSE | MAP@K | ...> — higher is better / lower is better
**Submission deadline:** <date or "open">

---

## Medal Targets

> These are the leaderboard score thresholds for medal placement.
> Use them as calibration markers to know if you're in the right ballpark.
> Design the pipeline to be capable of gold-level performance, but
> optimize by ML instinct (CV trends, overfitting signals), not by
> chasing these numbers.

| Medal | Score Threshold |
|-------|-----------------|
| Gold | `<gold_score>` |
| Silver | `<silver_score>` |
| Bronze | `<bronze_score>` |
| Median | `<median_score>` |

**Score direction:** <higher is better / lower is better>
**Interpretation:** <For "higher is better": your score must be >= threshold. For "lower is better": your score must be <= threshold.>

---

## I/O Paths

> All paths below are relative to the competition workspace root.

| Artifact | Path |
|---|---|
| Raw train data | `<path/to/train.csv or .parquet>` |
| Raw test data | `<path/to/test.csv or .parquet>` |
| Sample submission | `<path/to/sample_submission.csv>` |
| Processed train arrays | `<path/to/processed/X_train.npy>, <path/to/processed/y_train.npy>` |
| Processed validation arrays | `<path/to/processed/X_val.npy>, <path/to/processed/y_val.npy>` |
| Processed test arrays | `<path/to/processed/X_test.npy>` |
| Trained model artifact | `<path/to/models/model.pkl or model.pt>` |
| Metric log | `<path/to/logs/metrics.txt>` |
| Submission file | `<path/to/submission.csv>` |

All nodes must read and write to exactly these paths. Do not invent new paths.

---

## Submission Format

```
<column_1_name>,<column_2_name>
<example_id_1>,<example_prediction_1>
<example_id_2>,<example_prediction_2>
```

- Row count must match test data exactly: `<N>` rows
- ID column name: `<id_column>`
- Prediction column name: `<target_column>`
- Prediction dtype: `<float | int | string>`
- Prediction range: `<[0, 1] | [0, N_classes) | ...>`

---

## Constraints

- <Any competition-specific rule, e.g. "External data not permitted">
- <Any known data quirks, e.g. "Target column has 3% missing values in train; treat as negative class">
- **Hardware:** <GPU availability, e.g. "GPU at /dev/cuda:0" or "CPU only">
- **Storage:** <Available disk, e.g. "~10 GB workspace disk — check `df -h .` before downloading large models or caching datasets. Clean up temp files after use.">
- **Time budget:** <Wall-clock limit, e.g. "~1 hour ideal, 1.5 hour typical, 2 hour hard cap">

---

## Ethics & First Principles

- **No solution lookup.** Do not search the internet for competition solutions, kernels, discussion threads, or leaderboard strategies. Treat every problem from first principles using the data provided.
- **Standard open-source and dataset licensing.** Use only permissively licensed libraries. Do not redistribute raw competition data outside the workspace.

---

## Version Control

All git operations run inside this competition workspace (initialized during bootstrap).

- **Commit on every Sign-Off** — each commit represents a completed node shift, not incremental saves.
- **Stage only relevant files** — never stage raw data files, model binaries larger than necessary, or temporary scripts.
- **Descriptive commit messages** in imperative mood: "Add feature engineering pipeline", not "Added..."
- **Never auto-push** — this workspace is local only.

---

## Dependency Management
This workspace uses `uv` for isolated dependency management. All commands run inside this workspace's own virtual environment.

- **Install packages** with `uv add <package>` — this updates `pyproject.toml` and `uv.lock` automatically.
- **Run scripts** with `uv run python <script.py>` to execute inside the isolated environment.
- **Never install globally** — do not use bare `pip install` or modify any environment outside this workspace.

---

## Verification

After finishing or editing any pipeline script, you **MUST** run it and verify the output before moving on. Check: shapes match expectations, dtypes are correct, no NaN where there shouldn't be, output files exist at the expected paths. Do not mark a task complete on code alone — run it.

