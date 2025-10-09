# CloudGuardAI

A high-performance, industry-grade web application to assess security risk in Infrastructure-as-Code (IaC) files using a trained machine learning model and interpretable feature engineering.

## Core Idea

Infrastructure misconfigurations (public buckets, overly-permissive security groups, plaintext secrets, etc.) frequently slip through code reviews. CloudGuardAI augments traditional policy scanners by learning statistical risk patterns from real-world IaC, combining:

- Path semantics (folder names, file names, n-grams)
- Resource tokens (Terraform/K8s keywords and provider objects)
- Structural features (size, lines, file type, CI/test signals)

This hybrid representation feeds a calibrated Logistic Regression model to produce a risk probability and an interpretable decision. The UI surfaces context, confidence, and recommendations to accelerate triage.

## What’s Included

- Production-ready Streamlit UI with a modern “mission control” design
- Single-file and batch (ZIP / directory) analysis flows
- Plotly visualizations: risk gauges, distributions, and executive dashboards
- Robust feature pipeline aligned to model expectations (auto pad/truncate)
- Detailed explanations with token highlights and structural signals
- Export options (CSV, summary JSON) for reporting workflows

## Quick Start

Requirements: Python 3.11, packages in `requirements.txt`, and model artifacts in `models_artifacts/` and `features_artifacts/`.

```bash
pip install -r requirements.txt
# Start UI (Windows PowerShell)
& "C:/Program Files/Python311/python.exe" -m streamlit run app.py
```

Open http://localhost:8501

## Project Structure

```
app.py                          # Streamlit app (hi‑tech UI)
utils/
  feature_extractor.py          # Deterministic hashing + dense features
  model_loader.py               # Loads model, threshold, metrics
  prediction_engine.py          # Alignment, explanations, batch ZIP flow
models_artifacts/               # best_model_lr.joblib, threshold_lr.json, metrics
features_artifacts/             # feature_meta.json or meta.json
```

## Model + Features

- Model: Logistic Regression (liblinear)
- Training metrics (OOF): PR‑AUC ≈ 0.337, ROC‑AUC ≈ 0.972
- Expected dimension: derived from `model.n_features_in_` (e.g., 32790)
- Runtime extractor auto‑aligns shapes by padding/truncation, avoiding errors if meta/hash settings drift.

## How to Use

- Single File: Upload .tf/.yaml/.yml/.json/.bicep; see risk and explanation.
- Batch: Upload a ZIP or point to a directory; review dashboard and export.
- Threshold: Tune in the sidebar to balance recall vs. precision.

## Sample File

A deliberately risky Terraform example is included: `test_high_risk.tf`.
Use it to validate flags for public S3, permissive SG, admin IAM, unencrypted volumes, and secret‑like tokens.

## Roadmap

- Add token contribution chart (feature importance surrogate)
- CI integration (pre-commit hook, GitHub Action example)
- Fine-tune per‑provider detectors and normalization

## License

Add your license terms here.
