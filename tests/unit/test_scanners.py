"""
Unit tests for all CloudGuardAI scanners.
Covers: secrets_scanner, cve_scanner, compliance_scanner, integrated_scanner
"""
import pytest
import sys
from pathlib import Path

# Ensure scanners are importable
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "api"))


# ===================== Secrets Scanner Tests =====================

class TestSecretsScanner:
    """Tests for the SecretsScanner"""
    
    @pytest.fixture
    def scanner(self):
        from scanners.secrets_scanner import SecretsScanner
        return SecretsScanner()
    
    def test_detects_aws_access_key(self, scanner):
        content = 'access_key = "AKIAEXAMPLEKEYDONOTUSE"'
        findings = scanner.scan_content(content, "test.tf")
        assert len(findings) >= 1
        aws_findings = [f for f in findings if 'AWS' in f['title']]
        assert len(aws_findings) >= 1
    
    def test_detects_github_token(self, scanner):
        content = 'token = "ghp_ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklm"'
        findings = scanner.scan_content(content, "test.yaml")
        github_findings = [f for f in findings if 'GitHub' in f['title']]
        assert len(github_findings) >= 1
    
    def test_detects_private_key(self, scanner):
        content = '-----BEGIN RSA PRIVATE KEY-----'
        findings = scanner.scan_content(content, "test.pem")
        key_findings = [f for f in findings if 'Private Key' in f['title']]
        assert len(key_findings) >= 1
    
    def test_detects_gcp_api_key(self, scanner):
        content = 'api_key = "AIzaSyABCDEFGHIJKLMNOPQRSTUVWXYZ1234567"'
        findings = scanner.scan_content(content, "test.tf")
        gcp_findings = [f for f in findings if 'GCP' in f['title']]
        assert len(gcp_findings) >= 1
    
    def test_skips_comments(self, scanner):
        content = '# access_key = "AKIAEXAMPLEKEYDONOTUSE"'
        findings = scanner.scan_content(content, "test.tf")
        assert len(findings) == 0
    
    def test_skips_placeholders(self, scanner):
        content = 'access_key = "<your-access-key>"'
        findings = scanner.scan_content(content, "test.tf")
        assert len(findings) == 0
    
    def test_redacts_secret_values(self, scanner):
        content = 'token = "ghp_ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklm"'
        findings = scanner.scan_content(content, "test.yaml")
        for finding in findings:
            snippet = finding.get('code_snippet', '')
            # The full token should NOT appear in the snippet
            assert 'ghp_ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklm' not in snippet
    
    def test_findings_have_required_fields(self, scanner):
        content = '-----BEGIN PRIVATE KEY-----'
        findings = scanner.scan_content(content, "test.pem")
        if findings:
            f = findings[0]
            assert 'severity' in f
            assert 'title' in f
            assert 'description' in f
            assert 'category' in f
            assert f['category'] == 'secrets'
            assert 'remediation_steps' in f
            assert isinstance(f['remediation_steps'], list)
    
    def test_entropy_calculation(self, scanner):
        # High entropy string (random-like)
        high_entropy = scanner.calculate_entropy("aB3$kL9mNpQrStUvWxYz")
        assert high_entropy > 3.5
        
        # Low entropy string (repetitive)
        low_entropy = scanner.calculate_entropy("aaaaaaaaaa")
        assert low_entropy < 1.0
    
    def test_empty_content(self, scanner):
        findings = scanner.scan_content("", "test.tf")
        assert findings == []
    
    def test_safe_content_no_false_positives(self, scanner):
        content = '''
resource "aws_instance" "example" {
  ami           = "ami-12345678"
  instance_type = "t2.micro"
  
  tags = {
    Name = "my-instance"
  }
}
'''
        findings = scanner.scan_content(content, "test.tf")
        # Should not have findings for normal Terraform
        secret_findings = [f for f in findings if f['category'] == 'secrets']
        # Allow some findings but no CRITICAL false positives for this safe content
        critical_findings = [f for f in secret_findings if f['severity'] == 'CRITICAL']
        assert len(critical_findings) == 0


# ===================== CVE Scanner Tests =====================

class TestCVEScanner:
    """Tests for the CVEScanner"""
    
    @pytest.fixture
    def scanner(self):
        from scanners.cve_scanner import CVEScanner
        return CVEScanner()
    
    def test_scan_requirements_txt(self, scanner):
        content = '''flask==1.0
requests==2.25.0
django==2.2.0
'''
        findings = scanner.scan_content(content, "requirements.txt")
        assert isinstance(findings, list)
    
    def test_scan_terraform_providers(self, scanner):
        content = '''
terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "4.0.0"
    }
  }
}
'''
        findings = scanner.scan_content(content, "main.tf")
        assert isinstance(findings, list)
    
    def test_findings_structure(self, scanner):
        content = 'flask==1.0\nrequests==2.20.0'
        findings = scanner.scan_content(content, "requirements.txt")
        for f in findings:
            assert 'severity' in f
            assert 'title' in f or 'description' in f
            assert 'category' in f
    
    def test_empty_content(self, scanner):
        findings = scanner.scan_content("", "requirements.txt")
        assert isinstance(findings, list)
    
    def test_package_json(self, scanner):
        content = '''{
  "dependencies": {
    "lodash": "4.17.4",
    "express": "4.17.0"
  }
}'''
        findings = scanner.scan_content(content, "package.json")
        assert isinstance(findings, list)


# ===================== Compliance Scanner Tests =====================

class TestComplianceScanner:
    """Tests for the ComplianceScanner"""
    
    @pytest.fixture
    def scanner(self):
        from scanners.compliance_scanner import ComplianceScanner
        return ComplianceScanner()
    
    def test_detects_unencrypted_s3(self, scanner):
        config = {
            's3': {
                'buckets': [
                    {'name': 'data-bucket', 'arn': 'arn:aws:s3:::data-bucket', 'encryption_enabled': False, 'logging_enabled': True}
                ]
            }
        }
        findings = scanner.scan_compliance(config)
        encryption_findings = [f for f in findings if 'encrypt' in f.get('title', '').lower() or 'encrypt' in f.get('description', '').lower()]
        assert len(encryption_findings) >= 1
    
    def test_detects_open_security_group(self, scanner):
        config = {
            'security_groups': [
                {
                    'name': 'open-sg',
                    'id': 'sg-123',
                    'ingress_rules': [
                        {'from_port': 22, 'to_port': 22, 'cidr_blocks': ['0.0.0.0/0']}
                    ]
                }
            ]
        }
        findings = scanner.scan_compliance(config)
        assert len(findings) >= 1
        assert any('SSH' in f.get('description', '') or '22' in f.get('description', '') for f in findings)
    
    def test_detects_rdp_open(self, scanner):
        config = {
            'security_groups': [
                {
                    'name': 'rdp-sg',
                    'id': 'sg-456',
                    'ingress_rules': [
                        {'from_port': 3389, 'to_port': 3389, 'cidr_blocks': ['0.0.0.0/0']}
                    ]
                }
            ]
        }
        findings = scanner.scan_compliance(config)
        assert len(findings) >= 1
    
    def test_iam_mfa_check(self, scanner):
        config = {
            'iam': {
                'users': [
                    {'name': 'admin', 'arn': 'arn:aws:iam::123:user/admin', 'mfa_enabled': False}
                ]
            }
        }
        findings = scanner.scan_compliance(config)
        mfa_findings = [f for f in findings if 'MFA' in f.get('title', '')]
        assert len(mfa_findings) >= 1
    
    def test_compliant_config_no_findings(self, scanner):
        config = {
            'iam': {
                'users': [
                    {'name': 'admin', 'mfa_enabled': True}
                ]
            },
            's3': {
                'buckets': [
                    {'name': 'secure', 'encryption_enabled': True, 'logging_enabled': True}
                ]
            },
            'security_groups': [
                {
                    'name': 'secure-sg',
                    'id': 'sg-789',
                    'ingress_rules': [
                        {'from_port': 443, 'to_port': 443, 'cidr_blocks': ['10.0.0.0/8']}
                    ]
                }
            ]
        }
        findings = scanner.scan_compliance(config)
        assert len(findings) == 0
    
    def test_empty_config(self, scanner):
        findings = scanner.scan_compliance({})
        assert isinstance(findings, list)
        assert len(findings) == 0
    
    def test_findings_have_compliance_fields(self, scanner):
        config = {
            'iam': {
                'users': [
                    {'name': 'user1', 'mfa_enabled': False}
                ]
            }
        }
        findings = scanner.scan_compliance(config)
        for f in findings:
            assert f.get('category') == 'compliance'
            assert 'compliance_framework' in f
            assert 'control_id' in f
            assert 'remediation_steps' in f


# ===================== Integrated Scanner Tests =====================

class TestIntegratedScanner:
    """Tests for the IntegratedScanner orchestrator"""
    
    @pytest.fixture
    def scanner(self):
        from scanners.integrated_scanner import get_integrated_scanner
        return get_integrated_scanner()
    
    def test_scan_terraform_content(self, scanner):
        content = '''
resource "aws_s3_bucket" "example" {
  bucket = "my-bucket"
}

resource "aws_security_group" "example" {
  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }
}
'''
        result = scanner.scan_content(content, "main.tf")
        assert isinstance(result, dict)
        assert 'findings' in result
        assert 'total_findings' in result
        assert isinstance(result['findings'], list)
    
    def test_result_has_risk_score(self, scanner):
        content = '''
resource "aws_s3_bucket" "example" {
  bucket = "my-bucket"
}
'''
        result = scanner.scan_content(content, "main.tf")
        assert 'risk_score' in result
        assert isinstance(result['risk_score'], (int, float))
        assert 0.0 <= result['risk_score'] <= 1.0
    
    def test_result_has_severity_counts(self, scanner):
        content = '''
provider "aws" {
  access_key = "AKIAEXAMPLEKEYDONOTUSE"
  secret_key = "EXAMPLESECRETKEY/DO/NOT/USE/EXAMPLE"
}
'''
        result = scanner.scan_content(content, "main.tf")
        assert 'severity_counts' in result
    
    def test_scan_yaml_content(self, scanner):
        content = '''
apiVersion: v1
kind: Pod
metadata:
  name: test-pod
spec:
  containers:
    - name: test
      image: nginx:latest
      securityContext:
        privileged: true
'''
        result = scanner.scan_content(content, "pod.yaml")
        assert isinstance(result, dict)
        assert 'findings' in result
    
    def test_empty_content(self, scanner):
        result = scanner.scan_content("", "empty.tf")
        assert isinstance(result, dict)
        assert result.get('total_findings', 0) >= 0
    
    def test_scanners_used_reported(self, scanner):
        content = 'resource "aws_s3_bucket" "test" { bucket = "test" }'
        result = scanner.scan_content(content, "main.tf")
        assert 'scanners_used' in result
        assert isinstance(result['scanners_used'], list)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])


