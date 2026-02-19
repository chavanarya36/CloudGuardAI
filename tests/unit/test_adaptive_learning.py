"""
Tests for the adaptive learning engine.
Validates all 7 subsystems: features, labels, drift, rule weights,
pattern discovery, model evaluation, telemetry, and the orchestrator.
"""
import json
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import MagicMock

import numpy as np
import pytest

# Ensure the api package is importable
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "api"))

from app.adaptive_learning import (
    AdaptiveLearningEngine,
    AdaptiveRuleWeights,
    DriftDetector,
    FeedbackLabelTransformer,
    LearningTelemetry,
    ModelEvaluator,
    PatternDiscoveryEngine,
    RichFeatureExtractor,
)


# -----------------------------------------------------------------------
# 1. RichFeatureExtractor
# -----------------------------------------------------------------------

class TestRichFeatureExtractor:

    def test_output_shape(self):
        vec = RichFeatureExtractor.extract("resource aws_s3_bucket {}", "main.tf")
        assert vec.shape == (40,)

    def test_detects_credentials(self):
        content = 'password = "hunter2"\nsecret = "abc"'
        vec = RichFeatureExtractor.extract(content, "bad.tf")
        # Credential signal indices: 5-12 (password @ 5, secret @ 6)
        assert vec[5] >= 1  # password
        assert vec[6] >= 1  # secret

    def test_detects_network_risk(self):
        content = 'cidr_blocks = ["0.0.0.0/0"]'
        vec = RichFeatureExtractor.extract(content, "sg.tf")
        # Network signals start at index 13; 0.0.0.0 is index 13
        assert vec[13] >= 1

    def test_empty_content_returns_near_zeros(self):
        vec = RichFeatureExtractor.extract("", "empty.tf")
        assert vec.shape == (40,)
        # Most features should be 0 or near-0 (structural features may have tiny values)
        assert np.sum(vec) < 1.0

    def test_k8s_manifest_detection(self):
        content = "apiVersion: v1\nkind: Pod"
        vec = RichFeatureExtractor.extract(content, "pod.yaml")
        assert vec[4] == 1.0  # apiVersion: flag


# -----------------------------------------------------------------------
# 2. FeedbackLabelTransformer
# -----------------------------------------------------------------------

class TestFeedbackLabelTransformer:
    t = FeedbackLabelTransformer()

    def test_false_positive_returns_safe(self):
        assert self.t.to_risk_label(None, "false_positive") == 0

    def test_false_negative_returns_risky(self):
        assert self.t.to_risk_label(None, "false_negative") == 1

    def test_accurate_returns_risky(self):
        assert self.t.to_risk_label(None, "accurate") == 1

    def test_is_correct_1_high_risk_returns_risky(self):
        assert self.t.to_risk_label(1, None, scan_risk_score=0.8) == 1

    def test_is_correct_0_high_risk_returns_safe(self):
        # Scanner flagged as risky but user says wrong → actually safe
        assert self.t.to_risk_label(0, None, scan_risk_score=0.8) == 0

    def test_is_correct_1_low_risk_returns_safe(self):
        # Scanner said safe, user confirms → safe
        assert self.t.to_risk_label(1, None, scan_risk_score=0.1) == 0

    def test_is_correct_0_low_risk_returns_risky(self):
        # Scanner said safe, user says wrong → actually risky
        assert self.t.to_risk_label(0, None, scan_risk_score=0.1) == 1

    def test_feedback_type_overrides_is_correct(self):
        # feedback_type takes priority
        assert self.t.to_risk_label(1, "false_positive", 0.9) == 0

    def test_no_info_defaults_risky(self):
        assert self.t.to_risk_label(None, None) == 1


# -----------------------------------------------------------------------
# 3. DriftDetector
# -----------------------------------------------------------------------

class TestDriftDetector:

    def test_no_drift_on_empty(self):
        dd = DriftDetector()
        result = dd.check()
        assert not result["drift_detected"]
        assert result["psi_score"] == 0.0

    def test_no_drift_on_stable_predictions(self):
        dd = DriftDetector(reference_window=50)
        rng = np.random.RandomState(42)
        for _ in range(100):
            dd.record_prediction(float(rng.uniform(0.3, 0.7)))
        result = dd.check()
        assert not result["drift_detected"]

    def test_drift_on_shifted_distribution(self):
        dd = DriftDetector(reference_window=50)
        # Fill reference with low-risk predictions
        for _ in range(60):
            dd.record_prediction(0.2)
        # Then shift to high-risk
        for _ in range(60):
            dd.record_prediction(0.9)
        result = dd.check(threshold=0.05)
        assert result["drift_detected"]
        assert result["psi_score"] > 0.05

    def test_reset_reference(self):
        dd = DriftDetector(reference_window=30)
        for _ in range(30):
            dd.record_prediction(0.5)
        dd.reset_reference()
        assert len(dd._reference) <= 30


# -----------------------------------------------------------------------
# 4. AdaptiveRuleWeights
# -----------------------------------------------------------------------

class TestAdaptiveRuleWeights:

    @pytest.fixture(autouse=True)
    def setup(self, tmp_path):
        self.arw = AdaptiveRuleWeights(str(tmp_path / "weights.json"))

    def test_default_weight_is_1(self):
        assert self.arw.get_weight("UNKNOWN_RULE") == 1.0

    def test_tp_raises_confidence(self):
        for _ in range(5):
            self.arw.record_feedback("RULE_001", "accurate")
        assert self.arw.get_weight("RULE_001") > 0.7

    def test_fp_lowers_confidence(self):
        for _ in range(10):
            self.arw.record_feedback("RULE_002", "false_positive")
        assert self.arw.get_weight("RULE_002") < 0.4

    def test_low_confidence_rules(self):
        for _ in range(10):
            self.arw.record_feedback("NOISY_RULE", "false_positive")
        low = self.arw.get_low_confidence_rules(threshold=0.4)
        assert "NOISY_RULE" in low

    def test_persistence(self, tmp_path):
        path = str(tmp_path / "weights2.json")
        arw1 = AdaptiveRuleWeights(path)
        arw1.record_feedback("R1", "accurate")
        # Reload
        arw2 = AdaptiveRuleWeights(path)
        assert arw2.get_weight("R1") == arw1.get_weight("R1")

    def test_stats_structure(self):
        self.arw.record_feedback("R1", "accurate")
        stats = self.arw.get_stats()
        assert "total_rules_tracked" in stats
        assert stats["total_rules_tracked"] == 1


# -----------------------------------------------------------------------
# 5. PatternDiscoveryEngine
# -----------------------------------------------------------------------

class TestPatternDiscoveryEngine:

    @pytest.fixture(autouse=True)
    def setup(self, tmp_path, monkeypatch):
        monkeypatch.setattr(PatternDiscoveryEngine, "RULES_DIR", tmp_path / "rules")
        self.engine = PatternDiscoveryEngine()
        self.engine._pattern_counts = {}
        monkeypatch.setattr(self.engine, "_state_path", lambda: tmp_path / "state.json")

    def test_ingest_findings_tracks_patterns(self):
        findings = [{"description": "S3 bucket is public", "severity": "HIGH", "rule_id": "R1"}]
        self.engine.ingest_findings(findings, scan_id=1)
        assert len(self.engine._pattern_counts) == 1

    def test_no_rules_before_threshold(self):
        findings = [{"description": "S3 bucket public access", "severity": "HIGH"}]
        self.engine.ingest_findings(findings, scan_id=1)
        result = self.engine.run_discovery_cycle()
        assert result["new_rules_generated"] == 0

    def test_rule_generated_after_threshold(self):
        findings = [{"description": "S3 bucket public access enabled", "severity": "HIGH"}]
        for i in range(5):
            self.engine.ingest_findings(findings, scan_id=i)
        result = self.engine.run_discovery_cycle()
        assert result["new_rules_generated"] >= 1

    def test_stats_structure(self):
        stats = self.engine.get_stats()
        assert "total_patterns_tracked" in stats
        assert "rules_generated" in stats


# -----------------------------------------------------------------------
# 6. ModelEvaluator
# -----------------------------------------------------------------------

class TestModelEvaluator:

    def test_insufficient_data(self):
        result = ModelEvaluator.evaluate(
            lambda x: np.ones(len(x)),
            lambda x: np.ones(len(x)),
            np.zeros((3, 5)),
            np.ones(3),
        )
        assert result["decision"] == "insufficient_data"

    def test_promote_better_challenger(self):
        y = np.array([1, 1, 1, 0, 0, 0, 1, 0, 1, 0, 1, 1])
        X = np.zeros((len(y), 5))
        result = ModelEvaluator.evaluate(
            champion_predict=lambda x: np.zeros(len(x)),   # always wrong
            challenger_predict=lambda x: y,                 # perfect
            X_holdout=X,
            y_holdout=y,
        )
        assert result["decision"] == "promote_challenger"

    def test_keep_champion_when_challenger_worse(self):
        y = np.array([1, 1, 1, 0, 0, 0, 1, 0, 1, 0, 1, 1])
        X = np.zeros((len(y), 5))
        result = ModelEvaluator.evaluate(
            champion_predict=lambda x: y,                  # perfect
            challenger_predict=lambda x: np.zeros(len(x)), # terrible
            X_holdout=X,
            y_holdout=y,
        )
        assert result["decision"] == "keep_champion"


# -----------------------------------------------------------------------
# 7. LearningTelemetry
# -----------------------------------------------------------------------

class TestLearningTelemetry:

    @pytest.fixture(autouse=True)
    def setup(self, tmp_path):
        self.tel = LearningTelemetry(str(tmp_path / "telemetry.json"))

    def test_log_and_retrieve(self):
        self.tel.log("test_event", {"key": "val"})
        recent = self.tel.get_recent(10)
        assert len(recent) == 1
        assert recent[0]["type"] == "test_event"

    def test_summary_counts(self):
        self.tel.log("scan", {})
        self.tel.log("scan", {})
        self.tel.log("feedback", {})
        summary = self.tel.get_summary()
        assert summary["total_events"] == 3
        assert summary["event_types"]["scan"] == 2


# -----------------------------------------------------------------------
# 8. AdaptiveLearningEngine (orchestrator)
# -----------------------------------------------------------------------

class TestAdaptiveLearningEngine:

    def test_instantiates(self):
        engine = AdaptiveLearningEngine()
        assert engine.telemetry is not None
        assert engine.drift_detector is not None

    def test_on_scan_completed_records(self):
        engine = AdaptiveLearningEngine()
        findings = [{"description": "test", "severity": "HIGH", "rule_id": "R1"}]
        engine.on_scan_completed(1, findings, 0.6)
        assert engine.drift_detector._recent[-1] == 0.6

    def test_on_feedback_fills_buffer(self):
        engine = AdaptiveLearningEngine()
        engine.on_feedback_received(
            scan_id=1, file_content='password = "x"', filename="bad.tf",
            is_correct=1, feedback_type=None, scan_risk_score=0.8,
        )
        assert len(engine._training_buffer_X) == 1
        assert engine._training_buffer_y[0] == 1

    def test_auto_retrain_threshold(self):
        engine = AdaptiveLearningEngine()
        engine.AUTO_RETRAIN_FEEDBACK_THRESHOLD = 3
        for i in range(3):
            engine.on_feedback_received(
                scan_id=i, file_content="test", filename="t.tf",
                is_correct=1, feedback_type=None, scan_risk_score=0.5,
            )
        should, reason = engine.should_auto_retrain()
        assert should
        assert "feedback_threshold" in reason

    def test_learning_status_structure(self):
        engine = AdaptiveLearningEngine()
        status = engine.get_learning_status()
        assert status["adaptive_learning_active"] is True
        assert "drift" in status
        assert "pattern_discovery" in status
        assert "rule_weights" in status
        assert "telemetry_summary" in status

    def test_on_retrain_resets_buffer(self):
        engine = AdaptiveLearningEngine()
        engine._training_buffer_X.append(np.zeros(40))
        engine._training_buffer_y.append(1)
        engine._feedback_count_since_retrain = 5
        engine.on_retrain_completed({"accuracy": 0.9})
        assert len(engine._training_buffer_X) == 0
        assert engine._feedback_count_since_retrain == 0

    def test_get_training_batch(self):
        engine = AdaptiveLearningEngine()
        engine._training_buffer_X.append(np.ones(40))
        engine._training_buffer_y.append(1)
        X, y = engine.get_training_batch()
        assert X.shape == (1, 40)
        assert y.shape == (1,)
