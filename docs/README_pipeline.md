# IaC Risk Baseline Pipeline

This directory provides a leakage-aware, reproducible baseline pipeline for predicting whether an Infrastructure-as-Code (IaC) file will have at least one security finding (has_findings). The pipeline is intentionally simple but structured for future enhancement (multi-label, severity modeling, explainability).

## Overview

Stages:
1. 01_prepare_labels.py – Build clean labels avoiding leakage.
2. 02_build_features.py – Construct feature matrices (hash-based tokens + dense structural features) without using any label-derived counts.
3. 03_train_model.py – Train a grouped, calibrated classifier with per-repo evaluation.
4. 04_predict_and_rank.py – Score all files, apply calibration & threshold, produce ranked outputs.

All grouping is performed by `repo_root` to prevent cross-repo leakage and approximate deployment/generalization boundaries.

## Quickstart

```powershell
# 1. Prepare labels (auto-detect checkov file)
python 01_prepare_labels.py --output-dir labels_artifacts --verbose

# 2. Build features
python 02_build_features.py --labels-file labels_artifacts/iac_labels_clean.csv --output-dir features_artifacts --verbose

# 3. Train model
python 03_train_model.py --labels-file labels_artifacts/iac_labels_clean.csv --features-dir features_artifacts --output-dir models_artifacts --verbose

# 4. Predict & rank
python 04_predict_and_rank.py --labels-file labels_artifacts/iac_labels_clean.csv --features-dir features_artifacts --models-dir models_artifacts --output-dir predictions_artifacts --verbose
```

## Artifacts

| Stage | Artifact | Description |
|-------|----------|-------------|
| 01 | labels_artifacts/iac_labels_clean.csv | One row per file with labels + basic metadata |
| 01 | labels_artifacts/iac_labels_summary.csv | Aggregate stats |
| 01 | labels_artifacts/iac_labels_meta.json | Provenance + schema |
| 02 | features_artifacts/X_sparse_joblib.pkl | CSR sparse matrix (path token hashes) |
| 02 | features_artifacts/X_dense.csv | Dense numeric features |
| 02 | features_artifacts/feature_matrix_meta.json | Feature construction parameters |
| 03 | models_artifacts/model.joblib | Trained LogisticRegression classifier |
| 03 | models_artifacts/calibrator.joblib | Isotonic or sigmoid calibrator (if used) |
| 03 | models_artifacts/metrics.json | Global metrics (PR-AUC, ROC-AUC, etc.) |
| 03 | models_artifacts/per_repo_metrics.csv | Metrics per repository (AP, ROC) |
| 03 | models_artifacts/calibration_bins.csv | Calibration reliability table |
| 03 | models_artifacts/threshold.json | Selected decision threshold metadata |
| 04 | predictions_artifacts/predictions.csv | Predictions with probabilities and ranks |
| 04 | predictions_artifacts/top_100_high_risk.csv | Top-100 high-risk files |
| 04 | predictions_artifacts/risk_summary.json | Distribution summary |

## Metrics

Primary: PR-AUC (average precision) – robust under class imbalance.
Secondary: ROC-AUC, Brier Score, Precision/Recall@{1%,5%,10%}, Calibration alignment.
Threshold Selection: Maximizes F1 on validation split.
Calibration: Isotonic if train positives ≥ 200, else sigmoid (Platt scaling). Disabled with `--no-calibration`.

## Leakage Guardrails

Excluded from feature engineering: `num_findings`, `severity_*` counts, `has_findings`, `severity_class`, `unique_check_ids`, `check_ids`, `unique_resources`.
These appear only in label artifact outputs and never feed into model features.

## Extending the Pipeline

Future directions:
- Add severity multiclass head and multi-task joint training.
- Incorporate file content embeddings (ensure content-only, not derived from findings).
- Introduce advanced models (LightGBM, XGBoost) behind an abstraction layer.
- Implement permutation importance & SHAP post-training (sampled due to cost).
- Multi-label top-K check ID prediction as auxiliary objective.

## Reproducibility

All scripts accept explicit input/output args. Hash dimensions and tokenization parameters stored in meta JSON files. Set random seeds for deterministic splitting.

## Sanity / Leakage Tests (Planned)

Script enhancements will add:
- Retrain without path token sparse matrix to observe performance drop.
- Shuffled label experiment (expect PR-AUC ≈ positive prevalence).

## Troubleshooting

| Issue | Cause | Remedy |
|-------|-------|--------|
| Empty predictions or all zeros | Threshold too high | Inspect `threshold.json`, consider manual override in prediction stage |
| NaN metrics per repo | Single-class repo subset | Normal; those repos lack positive examples |
| Calibration bins misaligned | Overfitting or insufficient positives | Increase data, change regularization, or switch calibration method |

## License & Attribution

Internal prototype. Contains no third-party code beyond common Python libraries. Ensure compliance with licensing when integrating external scanners or ML libraries.

---
Generated on first baseline initialization.
