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

## I/O Paths

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
- <Hardware constraint if relevant, e.g. "GPU available at /dev/cuda:0; use it for training">
- <Time constraint if relevant, e.g. "Total wall-clock budget: 4 hours">

---

## Active Phase

**Current phase:** <Architecture | DataEngineering | ModelEngineering | Evaluation>
**Active node:** <System_Architect | Data_Engineer | Model_Engineer | Evaluator>

> Update this section when System_Architect writes ml_rules.md, and again whenever Router transitions phases. This gives every node immediate awareness of where the project stands without reading ml_progress.txt.
