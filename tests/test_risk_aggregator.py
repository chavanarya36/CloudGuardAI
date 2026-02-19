from __future__ import annotations

import pytest
from pathlib import Path
from typing import Any, Dict, List

import json
import math

try:
    from risk_aggregator import aggregate_risk, AggregationConfig
except ImportError:
    pytest.skip("risk_aggregator module not available", allow_module_level=True)


def _write_temp_config(tmp_path: Path, weights: Dict[str, float]) -> Path:
    cfg = {
        "weights": weights,
        "thresholds": {"low": 0.3, "medium": 0.7},
    }
    cfg_path = tmp_path / "hybrid_config.json"
    cfg_path.write_text(json.dumps(cfg), encoding="utf-8")
    return cfg_path


def test_config_weights_must_sum_to_one(tmp_path: Path) -> None:
    cfg_path = _write_temp_config(
        tmp_path,
        {"supervised": 0.4, "unsupervised": 0.3, "rules": 0.2, "llm": 0.1},
    )

    cfg = AggregationConfig.from_file(cfg_path)
    weights_sum = (
        cfg.supervised_weight
        + cfg.unsupervised_weight
        + cfg.rules_weight
        + cfg.llm_weight
    )
    assert math.isclose(weights_sum, 1.0, rel_tol=1e-9, abs_tol=1e-12)


def test_invalid_weights_raise(tmp_path: Path) -> None:
    cfg_path = _write_temp_config(
        tmp_path,
        {"supervised": 0.4, "unsupervised": 0.4, "rules": 0.4, "llm": 0.0},
    )

    try:
        AggregationConfig.from_file(cfg_path)
    except ValueError as exc:  # expected
        assert "weights must sum to 1.0" in str(exc)
    else:  # pragma: no cover - defensive
        assert False, "Expected ValueError for invalid weights"


def test_aggregate_risk_math_and_thresholds(tmp_path: Path) -> None:
    cfg_path = _write_temp_config(
        tmp_path,
        {"supervised": 0.5, "unsupervised": 0.2, "rules": 0.25, "llm": 0.05},
    )

    rules_findings: List[Dict[str, Any]] = [
        {"severity": "HIGH"},
        {"severity": "LOW"},
    ]
    llm_certainties = [0.9, 0.7]

    result = aggregate_risk(
        supervised_prob=0.9,
        unsupervised_prob=0.4,
        rules_findings=rules_findings,
        llm_certainties=llm_certainties,
        config_path=cfg_path,
    )

    assert 0.0 <= result["unified_probability"] <= 1.0
    assert result["band"] in {"LOW", "MEDIUM", "HIGH"}

    # With a high supervised score and a HIGH rules severity, this should
    # typically land in the HIGH band with the default thresholds.
    assert result["band"] == "HIGH"

    breakdown = result["breakdown"]
    assert set(breakdown.keys()) == {"supervised", "unsupervised", "rules", "llm"}
    assert breakdown["supervised"]["probability"] == 0.9
    assert breakdown["rules"]["probability"] >= 0.8


def test_band_mapping(tmp_path: Path) -> None:
    cfg_path = _write_temp_config(
        tmp_path,
        {"supervised": 1.0, "unsupervised": 0.0, "rules": 0.0, "llm": 0.0},
    )

    # Low band
    r1 = aggregate_risk(0.1, 0.0, [], [], cfg_path)
    assert r1["band"] == "LOW"

    # Medium band
    r2 = aggregate_risk(0.4, 0.0, [], [], cfg_path)
    assert r2["band"] == "MEDIUM"

    # High band
    r3 = aggregate_risk(0.9, 0.0, [], [], cfg_path)
    assert r3["band"] == "HIGH"
