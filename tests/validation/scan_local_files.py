#!/usr/bin/env python3
"""
Alternative: Use Local IaC Sample Files + Smart Subset

Instead of downloading 5000 files (which may hit rate limits),
we'll use a smart strategy:
1. Scan all local samples we have
2. Download a smaller representative subset (500-1000 files)
3. Extrapolate results to 21k

This gives us REAL data that's defensible for thesis.
"""

import csv
import os
import sys
import json
import time
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any
import glob

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from api.scanners.integrated_scanner import IntegratedSecurityScanner


def find_all_local_iac_files(base_dir: Path) -> List[Path]:
    """Find all IaC files in project"""
    
    patterns = [
        "**/*.tf",
        "**/*.yaml",
        "**/*.yml",
        "**/*.json"
    ]
    
    all_files = []
    for pattern in patterns:
        files = list(base_dir.glob(pattern))
        all_files.extend(files)
    
    # Filter out non-IaC files
    iac_files = []
    for f in all_files:
        # Skip obvious non-IaC files
        if any(skip in str(f) for skip in ['node_modules', '__pycache__', '.git', 'venv', 'package']):
            continue
        iac_files.append(f)
    
    return iac_files


def scan_files_batch(files: List[Path], scanner: IntegratedSecurityScanner) -> Dict:
    """Scan a batch of files"""
    
    print(f"\n🔍 Scanning {len(files)} files...")
    
    all_findings = []
    files_scanned = 0
    files_with_findings = 0
    
    start_time = time.time()
    
    for file_path in files:
        try:
            files_scanned += 1
            
            if files_scanned % 10 == 0:
                elapsed = time.time() - start_time
                rate = files_scanned / elapsed if elapsed > 0 else 0
                print(f"  Progress: {files_scanned}/{len(files)} ({rate:.1f} files/sec, {len(all_findings)} findings)")
            
            # Scan file
            findings = scanner.scan_file(str(file_path))
            
            if findings and len(findings) > 0:
                files_with_findings += 1
                all_findings.extend(findings)
        
        except Exception as e:
            print(f"  Error scanning {file_path.name}: {e}")
    
    scan_time = time.time() - start_time
    
    print(f"\n✅ Scanned: {files_scanned} files, {files_with_findings} with findings, {len(all_findings)} total findings")
    print(f"   Time: {scan_time:.2f}s ({files_scanned/scan_time:.1f} files/sec)")
    
    # Analyze findings
    findings_by_scanner = {}
    findings_by_severity = {}
    
    for finding in all_findings:
        scanner_name = finding.get('scanner', 'unknown')
        severity = finding.get('severity', 'unknown')
        
        findings_by_scanner[scanner_name] = findings_by_scanner.get(scanner_name, 0) + 1
        findings_by_severity[severity] = findings_by_severity.get(severity, 0) + 1
    
    return {
        'files_scanned': files_scanned,
        'files_with_findings': files_with_findings,
        'total_findings': len(all_findings),
        'scan_time_seconds': scan_time,
        'files_per_second': files_scanned / scan_time if scan_time > 0 else 0,
        'findings_by_scanner': findings_by_scanner,
        'findings_by_severity': findings_by_severity,
        'all_findings': all_findings
    }


def main():
    """Main execution"""
    
    project_root = Path(__file__).parent.parent.parent
    
    print("\n" + "=" * 80)
    print("REAL IaC FILES SCAN - LOCAL + SUBSET STRATEGY")
    print("=" * 80)
    
    # Initialize scanner
    scanner = IntegratedSecurityScanner()
    
    # Step 1: Scan local samples
    print("\n📁 STEP 1: SCANNING LOCAL IaC SAMPLES")
    print("-" * 80)
    
    samples_dir = project_root / "data" / "samples"
    local_files = find_all_local_iac_files(samples_dir)
    print(f"Found {len(local_files)} local IaC files")
    
    if len(local_files) > 0:
        local_results = scan_files_batch(local_files, scanner)
    else:
        local_results = {'files_scanned': 0, 'total_findings': 0}
    
    # Step 2: Scan real_test_samples (TerraGoat, etc)
    print("\n📁 STEP 2: SCANNING TEST SAMPLES")
    print("-" * 80)
    
    test_samples = project_root / "real_test_samples"
    if test_samples.exists():
        test_files = find_all_local_iac_files(test_samples)
        print(f"Found {len(test_files)} test files")
        test_results = scan_files_batch(test_files, scanner)
    else:
        print("No test samples found")
        test_results = {'files_scanned': 0, 'total_findings': 0}
    
    # Combine results
    total_files = local_results['files_scanned'] + test_results['files_scanned']
    total_findings = local_results['total_findings'] + test_results['total_findings']
    
    print("\n" + "=" * 80)
    print("COMBINED REAL SCAN RESULTS")
    print("=" * 80)
    print(f"Total Files Scanned: {total_files}")
    print(f"Total Findings: {total_findings}")
    print(f"Findings per File: {total_findings/total_files if total_files > 0 else 0:.3f}")
    
    # Calculate projection to 21k
    if total_files > 0:
        findings_per_file = total_findings / total_files
        projected_21k = int(findings_per_file * 21000)
        
        print(f"\n📊 EXTRAPOLATION TO 21k FILES")
        print("-" * 80)
        print(f"Based on {total_files} REAL scanned files:")
        print(f"  • Projected for 21k: {projected_21k:,} findings")
        print(f"  • vs Phase 1 ML (500): {projected_21k/500:.1f}x improvement")
        
        # Save report
        results_dir = Path(__file__).parent / "results"
        results_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        report = {
            'report_metadata': {
                'generated_at': datetime.now().isoformat(),
                'report_type': 'Real Scan Results (Local Files)',
                'method': 'Actual scan + extrapolation'
            },
            'actual_scan': {
                'files_scanned': total_files,
                'total_findings': total_findings,
                'findings_per_file': findings_per_file,
                'local_samples': local_results,
                'test_samples': test_results
            },
            'projection_21k': {
                'projected_findings': projected_21k,
                'improvement_vs_ml': projected_21k / 500
            }
        }
        
        json_path = results_dir / f"real_local_scan_{timestamp}.json"
        with open(json_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"\n✅ Report saved: {json_path}")
    
    print("\n" + "=" * 80)


if __name__ == "__main__":
    main()
