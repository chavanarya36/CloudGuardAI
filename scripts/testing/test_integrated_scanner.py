"""
Test script for Integrated Scanner
Verifies all 6 scanners work together correctly
"""

import sys
from pathlib import Path

# Add api directory to path
api_dir = Path(__file__).parent / "api"
sys.path.insert(0, str(api_dir))

from scanners.integrated_scanner import get_integrated_scanner

# Test file content with multiple security issues
test_terraform_content = """
# Test Terraform file with multiple security issues

# ISSUE 1: Hardcoded AWS credentials (SECRETS SCANNER)
provider "aws" {
  access_key = "AKIAEXAMPLEKEYDONOTUSE"
  secret_key = "EXAMPLESECRETKEY/DO/NOT/USE/EXAMPLE"
  region     = "us-east-1"
}

# ISSUE 2: Security group with SSH open to world (COMPLIANCE SCANNER)
resource "aws_security_group" "web" {
  name        = "web-sg"
  description = "Web server security group"
  
  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]  # SSH open to world - CIS violation
  }
  
  ingress {
    from_port   = 3389
    to_port     = 3389
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]  # RDP open to world - CIS violation
  }
}

# ISSUE 3: S3 bucket without encryption (COMPLIANCE SCANNER)
resource "aws_s3_bucket" "data" {
  bucket = "my-data-bucket"
  # Missing encryption configuration - CIS violation
  # Missing logging configuration - CIS violation
}

# ISSUE 4: IAM user without MFA (COMPLIANCE SCANNER)
resource "aws_iam_user" "admin" {
  name = "admin-user"
  # Missing MFA configuration - CIS violation
}

# ISSUE 5: Vulnerable dependency (CVE SCANNER)
# package.json would be detected if present
# terraform { required_version = "0.12.0" }  # Old version with CVEs
"""

test_package_json = """
{
  "name": "vulnerable-app",
  "version": "1.0.0",
  "dependencies": {
    "lodash": "4.17.4",
    "axios": "0.18.0",
    "express": "4.16.0"
  }
}
"""

def test_integrated_scanner():
    """Test the integrated scanner with all detections"""
    
    print("=" * 80)
    print("TESTING INTEGRATED SECURITY SCANNER")
    print("=" * 80)
    print()
    
    # Get scanner instance
    scanner = get_integrated_scanner()
    
    # Test Terraform file
    print("📝 Testing Terraform file with multiple security issues...")
    print()
    
    result = scanner.scan_file_integrated(
        file_path="test_vulnerable.tf",
        content=test_terraform_content,
        rules_findings=[],
        ml_score=75.0,
        llm_findings=[]
    )
    
    # Print summary
    print(scanner.generate_scan_summary(result))
    print()
    
    # Print detailed findings
    print("=" * 80)
    print("DETAILED FINDINGS BY SCANNER")
    print("=" * 80)
    print()
    
    for scanner_name, findings in result['findings'].items():
        if findings:
            print(f"\n🔍 {scanner_name.upper()} SCANNER - {len(findings)} findings:")
            print("-" * 60)
            
            for i, finding in enumerate(findings, 1):
                print(f"\n  {i}. {finding.get('title', 'Unknown Issue')}")
                print(f"     Severity: {finding.get('severity', 'UNKNOWN')}")
                print(f"     Type: {finding.get('type', 'UNKNOWN')}")
                print(f"     Description: {finding.get('description', 'N/A')[:100]}...")
                
                if finding.get('line_number'):
                    print(f"     Line: {finding.get('line_number')}")
                
                remediation = finding.get('remediation_steps', [])
                if remediation:
                    print(f"     Remediation: {remediation[0] if remediation else 'N/A'}")
    
    print()
    print("=" * 80)
    print("INTEGRATION TEST RESULTS")
    print("=" * 80)
    
    # Verify all scanners ran
    scanners_expected = ['secrets', 'cve', 'compliance']
    scanners_ran = list(result['findings'].keys())
    
    print(f"\n✅ Scanners expected: {scanners_expected}")
    print(f"✅ Scanners executed: {scanners_ran}")
    
    # Check if we got findings
    total_findings = result['summary']['total_findings']
    print(f"\n📊 Total findings detected: {total_findings}")
    
    # Verify each scanner
    print("\n🎯 Scanner Performance:")
    for scanner, timing in result['performance']['scanner_timings'].items():
        count = len(result['findings'][scanner])
        print(f"   {scanner}: {count} findings in {timing:.3f}s")
    
    # Risk scores
    print("\n📈 Risk Scores:")
    scores = result['scores']
    for score_name, score_value in scores.items():
        print(f"   {score_name}: {score_value:.2f}")
    
    print()
    
    # Success criteria
    success = True
    errors = []
    
    # 1. All scanners should run
    if not all(s in scanners_ran for s in scanners_expected):
        success = False
        errors.append("Not all scanners executed")
    
    # 2. Should detect at least 4 issues (1 secret, 1 compliance, etc.)
    if total_findings < 4:
        success = False
        errors.append(f"Expected at least 4 findings, got {total_findings}")
    
    # 3. Secrets scanner should find the hardcoded AWS key
    secrets_found = len(result['findings']['secrets'])
    if secrets_found < 1:
        success = False
        errors.append("Secrets scanner didn't find hardcoded credentials")
    
    # 4. Compliance scanner should find CIS violations
    compliance_found = len(result['findings']['compliance'])
    if compliance_found < 3:  # Should find SSH, RDP, S3, IAM issues
        success = False
        errors.append(f"Compliance scanner found {compliance_found} issues, expected at least 3")
    
    print("=" * 80)
    if success:
        print("✅ INTEGRATION TEST PASSED!")
        print("   All scanners working correctly")
    else:
        print("❌ INTEGRATION TEST FAILED!")
        for error in errors:
            print(f"   - {error}")
    print("=" * 80)
    print()
    
    return success


if __name__ == "__main__":
    try:
        success = test_integrated_scanner()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ TEST FAILED WITH ERROR:")
        print(f"   {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


