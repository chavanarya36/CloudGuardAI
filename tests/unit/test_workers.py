"""
Unit tests for scan_worker and retrain_worker.

All external dependencies (DB, HTTP calls) are mocked so these tests run
in isolation without a live database or ML service.
"""
from __future__ import annotations

import sys
from pathlib import Path
from datetime import datetime
from unittest.mock import MagicMock, patch, PropertyMock

import pytest

# Ensure api/ is importable
api_dir = Path(__file__).parent.parent.parent / "api"
sys.path.insert(0, str(api_dir))

from app.models import Scan, Finding, Feedback, ModelVersion, ScanStatus


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _make_scan(scan_id: int = 1, filename: str = "main.tf", content: str = "resource {}") -> MagicMock:
    """Create a mock Scan ORM object."""
    scan = MagicMock(spec=Scan)
    scan.id = scan_id
    scan.filename = filename
    scan.file_content = content
    scan.status = ScanStatus.PENDING
    scan.error_message = None
    scan.completed_at = None
    scan.unified_risk_score = None
    scan.ml_score = None
    scan.rules_score = None
    scan.llm_score = None
    scan.risk_score = 0.7  # needed by FeedbackLabelTransformer
    return scan


def _make_feedback(fb_id: int, is_correct: bool, severity: str = "HIGH") -> MagicMock:
    """Create a mock Feedback ORM object."""
    fb = MagicMock(spec=Feedback)
    fb.id = fb_id
    fb.is_correct = is_correct
    fb.adjusted_severity = MagicMock()
    fb.adjusted_severity.value = severity
    fb.scan = _make_scan(scan_id=fb_id)
    return fb


# ===========================================================================
# scan_worker tests
# ===========================================================================

class TestScanWorker:
    """Tests for api/app/workers/scan_worker.py → process_scan()"""

    @patch("app.workers.scan_worker.SessionLocal")
    @patch("app.workers.scan_worker.httpx.Client")
    def test_successful_scan(self, mock_httpx_cls, mock_session_local):
        """process_scan happy-path: ML service returns results, findings stored."""
        from app.workers.scan_worker import process_scan

        # --- DB mock ---
        db = MagicMock()
        mock_session_local.return_value = db
        scan = _make_scan()
        db.query.return_value.filter.return_value.first.return_value = scan

        # --- HTTP mock ---
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "unified_risk_score": 0.85,
            "ml_score": 0.7,
            "rules_score": 0.9,
            "llm_score": 0.6,
            "findings": [
                {
                    "rule_id": "OPEN_SG",
                    "severity": "HIGH",
                    "title": "Open security group",
                    "description": "0.0.0.0/0 ingress",
                    "file_path": "main.tf",
                    "line_number": 5,
                    "code_snippet": "cidr = 0.0.0.0/0",
                    "resource": "aws_security_group",
                    "llm_explanation": "This allows all traffic",
                    "llm_remediation": "Restrict CIDR",
                    "certainty": 0.9,
                    "metadata": {},
                },
            ],
        }
        mock_client = MagicMock()
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client.post.return_value = mock_response
        mock_httpx_cls.return_value = mock_client

        result = process_scan(1)

        assert result["status"] == "completed"
        assert result["scan_id"] == 1
        assert scan.status == ScanStatus.COMPLETED
        assert scan.unified_risk_score == 0.85
        assert db.add.call_count == 1  # one finding added
        assert db.commit.call_count >= 2  # status update + findings

    @patch("app.workers.scan_worker.SessionLocal")
    def test_scan_not_found(self, mock_session_local):
        """process_scan returns error when scan id doesn't exist."""
        from app.workers.scan_worker import process_scan

        db = MagicMock()
        mock_session_local.return_value = db
        db.query.return_value.filter.return_value.first.return_value = None

        result = process_scan(999)

        assert "error" in result
        assert "not found" in result["error"].lower()

    @patch("app.workers.scan_worker.SessionLocal")
    @patch("app.workers.scan_worker.httpx.Client")
    def test_ml_service_failure_marks_scan_failed(self, mock_httpx_cls, mock_session_local):
        """When ML service call raises, scan status becomes FAILED."""
        from app.workers.scan_worker import process_scan

        db = MagicMock()
        mock_session_local.return_value = db
        scan = _make_scan()
        db.query.return_value.filter.return_value.first.return_value = scan

        mock_client = MagicMock()
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client.post.side_effect = Exception("ML service unreachable")
        mock_httpx_cls.return_value = mock_client

        result = process_scan(1)

        assert result["status"] == "failed"
        assert "ML service unreachable" in result["error"]
        assert scan.status == ScanStatus.FAILED
        assert scan.error_message is not None

    @patch("app.workers.scan_worker.SessionLocal")
    @patch("app.workers.scan_worker.httpx.Client")
    def test_empty_findings_still_completes(self, mock_httpx_cls, mock_session_local):
        """process_scan completes even when ML service returns zero findings."""
        from app.workers.scan_worker import process_scan

        db = MagicMock()
        mock_session_local.return_value = db
        scan = _make_scan()
        db.query.return_value.filter.return_value.first.return_value = scan

        mock_response = MagicMock()
        mock_response.json.return_value = {
            "unified_risk_score": 0.1,
            "ml_score": 0.1,
            "rules_score": 0.0,
            "llm_score": 0.0,
            "findings": [],
        }
        mock_client = MagicMock()
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client.post.return_value = mock_response
        mock_httpx_cls.return_value = mock_client

        result = process_scan(1)

        assert result["status"] == "completed"
        assert scan.status == ScanStatus.COMPLETED
        assert db.add.call_count == 0  # no findings

    @patch("app.workers.scan_worker.SessionLocal")
    @patch("app.workers.scan_worker.httpx.Client")
    def test_db_session_closed_on_success(self, mock_httpx_cls, mock_session_local):
        """DB session is always closed, even on success."""
        from app.workers.scan_worker import process_scan

        db = MagicMock()
        mock_session_local.return_value = db
        scan = _make_scan()
        db.query.return_value.filter.return_value.first.return_value = scan

        mock_response = MagicMock()
        mock_response.json.return_value = {
            "unified_risk_score": 0.5,
            "findings": [],
        }
        mock_client = MagicMock()
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client.post.return_value = mock_response
        mock_httpx_cls.return_value = mock_client

        process_scan(1)
        db.close.assert_called_once()

    @patch("app.workers.scan_worker.SessionLocal")
    @patch("app.workers.scan_worker.httpx.Client")
    def test_db_session_closed_on_failure(self, mock_httpx_cls, mock_session_local):
        """DB session is always closed, even on error."""
        from app.workers.scan_worker import process_scan

        db = MagicMock()
        mock_session_local.return_value = db
        scan = _make_scan()
        db.query.return_value.filter.return_value.first.return_value = scan

        mock_client = MagicMock()
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client.post.side_effect = RuntimeError("boom")
        mock_httpx_cls.return_value = mock_client

        process_scan(1)
        db.close.assert_called_once()

    @patch("app.workers.scan_worker.SessionLocal")
    @patch("app.workers.scan_worker.httpx.Client")
    def test_status_set_processing_before_ml_call(self, mock_httpx_cls, mock_session_local):
        """Scan status transitions to PROCESSING before calling ML."""
        from app.workers.scan_worker import process_scan

        db = MagicMock()
        mock_session_local.return_value = db
        scan = _make_scan()
        db.query.return_value.filter.return_value.first.return_value = scan

        statuses_seen = []

        def track_commit():
            statuses_seen.append(scan.status)

        db.commit.side_effect = track_commit

        mock_response = MagicMock()
        mock_response.json.return_value = {"unified_risk_score": 0.5, "findings": []}
        mock_client = MagicMock()
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client.post.return_value = mock_response
        mock_httpx_cls.return_value = mock_client

        process_scan(1)

        # First commit sets PROCESSING, second sets COMPLETED
        assert ScanStatus.PROCESSING in statuses_seen


# ===========================================================================
# retrain_worker tests
# ===========================================================================

class TestRetrainWorker:
    """Tests for api/app/workers/retrain_worker.py → retrain_model()"""

    @patch("app.workers.retrain_worker.SessionLocal")
    def test_skips_when_no_feedback(self, mock_session_local):
        """retrain_model skips gracefully when no feedback data exists."""
        from app.workers.retrain_worker import retrain_model

        db = MagicMock()
        mock_session_local.return_value = db
        db.query.return_value.filter.return_value.all.return_value = []

        result = retrain_model()

        assert result["status"] == "skipped"
        assert "No feedback" in result["reason"]

    @patch("app.workers.retrain_worker.SessionLocal")
    @patch("app.workers.retrain_worker.httpx.Client")
    def test_successful_retrain(self, mock_httpx_cls, mock_session_local):
        """retrain_model happy-path: calls ML service, creates model version."""
        from app.workers.retrain_worker import retrain_model

        db = MagicMock()
        mock_session_local.return_value = db

        # Return 2 feedback items
        fb1 = _make_feedback(1, True, "HIGH")
        fb2 = _make_feedback(2, False, "LOW")
        db.query.return_value.filter.return_value.all.return_value = [fb1, fb2]

        # Mock the update() call for deactivating old models
        db.query.return_value.update = MagicMock()

        mock_response = MagicMock()
        mock_response.json.return_value = {
            "accuracy": 0.92,
            "precision": 0.88,
            "recall": 0.85,
            "f1_score": 0.86,
            "metadata": {"iterations": 50},
        }
        mock_client = MagicMock()
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client.post.return_value = mock_response
        mock_httpx_cls.return_value = mock_client

        result = retrain_model()

        assert result["status"] == "completed"
        assert result["samples"] == 2
        assert result["metrics"]["accuracy"] == 0.92
        assert result["metrics"]["f1_score"] == 0.86
        # Model version was added
        db.add.assert_called_once()

    @patch("app.workers.retrain_worker.SessionLocal")
    @patch("app.workers.retrain_worker.httpx.Client")
    def test_ml_service_failure(self, mock_httpx_cls, mock_session_local):
        """retrain_model fails gracefully when ML service errors."""
        from app.workers.retrain_worker import retrain_model

        db = MagicMock()
        mock_session_local.return_value = db
        db.query.return_value.filter.return_value.all.return_value = [
            _make_feedback(1, True),
        ]

        mock_client = MagicMock()
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client.post.side_effect = Exception("timeout")
        mock_httpx_cls.return_value = mock_client

        result = retrain_model()

        assert result["status"] == "failed"
        assert "timeout" in result["error"]

    @patch("app.workers.retrain_worker.SessionLocal")
    @patch("app.workers.retrain_worker.httpx.Client")
    def test_old_models_deactivated(self, mock_httpx_cls, mock_session_local):
        """retrain_model deactivates previous model versions."""
        from app.workers.retrain_worker import retrain_model

        db = MagicMock()
        mock_session_local.return_value = db

        fb = _make_feedback(1, True)
        db.query.return_value.filter.return_value.all.return_value = [fb]
        db.query.return_value.update = MagicMock()

        mock_response = MagicMock()
        mock_response.json.return_value = {
            "accuracy": 0.9,
            "precision": 0.9,
            "recall": 0.9,
            "f1_score": 0.9,
            "metadata": {},
        }
        mock_client = MagicMock()
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client.post.return_value = mock_response
        mock_httpx_cls.return_value = mock_client

        retrain_model()

        # Verify old models were deactivated via update()
        db.query.return_value.update.assert_called_with({"is_active": 0})

    @patch("app.workers.retrain_worker.SessionLocal")
    @patch("app.workers.retrain_worker.httpx.Client")
    def test_db_session_closed_on_success(self, mock_httpx_cls, mock_session_local):
        """DB session always closed after retrain succeeds."""
        from app.workers.retrain_worker import retrain_model

        db = MagicMock()
        mock_session_local.return_value = db
        db.query.return_value.filter.return_value.all.return_value = []

        retrain_model()
        db.close.assert_called_once()

    @patch("app.workers.retrain_worker.SessionLocal")
    @patch("app.workers.retrain_worker.httpx.Client")
    def test_db_session_closed_on_failure(self, mock_httpx_cls, mock_session_local):
        """DB session always closed after retrain fails."""
        from app.workers.retrain_worker import retrain_model

        db = MagicMock()
        mock_session_local.return_value = db
        db.query.return_value.filter.return_value.all.return_value = [
            _make_feedback(1, True),
        ]

        mock_client = MagicMock()
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client.post.side_effect = RuntimeError("crash")
        mock_httpx_cls.return_value = mock_client

        retrain_model()
        db.close.assert_called_once()
