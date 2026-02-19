"""
Prometheus metrics for CloudGuard AI API.

Exposes a /metrics endpoint compatible with Prometheus scraping.
Tracks request counts, latencies, scan statistics, and model metrics.
"""

import logging
import time
from collections import defaultdict
from typing import Optional

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)


class MetricsCollector:
    """Lightweight Prometheus-compatible metrics collector (no external deps)."""

    def __init__(self):
        # Counters
        self.request_count: dict[str, int] = defaultdict(int)  # method:path:status
        self.scan_count: int = 0
        self.scan_errors: int = 0
        self.feedback_count: int = 0
        self.retrain_count: int = 0

        # Histograms (simplified — store sum + count)
        self._request_duration_sum: dict[str, float] = defaultdict(float)
        self._request_duration_count: dict[str, int] = defaultdict(int)

        # Gauges
        self.active_scans: int = 0
        self.model_accuracy: float = 0.0
        self.model_f1: float = 0.0
        self.drift_psi: float = 0.0
        self.learning_buffer_size: int = 0
        self.discovered_patterns: int = 0

    def record_request(self, method: str, path: str, status: int, duration: float):
        """Record an HTTP request."""
        # Normalize path (replace IDs with :id)
        normalized = self._normalize_path(path)
        key = f'{method}:{normalized}:{status}'
        self.request_count[key] += 1
        self._request_duration_sum[f'{method}:{normalized}'] += duration
        self._request_duration_count[f'{method}:{normalized}'] += 1

    def record_scan(self, success: bool = True):
        self.scan_count += 1
        if not success:
            self.scan_errors += 1

    def record_feedback(self):
        self.feedback_count += 1

    def record_retrain(self):
        self.retrain_count += 1

    def _normalize_path(self, path: str) -> str:
        """Replace numeric path segments with :id."""
        parts = path.strip("/").split("/")
        normalized = []
        for part in parts:
            if part.isdigit():
                normalized.append(":id")
            else:
                normalized.append(part)
        return "/" + "/".join(normalized) if normalized else "/"

    def render_prometheus(self) -> str:
        """Render all metrics in Prometheus exposition format."""
        lines = []

        # Request counters
        lines.append("# HELP cloudguard_http_requests_total Total HTTP requests")
        lines.append("# TYPE cloudguard_http_requests_total counter")
        for key, count in sorted(self.request_count.items()):
            method, path, status = key.rsplit(":", 2)
            lines.append(
                f'cloudguard_http_requests_total{{method="{method}",path="{path}",status="{status}"}} {count}'
            )

        # Request duration
        lines.append("# HELP cloudguard_http_request_duration_seconds HTTP request duration")
        lines.append("# TYPE cloudguard_http_request_duration_seconds summary")
        for key in sorted(self._request_duration_sum):
            method, path = key.split(":", 1)
            total = self._request_duration_sum[key]
            count = self._request_duration_count[key]
            avg = total / count if count > 0 else 0
            lines.append(
                f'cloudguard_http_request_duration_seconds_sum{{method="{method}",path="{path}"}} {total:.4f}'
            )
            lines.append(
                f'cloudguard_http_request_duration_seconds_count{{method="{method}",path="{path}"}} {count}'
            )

        # Scan metrics
        lines.append("# HELP cloudguard_scans_total Total scans performed")
        lines.append("# TYPE cloudguard_scans_total counter")
        lines.append(f"cloudguard_scans_total {self.scan_count}")

        lines.append("# HELP cloudguard_scan_errors_total Total scan errors")
        lines.append("# TYPE cloudguard_scan_errors_total counter")
        lines.append(f"cloudguard_scan_errors_total {self.scan_errors}")

        # Feedback
        lines.append("# HELP cloudguard_feedback_total Total feedback submissions")
        lines.append("# TYPE cloudguard_feedback_total counter")
        lines.append(f"cloudguard_feedback_total {self.feedback_count}")

        # Retrain
        lines.append("# HELP cloudguard_retrain_total Total model retrains")
        lines.append("# TYPE cloudguard_retrain_total counter")
        lines.append(f"cloudguard_retrain_total {self.retrain_count}")

        # Gauges
        lines.append("# HELP cloudguard_active_scans Currently active scans")
        lines.append("# TYPE cloudguard_active_scans gauge")
        lines.append(f"cloudguard_active_scans {self.active_scans}")

        lines.append("# HELP cloudguard_model_accuracy Current model accuracy")
        lines.append("# TYPE cloudguard_model_accuracy gauge")
        lines.append(f"cloudguard_model_accuracy {self.model_accuracy:.4f}")

        lines.append("# HELP cloudguard_model_f1 Current model F1 score")
        lines.append("# TYPE cloudguard_model_f1 gauge")
        lines.append(f"cloudguard_model_f1 {self.model_f1:.4f}")

        lines.append("# HELP cloudguard_drift_psi Current drift PSI score")
        lines.append("# TYPE cloudguard_drift_psi gauge")
        lines.append(f"cloudguard_drift_psi {self.drift_psi:.6f}")

        lines.append("# HELP cloudguard_learning_buffer_size Training buffer size")
        lines.append("# TYPE cloudguard_learning_buffer_size gauge")
        lines.append(f"cloudguard_learning_buffer_size {self.learning_buffer_size}")

        lines.append("# HELP cloudguard_discovered_patterns Discovered vulnerability patterns")
        lines.append("# TYPE cloudguard_discovered_patterns gauge")
        lines.append(f"cloudguard_discovered_patterns {self.discovered_patterns}")

        return "\n".join(lines) + "\n"


# Singleton
metrics = MetricsCollector()


class MetricsMiddleware(BaseHTTPMiddleware):
    """Middleware that records request metrics."""

    async def dispatch(self, request: Request, call_next):
        start = time.monotonic()
        response = await call_next(request)
        duration = time.monotonic() - start
        metrics.record_request(request.method, request.url.path, response.status_code, duration)
        return response
