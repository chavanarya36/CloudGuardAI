from __future__ import annotations

import pytest
from pathlib import Path
from typing import Any, Dict, List

import types

try:
    import app
    import utils.core_predictor  # noqa: F401
except ImportError:
    pytest.skip("utils/app packages not available", allow_module_level=True)


def test_compute_unified_risk_backend_with_mocks(monkeypatch, tmp_path):
    # Create a dummy IaC file path and content
    file_path = tmp_path / "main.tf"
    file_path.write_text("resource \"aws_s3_bucket\" \"b\" {}", encoding="utf-8")
    content = file_path.read_text(encoding="utf-8")

    # Mock CorePredictor.predict_X to return a fixed probability
    class DummyCorePredictor:
        def __init__(self, mode: str = "hybrid") -> None:  # pragma: no cover - trivial
            self.mode = mode

        def predict_X(self, X):  # pragma: no cover - trivial
            return {"risk_probability": 0.8}

    def fake_core_predictor(mode: str = "hybrid"):
        return DummyCorePredictor(mode=mode)

    # Patch inside app.compute_unified_risk's lazy import path
    import utils.core_predictor as core_mod
    monkeypatch.setattr(core_mod, "CorePredictor", fake_core_predictor)

    # Mock PredictionEngine.feature_extractor.extract_features_single
    class DummyExtractor:
        def extract_features_single(self, file_path: str, content: str):  # pragma: no cover - trivial
            from scipy import sparse
            import numpy as np

            X = sparse.csr_matrix([[0.0]])
            return X, {}

    from utils import prediction_engine as pe_mod

    class DummyPE:
        def __init__(self):  # pragma: no cover - trivial
            self.feature_extractor = DummyExtractor()

    monkeypatch.setattr(pe_mod, "PredictionEngine", DummyPE)

    # Mock rules_engine.engine.scan_single_file
    from rules_engine import engine as re_engine

    def fake_scan_single_file(path, content):
        # Return normalized dict (not Finding object)
        return [{
            "rule_id": "RULE_X",
            "severity": "HIGH",
            "file_path": str(file_path.name),
            "resource": "",
            "title": "Test Rule",
            "description": "Test description",
            "references": [],
            "code_snippet": "",
            "line": 1,
        }]

    monkeypatch.setattr(re_engine, "scan_single_file", fake_scan_single_file)

    # Mock llm_reasoner.explain_and_remediate to avoid network calls
    from rules_engine import llm_reasoner as llm_mod

    def fake_explain_and_remediate(finding: Dict[str, Any], file_content: str) -> Dict[str, Any]:
        return {
            "explanation": "test explanation",
            "remediation": "test remediation",
            "certainty": 0.42,
        }

    monkeypatch.setattr(llm_mod, "explain_and_remediate", fake_explain_and_remediate)

    # Run backend helper
    backend = app.compute_unified_risk(file_path, content)

    # Validate shape
    assert set(backend.keys()) == {"unified_probability", "band", "breakdown", "findings"}
    assert 0.0 <= backend["unified_probability"] <= 1.0
    assert backend["band"] in {"LOW", "MEDIUM", "HIGH"}
    assert isinstance(backend["breakdown"], dict)

    findings: List[Dict[str, Any]] = backend["findings"]
    assert findings
    assert findings[0]["rule_id"] == "RULE_X"
    assert findings[0]["llm_certainty"] == 0.42
