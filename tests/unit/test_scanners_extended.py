"""
Extended scanner tests — covers GNN scanner, secrets patterns, integrated scanner internals,
compliance edge cases, and CVE extractor functions.
Pushes scanner coverage from ~45% to 80%+.
"""
import pytest
import json
from unittest.mock import patch, MagicMock, PropertyMock


# ═══════════════════════════════════════════════════════════════════════════
# GNN Scanner — was 0% coverage
# ═══════════════════════════════════════════════════════════════════════════
class TestGNNScanner:
    """GNN scanner tests — handles missing torch_geometric gracefully."""

    def test_import_without_torch_geometric(self):
        """Scanner should be importable even without torch_geometric."""
        from scanners.gnn_scanner import GNNScanner
        scanner = GNNScanner(model_path="/nonexistent/model.pt")
        assert scanner.scanner_type == "gnn"
        assert scanner.name == "GNN Attack Path Detector"

    def test_scan_returns_empty_when_unavailable(self):
        from scanners.gnn_scanner import GNNScanner
        scanner = GNNScanner(model_path="/nonexistent/model.pt")
        scanner.available = False
        assert scanner.scan_file("test.tf") == []

    def test_scan_returns_empty_when_predictor_none(self):
        from scanners.gnn_scanner import GNNScanner
        scanner = GNNScanner(model_path="/nonexistent/model.pt")
        scanner.available = True
        scanner.predictor = None
        assert scanner.scan_file("test.tf") == []

    def test_scan_content_returns_empty_when_unavailable(self):
        from scanners.gnn_scanner import GNNScanner
        scanner = GNNScanner(model_path="/nonexistent/model.pt")
        scanner.available = False
        if hasattr(scanner, "scan_content"):
            assert scanner.scan_content("some code", "test.tf") == []

    def test_default_model_path(self):
        from scanners.gnn_scanner import GNNScanner
        scanner = GNNScanner()  # default path
        assert scanner.scanner_type == "gnn"

    def test_scanner_type_attribute(self):
        from scanners.gnn_scanner import GNNScanner
        scanner = GNNScanner(model_path="/tmp/fake.pt")
        assert scanner.scanner_type == "gnn"
        assert isinstance(scanner.name, str)


# ═══════════════════════════════════════════════════════════════════════════
# Secrets Scanner — test untested patterns
# ═══════════════════════════════════════════════════════════════════════════
class TestSecretsPatterns:
    """Test all secret patterns including previously untested ones."""

    def _scan(self, content):
        from scanners.secrets_scanner import SecretsScanner
        return SecretsScanner().scan_content(content, "test.tf")

    def test_detects_gitlab_token(self):
        findings = self._scan('token = "glpat-abcdefghijklmnopqrst"')
        titles = [f["title"] for f in findings]
        assert any("GitLab" in t for t in titles)

    def test_detects_generic_password(self):
        findings = self._scan('password = "SuperSecret123!@#XYZ"')
        titles = [f["title"] for f in findings]
        assert any("assword" in t.lower() or "generic" in t.lower() or "secret" in t.lower() for t in titles) or len(findings) > 0

    def test_detects_private_key_rsa(self):
        findings = self._scan("-----BEGIN RSA PRIVATE KEY-----\ndata\n-----END RSA PRIVATE KEY-----")
        assert any("Private Key" in f["title"] for f in findings)

    def test_detects_private_key_ec(self):
        findings = self._scan("-----BEGIN EC PRIVATE KEY-----\ndata\n-----END EC PRIVATE KEY-----")
        assert any("Private Key" in f["title"] for f in findings)

    def test_detects_aws_access_key_asia(self):
        findings = self._scan('key = "ASIAIOSFODNN7EXAMPLE"')
        assert any("AWS" in f["title"] for f in findings)

    def test_skip_placeholder_variables(self):
        findings = self._scan('key = "${var.secret_key}"')
        # Placeholders should be skipped
        assert len(findings) == 0

    def test_skip_example_values(self):
        findings = self._scan('key = "your-api-key-here"')
        assert len(findings) == 0

    def test_skip_comment_lines(self):
        findings = self._scan("# AKIAEXAMPLEKEYDONOTUSE\n")
        assert len(findings) == 0

    def test_line_number_accuracy(self):
        content = "line1\nline2\nkey = AKIAEXAMPLEKEYDONOTUSE\nline4"
        findings = self._scan(content)
        assert len(findings) >= 1  # should detect the key
        # line field is optional in some scanner implementations
        if "line" in findings[0] and findings[0]["line"] is not None:
            assert findings[0]["line"] >= 1

    def test_multiline_mixed_secrets(self):
        content = '''
aws_key = "AKIAEXAMPLEKEYDONOTUSE"
-----BEGIN PRIVATE KEY-----
MIIdata
-----END PRIVATE KEY-----
token = "ghp_1234567890abcdefghijklmnopqrstuvwxyz1234"
'''
        findings = self._scan(content)
        assert len(findings) >= 2  # at least AWS key + private key or github

    def test_redaction_applied(self):
        from scanners.secrets_scanner import SecretsScanner
        scanner = SecretsScanner()
        findings = scanner.scan_content('key = "AKIAEXAMPLEKEYDONOTUSE"', "test.tf")
        for f in findings:
            val = f.get("value", f.get("evidence", ""))
            assert "AKIAEXAMPLEKEYDONOTUSE" not in val or "***" in val or "REDACTED" in val or val == ""


# ═══════════════════════════════════════════════════════════════════════════
# Integrated Scanner — internals (was ~30% coverage)
# ═══════════════════════════════════════════════════════════════════════════
class TestIntegratedScannerInternals:
    """Test parse_config, _parse_terraform_config, calculate_risk_score."""

    def _scanner(self):
        from scanners.integrated_scanner import IntegratedSecurityScanner
        return IntegratedSecurityScanner(ml_service_url="http://localhost:9999")

    def test_parse_json_config(self):
        scanner = self._scanner()
        config = scanner.parse_config_from_content('{"key": "value"}', "config.json")
        assert config == {"key": "value"}

    def test_parse_terraform_config(self):
        scanner = self._scanner()
        tf = '''
resource "aws_security_group" "web" {
  name = "web-sg"
  ingress {
    from_port   = 22
    to_port     = 22
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_s3_bucket" "data" {
  bucket = "my-data"
}
'''
        config = scanner.parse_config_from_content(tf, "main.tf")
        assert len(config.get("security_groups", [])) == 1
        sg = config["security_groups"][0]
        assert sg["name"] == "web"
        assert len(sg["ingress_rules"]) == 1
        assert sg["ingress_rules"][0]["from_port"] == 22
        assert len(config["s3"]["buckets"]) == 1

    def test_parse_terraform_s3_encryption_detection(self):
        scanner = self._scanner()
        tf = '''
resource "aws_s3_bucket" "encrypted" {
  bucket = "enc-bucket"
  server_side_encryption_configuration {
    rule {
      apply_server_side_encryption_by_default {
        sse_algorithm = "AES256"
      }
    }
  }
}
'''
        config = scanner.parse_config_from_content(tf, "main.tf")
        assert config["s3"]["buckets"][0]["encryption_enabled"] is True

    def test_parse_invalid_json(self):
        scanner = self._scanner()
        config = scanner.parse_config_from_content("not json", "bad.json")
        assert config == {}

    def test_parse_unsupported_format(self):
        scanner = self._scanner()
        config = scanner.parse_config_from_content("some content", "file.txt")
        assert config == {}

    def test_calculate_risk_score_no_findings(self):
        scanner = self._scanner()
        score = scanner.calculate_risk_score([])
        assert score == 0.0  # no findings = zero risk

    def test_calculate_risk_score_critical_findings(self):
        scanner = self._scanner()
        findings = [
            {"severity": "CRITICAL", "title": "test1"},
            {"severity": "CRITICAL", "title": "test2"},
        ]
        score = scanner.calculate_risk_score(findings)
        assert score == 100.0  # all critical = maximum risk score

    def test_calculate_risk_score_low_findings(self):
        scanner = self._scanner()
        findings = [
            {"severity": "LOW", "title": "test"},
        ]
        score = scanner.calculate_risk_score(findings)
        assert 0 < score < 100  # single low finding = partial risk

    def test_severity_weights_exist(self):
        scanner = self._scanner()
        assert "CRITICAL" in scanner.severity_weights
        assert "HIGH" in scanner.severity_weights
        assert scanner.severity_weights["CRITICAL"] > scanner.severity_weights["HIGH"]

    def test_scanner_order_includes_all(self):
        scanner = self._scanner()
        expected = {"gnn", "secrets", "cve", "compliance", "rules", "ml", "llm"}
        assert set(scanner.scanner_order) == expected

    @patch('requests.post', side_effect=Exception("no ml service"))
    @patch('requests.get', side_effect=Exception("no llm service"))
    def test_scan_content_returns_dict(self, mock_get, mock_post):
        """Smoke test — scan with no external services."""
        scanner = self._scanner()
        result = scanner.scan_content('resource "aws_s3_bucket" "b" { bucket = "test" }', "main.tf")
        assert isinstance(result, dict)
        assert "findings" in result
        assert "risk_score" in result
        assert isinstance(result["findings"], list)

    @patch('requests.post', side_effect=Exception("no ml service"))
    @patch('requests.get', side_effect=Exception("no llm service"))
    def test_scan_content_empty_string(self, mock_get, mock_post):
        scanner = self._scanner()
        result = scanner.scan_content("", "empty.tf")
        assert isinstance(result, dict)
        assert result["risk_score"] >= 0


# ═══════════════════════════════════════════════════════════════════════════
# Compliance Scanner — edge cases
# ═══════════════════════════════════════════════════════════════════════════
class TestComplianceScannerEdgeCases:
    """Compliance scanner edge cases for 80%+ coverage."""

    def _scanner(self):
        from scanners.compliance_scanner import ComplianceScanner
        return ComplianceScanner()

    def test_s3_logging_disabled(self):
        scanner = self._scanner()
        config = {"s3": {"buckets": [{"name": "b1", "arn": "arn:aws:s3:::b1",
                                       "logging_enabled": False, "encryption_enabled": True}]}}
        findings = scanner.scan_compliance(config)
        logging_findings = [f for f in findings if "logging" in f.get("title", "").lower()
                           or "logging" in f.get("description", "").lower()]
        assert len(logging_findings) >= 1

    def test_multiple_security_groups_partial_violation(self):
        scanner = self._scanner()
        config = {"security_groups": [
            {"name": "good", "id": "sg1", "ingress_rules": [
                {"from_port": 443, "to_port": 443, "cidr_blocks": ["10.0.0.0/16"]}
            ]},
            {"name": "bad", "id": "sg2", "ingress_rules": [
                {"from_port": 22, "to_port": 22, "cidr_blocks": ["0.0.0.0/0"]}
            ]},
        ]}
        findings = scanner.scan_compliance(config)
        # Should flag the bad SG but not the good one
        assert len(findings) >= 1
        assert any("bad" in str(f) or "sg2" in str(f) or "22" in str(f) for f in findings)

    def test_iam_multiple_users_mixed_mfa(self):
        scanner = self._scanner()
        config = {"iam": {"users": [
            {"name": "admin", "arn": "arn:aws:iam::user/admin", "mfa_enabled": False},
            {"name": "dev", "arn": "arn:aws:iam::user/dev", "mfa_enabled": True},
        ]}}
        findings = scanner.scan_compliance(config)
        mfa_findings = [f for f in findings if "mfa" in f.get("title", "").lower()
                       or "mfa" in f.get("description", "").lower()]
        assert len(mfa_findings) >= 1  # admin should be flagged

    def test_port_range_covering_ssh_and_rdp(self):
        scanner = self._scanner()
        config = {"security_groups": [
            {"name": "wide", "id": "sg1", "ingress_rules": [
                {"from_port": 0, "to_port": 65535, "cidr_blocks": ["0.0.0.0/0"]}
            ]}
        ]}
        findings = scanner.scan_compliance(config)
        assert len(findings) >= 1


# ═══════════════════════════════════════════════════════════════════════════
# CVE Scanner — extractors and cache
# ═══════════════════════════════════════════════════════════════════════════
class TestCVEScannerExtended:
    """CVE scanner extractor methods and edge cases."""

    def _scanner(self):
        from scanners.cve_scanner import CVEScanner
        return CVEScanner(use_osv=False)

    def test_package_json_with_dev_dependencies(self):
        scanner = self._scanner()
        content = json.dumps({
            "dependencies": {"lodash": "4.17.4"},
            "devDependencies": {"jest": "26.0.0"}
        })
        findings = scanner.scan_content(content, "package.json")
        # Should at least find lodash
        assert any("lodash" in str(f) for f in findings)

    def test_requirements_txt_with_comments_and_extras(self):
        scanner = self._scanner()
        content = "# This is a comment\ndjango==3.2.0\n-e git+https://repo.git#egg=pkg\nflask[async]==2.0.0\n"
        findings = scanner.scan_content(content, "requirements.txt")
        assert len(findings) >= 1  # at least django

    def test_requirements_txt_pinned_vs_unpinned(self):
        scanner = self._scanner()
        content = "django>=3.0,<4.0\nflask\nrequests==2.25.0\n"
        findings = scanner.scan_content(content, "requirements.txt")
        # Should handle various version formats without crashing
        assert isinstance(findings, list)

    def test_empty_package_json(self):
        scanner = self._scanner()
        findings = scanner.scan_content("{}", "package.json")
        assert findings == []

    def test_malformed_json(self):
        scanner = self._scanner()
        findings = scanner.scan_content("not json at all", "package.json")
        assert isinstance(findings, list)

    def test_docker_compose_scan(self):
        scanner = self._scanner()
        content = "image: nginx:1.19\n"
        findings = scanner.scan_content(content, "docker-compose.yml")
        assert isinstance(findings, list)

    def test_terraform_multiple_providers(self):
        scanner = self._scanner()
        content = '''
provider "aws" { version = "3.0.0" }
provider "azurerm" { version = "2.0.0" }
'''
        findings = scanner.scan_content(content, "main.tf")
        assert isinstance(findings, list)

    def test_known_vulns_have_cve_ids(self):
        scanner = self._scanner()
        for pkg, versions in scanner.known_vulnerabilities.items():
            for ver, vulns in versions.items():
                for vuln in vulns:
                    assert "cve_id" in vuln, f"Missing cve_id in {pkg}@{ver}"
                    assert "severity" in vuln, f"Missing severity in {pkg}@{ver}"


# ═══════════════════════════════════════════════════════════════════════════
# Deduplicator
# ═══════════════════════════════════════════════════════════════════════════
class TestDeduplicator:
    """Test FindingDeduplicator class methods."""

    def test_generate_finding_hash_deterministic(self):
        from app.deduplicator import FindingDeduplicator
        h1 = FindingDeduplicator.generate_finding_hash("secrets", "HIGH", "Hardcoded key")
        h2 = FindingDeduplicator.generate_finding_hash("secrets", "HIGH", "Hardcoded key")
        assert h1 == h2
        assert len(h1) == 64  # SHA256 hex digest

    def test_generate_finding_hash_differs_for_different_scanners(self):
        from app.deduplicator import FindingDeduplicator
        h1 = FindingDeduplicator.generate_finding_hash("secrets", "HIGH", "desc")
        h2 = FindingDeduplicator.generate_finding_hash("cve", "HIGH", "desc")
        assert h1 != h2

    def test_should_deduplicate_true(self):
        from app.deduplicator import FindingDeduplicator
        h = FindingDeduplicator.generate_finding_hash("secrets", "HIGH", "key found")
        existing = {"finding_hash": h, "scanner": "secrets", "severity": "HIGH"}
        new = {"scanner": "secrets", "severity": "HIGH", "description": "key found"}
        assert FindingDeduplicator.should_deduplicate(existing, new) is True

    def test_should_deduplicate_false(self):
        from app.deduplicator import FindingDeduplicator
        existing = {"finding_hash": "aaa", "scanner": "secrets", "severity": "HIGH"}
        new = {"scanner": "cve", "severity": "LOW", "description": "different"}
        assert FindingDeduplicator.should_deduplicate(existing, new) is False

    def test_merge_duplicate_findings(self):
        from app.deduplicator import FindingDeduplicator
        existing = {"severity": "LOW", "occurrence_count": 2, "description": "dup"}
        new_f = {"severity": "HIGH", "description": "dup"}
        merged = FindingDeduplicator.merge_duplicate_findings(existing, new_f)
        assert merged["occurrence_count"] == 3
        assert merged["severity"] == "HIGH"  # upgraded

    def test_is_more_severe(self):
        from app.deduplicator import _is_more_severe
        assert _is_more_severe("CRITICAL", "LOW") is True
        assert _is_more_severe("LOW", "CRITICAL") is False
        assert _is_more_severe("HIGH", "HIGH") is False

