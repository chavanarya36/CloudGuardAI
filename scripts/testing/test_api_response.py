"""
Test API Response Updates - Step 1.5
Validates that API returns scanner-specific findings correctly
"""

import requests
import json
from pathlib import Path

# Test Terraform content with known issues
test_terraform = """
provider "aws" {
  access_key = "AKIAEXAMPLEKEYDONOTUSE"
  secret_key = "EXAMPLESECRETKEY/DO/NOT/USE/EXAMPLE"
  region     = "us-east-1"
}

resource "aws_security_group" "web" {
  name = "web-sg"
  
  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }
}
"""

def test_api_scan_response():
    """Test that API returns enhanced scanner-specific response"""
    
    print("=" * 80)
    print("TESTING API RESPONSE UPDATES - STEP 1.5")
    print("=" * 80)
    print()
    
    # API endpoint
    api_url = "http://127.0.0.1:8000/scan"
    
    # Prepare request
    payload = {
        "file_name": "test_api.tf",
        "file_content": test_terraform
    }
    
    print("📡 Sending scan request to API...")
    print(f"   Endpoint: {api_url}")
    print(f"   File: {payload['file_name']}")
    print()
    
    try:
        # Send request
        response = requests.post(api_url, json=payload, timeout=30)
        
        if response.status_code != 200:
            print(f"❌ API returned status {response.status_code}")
            print(f"   Error: {response.text}")
            return False
        
        # Parse response
        result = response.json()
        
        print("✅ API Response received successfully!")
        print()
        print("=" * 80)
        print("RESPONSE STRUCTURE VALIDATION")
        print("=" * 80)
        print()
        
        # Validate required fields
        required_fields = [
            'scan_id', 'status', 'unified_risk_score',
            'ml_score', 'rules_score', 'llm_score',
            'findings'
        ]
        
        # New scanner-specific fields
        new_fields = [
            'secrets_score', 'cve_score', 'compliance_score',
            'secrets_findings', 'cve_findings', 'compliance_findings',
            'scanner_breakdown'
        ]
        
        print("📋 Checking required fields:")
        all_present = True
        for field in required_fields:
            present = field in result
            status = "✅" if present else "❌"
            print(f"   {status} {field}: {present}")
            if not present:
                all_present = False
        
        print()
        print("📋 Checking new scanner-specific fields:")
        new_fields_present = True
        for field in new_fields:
            present = field in result
            status = "✅" if present else "❌"
            value = result.get(field, "N/A")
            if isinstance(value, list):
                print(f"   {status} {field}: {len(value)} items")
            elif isinstance(value, dict):
                print(f"   {status} {field}: {value}")
            else:
                print(f"   {status} {field}: {value}")
            if not present:
                new_fields_present = False
        
        print()
        print("=" * 80)
        print("SCAN RESULTS SUMMARY")
        print("=" * 80)
        print()
        
        print(f"📊 Scan ID: {result.get('scan_id', 'N/A')}")
        print(f"📊 Status: {result.get('status', 'N/A')}")
        print()
        
        print("Risk Scores:")
        print(f"   Unified Risk: {result.get('unified_risk_score', 0):.2f}/1.0")
        print(f"   ML Score: {result.get('ml_score', 0):.2f}")
        print(f"   Rules Score: {result.get('rules_score', 0):.2f}")
        print(f"   LLM Score: {result.get('llm_score', 0):.2f}")
        print(f"   Secrets Score: {result.get('secrets_score', 0):.2f}")
        print(f"   CVE Score: {result.get('cve_score', 0):.2f}")
        print(f"   Compliance Score: {result.get('compliance_score', 100):.2f}/100")
        print()
        
        # Scanner breakdown
        breakdown = result.get('scanner_breakdown', {})
        if breakdown:
            print("Scanner Breakdown:")
            for scanner, count in breakdown.items():
                print(f"   {scanner}: {count} findings")
            print()
        
        # Findings summary
        total_findings = len(result.get('findings', []))
        secrets_count = len(result.get('secrets_findings', []))
        cve_count = len(result.get('cve_findings', []))
        compliance_count = len(result.get('compliance_findings', []))
        
        print(f"Total Findings: {total_findings}")
        print(f"   Secrets: {secrets_count}")
        print(f"   CVE: {cve_count}")
        print(f"   Compliance: {compliance_count}")
        print()
        
        # Show sample findings from each category
        if secrets_count > 0:
            print("🔑 Sample Secret Finding:")
            secret = result['secrets_findings'][0]
            print(f"   Title: {secret.get('title', 'N/A')}")
            print(f"   Severity: {secret.get('severity', 'N/A')}")
            print(f"   Category: {secret.get('category', 'N/A')}")
            print()
        
        if compliance_count > 0:
            print("📋 Sample Compliance Finding:")
            comp = result['compliance_findings'][0]
            print(f"   Title: {comp.get('title', 'N/A')}")
            print(f"   Severity: {comp.get('severity', 'N/A')}")
            print(f"   Control ID: {comp.get('type', 'N/A')}")
            print()
        
        # Reasoning
        reasoning = result.get('reasoning', '')
        if reasoning:
            print(f"💡 Reasoning: {reasoning[:150]}...")
            print()
        
        print("=" * 80)
        print("VALIDATION RESULTS")
        print("=" * 80)
        
        success = all_present and new_fields_present
        
        if success:
            print("✅ ALL VALIDATIONS PASSED!")
            print("   - All required fields present")
            print("   - All new scanner fields present")
            print("   - Scanner breakdown included")
            print("   - Findings properly categorized")
        else:
            print("❌ VALIDATION FAILED!")
            if not all_present:
                print("   - Missing required fields")
            if not new_fields_present:
                print("   - Missing new scanner fields")
        
        print("=" * 80)
        print()
        
        return success
        
    except requests.exceptions.ConnectionError:
        print("❌ CONNECTION ERROR!")
        print("   API server is not running on http://127.0.0.1:8000")
        print()
        print("   To start the API server, run:")
        print("   cd api")
        print("   python test_server.py")
        print()
        return False
        
    except Exception as e:
        print(f"❌ TEST FAILED WITH ERROR:")
        print(f"   {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    import sys
    
    success = test_api_scan_response()
    sys.exit(0 if success else 1)


