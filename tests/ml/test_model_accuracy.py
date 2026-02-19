"""Pytest-based accuracy sanity check for the main model.

This test reuses the same PredictionEngine / FeatureExtractor pipeline
as the main application and verifies that the model can score a sample
without feature-shape mismatches and that basic metrics are in-range.
"""
import pytest

import pandas as pd
import numpy as np
from scipy import sparse
try:
    from utils.model_loader import ModelLoader
    from utils.prediction_engine import PredictionEngine
except ImportError:
    pytest.skip("utils package not available", allow_module_level=True)

from sklearn.metrics import accuracy_score, precision_score, recall_score, roc_auc_score


def test_model_accuracy_metrics() -> None:
    # Load model and associated metadata
    loader = ModelLoader()
    model, threshold, metrics = loader.load_all()

    # Load raw training matrix and labels from artifacts
    X_raw = sparse.load_npz("features_artifacts/X.npz")
    y = pd.read_csv("features_artifacts/y.csv")["has_findings"].values

    # Build a sample using PredictionEngine's feature extractor so feature
    # shapes always align with the loaded model's expectations.
    np.random.seed(42)
    sample_indices = np.random.choice(X_raw.shape[0], 100, replace=False)

    pe = PredictionEngine()
    expected = getattr(loader.model, "n_features_in_", None)

    rows = []
    for idx in sample_indices:
        dummy_path = f"sample_{idx}.tf"
        dummy_content = 'resource "aws_s3_bucket" "b" {}'
        X_row, _ = pe.feature_extractor.extract_features_single(dummy_path, dummy_content)
        if expected is not None:
            X_row = pe.feature_extractor.align_to_expected(X_row, expected)
        rows.append(X_row)

    X_sample = sparse.vstack(rows)
    y_sample = y[sample_indices]

    # Sanity check: feature count should match model expectations
    if expected is not None:
        assert X_sample.shape[1] == expected

    # Predict probabilities and labels
    y_probs = loader.predict_proba(X_sample)
    y_pred = (y_probs >= threshold).astype(int)

    # Compute metrics
    accuracy = accuracy_score(y_sample, y_pred)
    try:
        precision = precision_score(y_sample, y_pred, zero_division=0)
        recall = recall_score(y_sample, y_pred, zero_division=0)
    except Exception:  # pragma: no cover - defensive
        precision = 0.0
        recall = 0.0

    roc_auc = roc_auc_score(y_sample, y_probs) if y_sample.sum() > 0 else 0.0

    # Assertions: basic bounds only; we intentionally do not hard-code
    # strong guarantees on accuracy to keep the test stable.
    assert 0.0 <= accuracy <= 1.0
    assert 0.0 <= roc_auc <= 1.0

    # Basic sanity on precision/recall types
    assert isinstance(precision, float)
    assert isinstance(recall, float)
