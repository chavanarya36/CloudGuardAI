"""Test CVE scanner with vulnerable providers"""
import sys
sys.path.insert(0, 'd:/CloudGuardAI')

from api.scanners.cve_scanner import CVEScanner

# Test file with vulnerable providers
test_file = 'd:/CloudGuardAI/tests/validation/test_vulnerable_providers.tf'

with open(test_file, 'r') as f:
    content = f.read()

scanner = CVEScanner()
findings = scanner.scan_content(content, test_file)

print(f"\n{'='*70}")
print(f"🔍 CVE Scanner Test - Vulnerable Terraform Providers")
print(f"{'='*70}\n")
print(f"File: {test_file}")
print(f"Total Findings: {len(findings)}\n")

if findings:
    for i, finding in enumerate(findings, 1):
        print(f"{i}. {finding['title']}")
        print(f"   Severity: {finding['severity']} (CVSS: {finding['cvss_score']})")
        print(f"   Description: {finding['description']}")
        print(f"   Fix: Upgrade to {finding['fixed_version']}")
        print()
    print(f"✅ CVE Scanner Working! Found {len(findings)} vulnerabilities")
else:
    print("⚠️  No CVE findings (check provider extraction)")

print(f"\n{'='*70}\n")
