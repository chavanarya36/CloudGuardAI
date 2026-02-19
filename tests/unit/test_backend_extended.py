"""
Extended adaptive learning, utils, and schemas edge-case tests.
Pushes remaining backend areas from ~70% to 80%+.
"""
import pytest
import json
import time
from unittest.mock import patch, MagicMock
from pathlib import Path


# ═══════════════════════════════════════════════════════════════════════════
# Adaptive Learning — edge cases in subsystems
# ═══════════════════════════════════════════════════════════════════════════
class TestAdaptiveLearningEdgeCases:
    """Edge cases in adaptive_learning.py subsystems."""

    def test_drift_detector_identical_dists(self):
        from app.adaptive_learning import DriftDetector
        detector = DriftDetector(reference_window=50)
        # Feed identical predictions → PSI should be ~0
        for _ in range(100):
            detector.record_prediction(0.5)
        psi = detector.compute_psi()
        assert psi < 0.01  # practically zero drift

    def test_drift_detector_check_no_drift(self):
        from app.adaptive_learning import DriftDetector
        detector = DriftDetector(reference_window=50)
        for _ in range(60):
            detector.record_prediction(0.5)
        result = detector.check(threshold=0.15)
        assert result["drift_detected"] is False
        assert result["action"] == "normal"

    def test_drift_detector_insufficient_data(self):
        from app.adaptive_learning import DriftDetector
        detector = DriftDetector(reference_window=200)
        for _ in range(10):
            detector.record_prediction(0.5)
        psi = detector.compute_psi()
        assert psi == 0.0  # not enough data

    def test_drift_detector_reset_reference(self):
        from app.adaptive_learning import DriftDetector
        detector = DriftDetector(reference_window=50)
        for _ in range(60):
            detector.record_prediction(0.5)
        detector.reset_reference()
        assert len(detector._reference) > 0

    def test_pattern_discovery_signature(self):
        from app.adaptive_learning import PatternDiscoveryEngine
        engine = PatternDiscoveryEngine()
        sig = engine._signature({"description": "public bucket access", "severity": "HIGH"})
        assert isinstance(sig, str)
        assert len(sig) == 12  # MD5 hex[:12]

    def test_pattern_discovery_same_finding_same_sig(self):
        from app.adaptive_learning import PatternDiscoveryEngine
        engine = PatternDiscoveryEngine()
        f = {"description": "public bucket", "severity": "HIGH"}
        sig1 = engine._signature(f)
        sig2 = engine._signature(f)
        assert sig1 == sig2

    def test_model_evaluator_equal_models(self):
        from app.adaptive_learning import ModelEvaluator
        import numpy as np
        # Both models predict the same thing → keep champion
        X = np.random.randn(20, 5)
        y = np.array([0]*10 + [1]*10)
        pred = lambda x: y  # both predict exactly y
        result = ModelEvaluator.evaluate(pred, pred, X, y)
        assert result["decision"] == "keep_champion"
        assert result["improvement"] == 0.0

    def test_model_evaluator_insufficient_data(self):
        from app.adaptive_learning import ModelEvaluator
        import numpy as np
        X = np.random.randn(5, 3)
        y = np.array([0, 1, 0, 1, 0])
        pred = lambda x: y
        result = ModelEvaluator.evaluate(pred, pred, X, y)
        assert result["decision"] == "insufficient_data"

    def test_telemetry_log_and_retrieve(self):
        from app.adaptive_learning import LearningTelemetry
        import tempfile
        tel = LearningTelemetry(path=tempfile.mktemp(suffix=".json"))
        tel.log("test_event", {"key": "value"})
        recent = tel.get_recent(10)
        assert len(recent) >= 1
        assert recent[-1]["type"] == "test_event"

    def test_telemetry_summary(self):
        from app.adaptive_learning import LearningTelemetry
        import tempfile
        tel = LearningTelemetry(path=tempfile.mktemp(suffix=".json"))
        tel.log("a", {})
        tel.log("b", {})
        tel.log("a", {})
        summary = tel.get_summary()
        assert summary["total_events"] == 3
        assert summary["event_types"]["a"] == 2

    def test_adaptive_learning_engine_init(self):
        from app.adaptive_learning import AdaptiveLearningEngine
        engine = AdaptiveLearningEngine()
        assert hasattr(engine, "drift_detector")
        assert hasattr(engine, "pattern_engine")
        assert hasattr(engine, "telemetry")
        assert hasattr(engine, "rule_weights")

    def test_engine_should_auto_retrain_false(self):
        from app.adaptive_learning import AdaptiveLearningEngine
        engine = AdaptiveLearningEngine()
        should, reason = engine.should_auto_retrain()
        assert should is False
        assert reason == "not_needed"

    def test_engine_get_training_batch_empty(self):
        from app.adaptive_learning import AdaptiveLearningEngine
        import numpy as np
        engine = AdaptiveLearningEngine()
        X, y = engine.get_training_batch()
        assert len(X) == 0
        assert len(y) == 0

    def test_engine_get_learning_status(self):
        from app.adaptive_learning import AdaptiveLearningEngine
        engine = AdaptiveLearningEngine()
        status = engine.get_learning_status()
        assert status["adaptive_learning_active"] is True
        assert "training_buffer_size" in status
        assert "drift" in status

    def test_adaptive_rule_weights_record(self):
        from app.adaptive_learning import AdaptiveRuleWeights
        weights = AdaptiveRuleWeights()
        weights.record_feedback("R1", "accurate")
        weights.record_feedback("R1", "false_positive")
        stats = weights.get_stats()
        assert isinstance(stats, dict)

    def test_rich_feature_extractor(self):
        from app.adaptive_learning import RichFeatureExtractor
        ext = RichFeatureExtractor()
        features = ext.extract("resource { acl = public }", "main.tf")
        assert len(features) == 40


# ═══════════════════════════════════════════════════════════════════════════
# Utils / Cache — edge-case paths
# ═══════════════════════════════════════════════════════════════════════════
class TestUtilsCacheEdgeCases:
    """Edge cases in utils.py cache and decorators."""

    def test_cache_hit_and_miss(self):
        from app.utils import InMemoryCache
        cache = InMemoryCache()
        cache.set("key1", "val1", ttl_seconds=300)
        assert cache.get("key1") == "val1"
        assert cache.get("nonexistent") is None

    def test_cache_expiration(self):
        from app.utils import InMemoryCache
        cache = InMemoryCache()
        cache.set("k", "v", ttl_seconds=0)
        time.sleep(0.05)
        assert cache.get("k") is None  # expired

    def test_cache_clear(self):
        from app.utils import InMemoryCache
        cache = InMemoryCache()
        cache.set("a", 1)
        cache.set("b", 2)
        cache.clear()
        assert cache.get("a") is None
        assert cache.get("b") is None

    def test_cache_invalidate(self):
        from app.utils import InMemoryCache
        cache = InMemoryCache()
        cache.set("key", "value")
        cache.invalidate("key")
        assert cache.get("key") is None

    def test_cache_stats(self):
        from app.utils import InMemoryCache
        cache = InMemoryCache()
        cache.set("k", "v", ttl_seconds=300)
        stats = cache.stats()
        assert stats["total_entries"] >= 1
        assert stats["active_entries"] >= 1

    def test_file_cache_set_and_get(self):
        from app.utils import FileCache
        import tempfile, shutil
        tmpdir = tempfile.mkdtemp()
        fc = FileCache(cache_dir=tmpdir)
        fc.set("test_key", {"data": 42})
        result = fc.get("test_key")
        assert result == {"data": 42}
        shutil.rmtree(tmpdir)

    def test_file_cache_missing_key(self):
        from app.utils import FileCache
        import tempfile, shutil
        tmpdir = tempfile.mkdtemp()
        fc = FileCache(cache_dir=tmpdir)
        assert fc.get("nonexistent") is None
        shutil.rmtree(tmpdir)

    def test_file_cache_invalidate(self):
        from app.utils import FileCache
        import tempfile, shutil
        tmpdir = tempfile.mkdtemp()
        fc = FileCache(cache_dir=tmpdir)
        fc.set("k", "v")
        fc.invalidate("k")
        assert fc.get("k") is None
        shutil.rmtree(tmpdir)

    def test_retry_decorator_success(self):
        from app.utils import retry

        @retry(max_attempts=3, delay_seconds=0.01)
        def always_works():
            return "ok"

        assert always_works() == "ok"

    def test_retry_decorator_eventual_success(self):
        from app.utils import retry
        call_count = {"n": 0}

        @retry(max_attempts=3, delay_seconds=0.01)
        def fails_twice():
            call_count["n"] += 1
            if call_count["n"] < 3:
                raise ValueError("not yet")
            return "success"

        result = fails_twice()
        assert result == "success"
        assert call_count["n"] == 3

    def test_cached_decorator(self):
        from app.utils import cached
        call_count = {"n": 0}

        @cached(ttl=300, key_prefix="test")
        def expensive():
            call_count["n"] += 1
            return "result"

        r1 = expensive()
        r2 = expensive()
        assert r1 == "result"
        assert r2 == "result"
        assert call_count["n"] == 1  # second call was cached

    def test_timed_decorator(self):
        from app.utils import timed

        @timed("test_op")
        def fast_func():
            return 42

        assert fast_func() == 42

    def test_memoize_to_file(self):
        from app.utils import memoize_to_file
        import tempfile, os
        tmpfile = tempfile.mktemp(suffix=".json")

        @memoize_to_file(tmpfile)
        def compute():
            return {"answer": 42}

        r1 = compute()
        assert r1 == {"answer": 42}
        assert Path(tmpfile).exists()

        # Second call should read from file
        r2 = compute()
        assert r2 == {"answer": 42}
        os.unlink(tmpfile)


# ═══════════════════════════════════════════════════════════════════════════
# Schemas (api/app/schemas.py) — enum and model basics
# ═══════════════════════════════════════════════════════════════════════════
class TestAPISchemas:
    """Test API Pydantic models basic validation."""

    def test_severity_enum_uppercase(self):
        from app.schemas import SeverityEnum
        assert SeverityEnum("HIGH") == SeverityEnum.HIGH
        assert SeverityEnum("CRITICAL") == SeverityEnum.CRITICAL

    def test_severity_enum_lowercase(self):
        from app.schemas import SeverityEnum
        assert SeverityEnum("high") == SeverityEnum.HIGH
        assert SeverityEnum("critical") == SeverityEnum.CRITICAL

    def test_scan_status_enum(self):
        from app.schemas import ScanStatusEnum
        assert ScanStatusEnum.PENDING.value == "pending"
        assert ScanStatusEnum.COMPLETED.value == "completed"

    def test_scan_create_schema(self):
        from app.schemas import ScanCreate
        req = ScanCreate(filename="test.tf", file_content="content")
        assert req.filename == "test.tf"

    def test_finding_response_schema(self):
        from app.schemas import FindingResponse
        fr = FindingResponse(
            id=1, rule_id="R1", severity="HIGH",
            title="Test", description="desc"
        )
        assert fr.severity == "HIGH"

    def test_feedback_create_schema(self):
        from app.schemas import FeedbackCreate
        fb = FeedbackCreate(scan_id=1, is_correct=1, feedback_type="accurate")
        assert fb.scan_id == 1
        assert fb.is_correct == 1

    def test_scan_response_schema(self):
        from app.schemas import ScanResponse, ScanStatusEnum
        from datetime import datetime
        resp = ScanResponse(
            id=1, filename="test.tf",
            status=ScanStatusEnum.COMPLETED,
            created_at=datetime.now(),
            unified_risk_score=0.75,
            findings=[]
        )
        assert resp.unified_risk_score == 0.75


# ═══════════════════════════════════════════════════════════════════════════
# Database — model creation
# ═══════════════════════════════════════════════════════════════════════════
class TestDatabaseModels:
    """Test database model instantiation."""

    def test_scan_model_creation(self):
        from app.models import Scan, ScanStatus
        scan = Scan(
            filename="test.tf",
            file_content="content",
            status=ScanStatus.PENDING
        )
        assert scan.filename == "test.tf"
        assert scan.status == ScanStatus.PENDING

    def test_finding_model_creation(self):
        from app.models import Finding
        finding = Finding(
            scan_id=1,
            rule_id="R1",
            severity="HIGH",
            title="Test finding",
            description="desc"
        )
        assert finding.severity == "HIGH"

    def test_scan_status_enum_values(self):
        from app.models import ScanStatus
        assert ScanStatus.PENDING is not None
        assert ScanStatus.COMPLETED is not None
        assert ScanStatus.FAILED is not None
