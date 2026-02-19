"""
Tests for auth module — JWT creation/verification and API key management.
"""
import time
import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient


class TestJWT:
    """Test JWT token creation and verification."""

    def test_create_and_verify_jwt(self):
        from app.auth import create_jwt, verify_jwt
        token = create_jwt("test_user", scopes=["read", "write"], expires_minutes=5)
        payload = verify_jwt(token)
        assert payload.sub == "test_user"
        assert "read" in payload.scopes
        assert "write" in payload.scopes

    def test_expired_jwt_rejected(self):
        from app.auth import create_jwt, verify_jwt
        token = create_jwt("user", expires_minutes=-1)
        with pytest.raises(ValueError, match="expired"):
            verify_jwt(token)

    def test_tampered_jwt_rejected(self):
        from app.auth import create_jwt, verify_jwt
        token = create_jwt("user")
        tampered = token[:-5] + "XXXXX"
        with pytest.raises(ValueError):
            verify_jwt(tampered)

    def test_invalid_format_rejected(self):
        from app.auth import verify_jwt
        with pytest.raises(ValueError, match="Invalid token"):
            verify_jwt("not.a.valid.token.at.all")


class TestAPIKey:
    """Test API key generation and validation."""

    def test_generate_api_key(self):
        from app.auth import generate_api_key, _is_valid_api_key
        key = generate_api_key()
        assert key.startswith("cg_")
        assert _is_valid_api_key(key)

    def test_invalid_api_key_rejected(self):
        from app.auth import _is_valid_api_key
        assert not _is_valid_api_key("invalid_key_12345")


class TestRateLimiter:
    """Test rate limiting token bucket."""

    def test_token_bucket_allows_within_limit(self):
        from app.rate_limiter import TokenBucket
        bucket = TokenBucket(rate=10.0, capacity=5)
        for _ in range(5):
            assert bucket.consume()

    def test_token_bucket_rejects_over_limit(self):
        from app.rate_limiter import TokenBucket
        bucket = TokenBucket(rate=0.1, capacity=2)
        assert bucket.consume()
        assert bucket.consume()
        assert not bucket.consume()

    def test_token_bucket_refills(self):
        from app.rate_limiter import TokenBucket
        bucket = TokenBucket(rate=100.0, capacity=5)
        for _ in range(5):
            bucket.consume()
        import time
        time.sleep(0.1)  # 0.1s * 100 tokens/s = 10 tokens refilled
        assert bucket.consume()

    def test_rate_limit_store_per_client(self):
        from app.rate_limiter import RateLimitStore
        store = RateLimitStore(rate=1.0, capacity=2)
        allowed_a, _ = store.check("client_a")
        allowed_b, _ = store.check("client_b")
        assert allowed_a
        assert allowed_b


class TestMetrics:
    """Test Prometheus metrics collector."""

    def test_record_request(self):
        from app.metrics import MetricsCollector
        m = MetricsCollector()
        m.record_request("GET", "/health", 200, 0.005)
        assert m.request_count["GET:/health:200"] == 1

    def test_record_scan(self):
        from app.metrics import MetricsCollector
        m = MetricsCollector()
        m.record_scan(success=True)
        m.record_scan(success=False)
        assert m.scan_count == 2
        assert m.scan_errors == 1

    def test_render_prometheus(self):
        from app.metrics import MetricsCollector
        m = MetricsCollector()
        m.record_request("POST", "/scan", 200, 1.5)
        m.record_scan()
        output = m.render_prometheus()
        assert "cloudguard_http_requests_total" in output
        assert "cloudguard_scans_total 1" in output
        assert "cloudguard_http_request_duration_seconds" in output

    def test_normalize_path_replaces_ids(self):
        from app.metrics import MetricsCollector
        m = MetricsCollector()
        assert m._normalize_path("/scan/123") == "/scan/:id"
        assert m._normalize_path("/scans/456/findings") == "/scans/:id/findings"


class TestCVEScanner:
    """Test CVE scanner with local database."""

    def test_scan_package_json_finds_vulns(self):
        from scanners.cve_scanner import CVEScanner
        scanner = CVEScanner(use_osv=False)
        content = '{"dependencies": {"lodash": "4.17.4", "axios": "0.18.0"}}'
        findings = scanner.scan_content(content, "package.json")
        assert len(findings) >= 2
        cve_ids = [f["cve_id"] for f in findings]
        assert "CVE-2019-10744" in cve_ids
        assert "CVE-2020-28168" in cve_ids

    def test_scan_requirements_txt(self):
        from scanners.cve_scanner import CVEScanner
        scanner = CVEScanner(use_osv=False)
        content = "django==3.2.0\nflask==2.0.0\n"
        findings = scanner.scan_content(content, "requirements.txt")
        assert len(findings) >= 2

    def test_scan_empty_file(self):
        from scanners.cve_scanner import CVEScanner
        scanner = CVEScanner(use_osv=False)
        findings = scanner.scan_content("{}", "package.json")
        assert findings == []

    def test_scan_terraform_providers(self):
        from scanners.cve_scanner import CVEScanner
        scanner = CVEScanner(use_osv=False)
        tf_content = '''
        provider "aws" {
          version = "3.0.0"
        }
        '''
        findings = scanner.scan_content(tf_content, "main.tf")
        assert len(findings) >= 1

    def test_expanded_local_db(self):
        from scanners.cve_scanner import CVEScanner
        scanner = CVEScanner(use_osv=False)
        # Verify expanded local DB has > 6 packages
        assert len(scanner.known_vulnerabilities) > 6
        assert "django" in scanner.known_vulnerabilities
        assert "flask" in scanner.known_vulnerabilities
        assert "pillow" in scanner.known_vulnerabilities


class TestRLAutoFix:
    """Test all 15 RL actions are implemented."""

    def test_all_15_actions_implemented(self):
        from ml.models.rl_auto_fix import FixAction, VulnerabilityState

        state = VulnerabilityState(
            vuln_type="unencrypted_storage",
            severity=0.8,
            resource_type="aws_s3_bucket",
            file_format="terraform",
            is_public=True,
            has_encryption=False,
            has_backup=False,
            has_logging=False,
            has_mfa=False,
            code_snippet='resource "aws_s3_bucket" "main" {\n  bucket = "my-bucket"\n}'
        )

        # All 15 actions should be callable (not raise)
        for action_id in range(FixAction.NUM_ACTIONS):
            result, success = FixAction.apply_fix(state, action_id)
            assert isinstance(result, str)
            assert isinstance(success, bool)

    def test_add_encryption_works(self):
        from ml.models.rl_auto_fix import FixAction, VulnerabilityState
        state = VulnerabilityState(
            vuln_type="unencrypted_storage", severity=0.8,
            resource_type="aws_s3_bucket", file_format="terraform",
            is_public=False, has_encryption=False, has_backup=False,
            has_logging=False, has_mfa=False,
            code_snippet='resource "aws_s3_bucket" "main" {\n  bucket = "test"\n}'
        )
        fixed, success = FixAction.apply_fix(state, FixAction.ADD_ENCRYPTION)
        assert success
        assert "server_side_encryption_configuration" in fixed

    def test_add_tags_works(self):
        from ml.models.rl_auto_fix import FixAction, VulnerabilityState
        state = VulnerabilityState(
            vuln_type="missing_tags", severity=0.3,
            resource_type="aws_s3_bucket", file_format="terraform",
            is_public=False, has_encryption=True, has_backup=False,
            has_logging=False, has_mfa=False,
            code_snippet='resource "aws_s3_bucket" "main" {\n  bucket = "test"\n}'
        )
        fixed, success = FixAction.apply_fix(state, FixAction.ADD_TAGS)
        assert success
        assert "tags" in fixed

    def test_strengthen_iam(self):
        from ml.models.rl_auto_fix import FixAction, VulnerabilityState
        state = VulnerabilityState(
            vuln_type="weak_iam", severity=0.9,
            resource_type="aws_iam_policy", file_format="terraform",
            is_public=False, has_encryption=False, has_backup=False,
            has_logging=False, has_mfa=False,
            code_snippet='{"Action": "*", "Resource": "*", "Effect": "Allow"}'
        )
        fixed, success = FixAction.apply_fix(state, FixAction.STRENGTHEN_IAM)
        assert success
        assert '"*"' not in fixed

    def test_enable_mfa(self):
        from ml.models.rl_auto_fix import FixAction, VulnerabilityState
        state = VulnerabilityState(
            vuln_type="missing_mfa", severity=0.7,
            resource_type="aws_s3_bucket", file_format="terraform",
            is_public=False, has_encryption=True, has_backup=False,
            has_logging=False, has_mfa=False,
            code_snippet='resource "aws_s3_bucket" "main" {\n  bucket = "test"\n}'
        )
        fixed, success = FixAction.apply_fix(state, FixAction.ENABLE_MFA)
        assert success
        assert "mfa_delete" in fixed
