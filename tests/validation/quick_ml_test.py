"""
Quick ML + Rules Scanner Test
Scan just the sample files to verify ML scanner is working
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "api"))

from api.scanners.integrated_scanner import IntegratedSecurityScanner
import json
from datetime import datetime


def main():
    print("=" * 70)
    print("CLOUDGUARD AI - ML + RULES SCANNER TEST")
    print("=" * 70)
    
    # Sample IaC files directory
    samples_dir = project_root / "data" / "samples" / "iac_files"
    
    if not samples_dir.exists():
        print(f"\n❌ Samples directory not found: {samples_dir}")
        return
    
    # Get IaC files
    files = []
    for ext in ['.tf', '.yaml', '.yml', '.json']:
        files.extend(samples_dir.glob(f'*{ext}'))
    
    print(f"\n📁 Found {len(files)} IaC files in {samples_dir.name}/")
    
    # Initialize scanner
    print("\n🔧 Initializing IntegratedSecurityScanner...")
    scanner = IntegratedSecurityScanner()
    
    # Scan results
    all_findings = []
    scanner_counts = {
        'gnn': 0,
        'secrets': 0,
        'cve': 0,
        'compliance': 0,
        'rules': 0,
        'ml': 0,
        'llm': 0
    }
    
    files_scanned = 0
    files_with_ml = 0
    files_with_rules = 0
    
    print("\n🔍 Scanning files with all 6 scanners (including ML + Rules)...\n")
    
    for file_path in files[:10]:  # Scan first 10 files for quick test
        files_scanned += 1
        print(f"[{files_scanned}/10] Scanning: {file_path.name}")
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Scan with integrated scanner (all 6 scanners)
            result = scanner.scan_file_integrated(
                file_path=str(file_path),
                content=content
            )
            
            # Count findings by scanner
            for scanner_name in scanner_counts.keys():
                if scanner_name in result['findings']:
                    count = len(result['findings'][scanner_name])
                    scanner_counts[scanner_name] += count
                    
                    if scanner_name == 'ml' and count > 0:
                        files_with_ml += 1
                        print(f"  ✅ ML Scanner: {count} findings")
                    
                    if scanner_name == 'rules' and count > 0:
                        files_with_rules += 1
                        print(f"  ✅ Rules Scanner: {count} findings")
            
            # Collect all findings
            all_findings.extend(result.get('all_findings', []))
            
        except Exception as e:
            print(f"  ❌ Error: {e}")
    
    # Results Summary
    print("\n" + "=" * 70)
    print("SCAN COMPLETE - RESULTS SUMMARY")
    print("=" * 70)
    
    print(f"\n📊 Files Scanned: {files_scanned}")
    print(f"📊 Total Findings: {len(all_findings)}")
    
    print(f"\n📈 Findings by Scanner:")
    for scanner, count in sorted(scanner_counts.items(), key=lambda x: x[1], reverse=True):
        if count > 0:
            pct = (count / len(all_findings) * 100) if len(all_findings) > 0 else 0
            status = "✅" if scanner in ['ml', 'rules'] else "  "
            print(f"{status} {scanner:20s}: {count:6,} ({pct:5.1f}%)")
    
    # ML Scanner Status
    print("\n" + "=" * 70)
    print("ML SCANNER STATUS")
    print("=" * 70)
    
    if scanner_counts['ml'] > 0:
        print(f"✅ ML Scanner: WORKING")
        print(f"   - Files with ML findings: {files_with_ml}/{files_scanned}")
        print(f"   - Total ML findings: {scanner_counts['ml']}")
        print(f"   - ML service connection: SUCCESS")
    else:
        print(f"⚠️  ML Scanner: No findings detected")
        print(f"   - This might mean:")
        print(f"     1. ML service not responding")
        print(f"     2. No files exceeded risk threshold (>0.4)")
        print(f"     3. Connection timeout issues")
    
    # Rules Scanner Status
    if scanner_counts['rules'] > 0:
        print(f"\n✅ Rules Scanner: WORKING")
        print(f"   - Files with Rules findings: {files_with_rules}/{files_scanned}")
        print(f"   - Total Rules findings: {scanner_counts['rules']}")
    else:
        print(f"\n⚠️  Rules Scanner: No findings detected")
    
    # Show sample ML finding if any
    ml_findings = [f for f in all_findings if f.get('scanner') == 'ml']
    if ml_findings:
        print("\n" + "=" * 70)
        print("SAMPLE ML FINDING")
        print("=" * 70)
        sample = ml_findings[0]
        print(f"File: {sample.get('file', 'unknown')}")
        print(f"Severity: {sample.get('severity', 'unknown')}")
        print(f"Risk Score: {sample.get('risk_score', 0):.2f}")
        print(f"Confidence: {sample.get('confidence', 0):.2f}")
        print(f"Description: {sample.get('description', 'N/A')}")
    
    print("\n" + "=" * 70)
    print("✅ TEST COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    main()
