#!/usr/bin/env python3
"""
Scan Downloaded IaC Files - Production Scanner

Scans all downloaded files and generates REAL findings report.
"""

import sys
import json
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, List

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from api.scanners.integrated_scanner import IntegratedSecurityScanner


def scan_downloaded_files(files_dir: Path) -> Dict:
    """Scan all downloaded files"""
    
    print(f"\n{'='*80}")
    print("SCANNING DOWNLOADED IAC FILES")
    print(f"{'='*80}")
    print(f"Directory: {files_dir}")
    
    # Get all files
    all_files = list(files_dir.glob("*"))
    if len(all_files) == 0:
        print("❌ No files found to scan!")
        return None
    
    print(f"Files found: {len(all_files)}")
    print(f"{'='*80}\n")
    
    # Initialize scanner
    scanner = IntegratedSecurityScanner()
    
    all_findings = []
    files_scanned = 0
    files_with_findings = 0
    errors = 0
    
    start_time = time.time()
    last_update = start_time
    
    for i, file_path in enumerate(all_files, 1):
        try:
            # Scan file
            findings = scanner.scan_file(str(file_path))
            files_scanned += 1
            
            if findings and len(findings) > 0:
                files_with_findings += 1
                all_findings.extend(findings)
            
            # Progress update every 100 files or 30 seconds
            current_time = time.time()
            if i % 100 == 0 or (current_time - last_update) > 30:
                elapsed = current_time - start_time
                rate = files_scanned / elapsed if elapsed > 0 else 0
                remaining = len(all_files) - files_scanned
                eta = remaining / rate if rate > 0 else 0
                
                print(f"Progress: {files_scanned}/{len(all_files)} files "
                      f"({files_scanned/len(all_files)*100:.1f}%) | "
                      f"{len(all_findings)} findings | "
                      f"{rate:.1f} files/sec | "
                      f"ETA: {eta/60:.0f}m")
                
                last_update = current_time
        
        except Exception as e:
            errors += 1
            if errors <= 10:  # Only print first 10 errors
                print(f"  Error scanning {file_path.name}: {e}")
    
    scan_time = time.time() - start_time
    
    # Analyze findings
    findings_by_scanner = {}
    findings_by_severity = {}
    findings_by_type = {}
    
    for finding in all_findings:
        scanner_name = finding.get('scanner', 'unknown')
        severity = finding.get('severity', 'unknown')
        finding_type = finding.get('type', 'unknown')
        
        findings_by_scanner[scanner_name] = findings_by_scanner.get(scanner_name, 0) + 1
        findings_by_severity[severity] = findings_by_severity.get(severity, 0) + 1
        findings_by_type[finding_type] = findings_by_type.get(finding_type, 0) + 1
    
    print(f"\n{'='*80}")
    print("SCAN COMPLETE!")
    print(f"{'='*80}")
    print(f"✅ Files scanned: {files_scanned:,}")
    print(f"✅ Files with findings: {files_with_findings:,} ({files_with_findings/files_scanned*100:.1f}%)")
    print(f"✅ Total findings: {len(all_findings):,}")
    print(f"⚠️  Scan errors: {errors}")
    print(f"⏱️  Time: {scan_time:.1f} seconds ({scan_time/60:.1f} minutes)")
    print(f"🚀 Speed: {files_scanned/scan_time:.1f} files/second")
    print(f"{'='*80}\n")
    
    print("📊 FINDINGS BREAKDOWN")
    print("-"*80)
    
    print("\nBy Scanner:")
    for scanner, count in sorted(findings_by_scanner.items(), key=lambda x: x[1], reverse=True):
        pct = count / len(all_findings) * 100 if all_findings else 0
        print(f"  {scanner:20s}: {count:6,} ({pct:5.1f}%)")
    
    print("\nBy Severity:")
    for severity, count in sorted(findings_by_severity.items(), key=lambda x: x[1], reverse=True):
        pct = count / len(all_findings) * 100 if all_findings else 0
        print(f"  {severity:20s}: {count:6,} ({pct:5.1f}%)")
    
    print("\nTop Finding Types:")
    for finding_type, count in sorted(findings_by_type.items(), key=lambda x: x[1], reverse=True)[:10]:
        pct = count / len(all_findings) * 100 if all_findings else 0
        print(f"  {finding_type[:40]:40s}: {count:6,} ({pct:5.1f}%)")
    
    print(f"\n{'='*80}\n")
    
    return {
        'files_scanned': files_scanned,
        'files_with_findings': files_with_findings,
        'total_findings': len(all_findings),
        'findings_per_file': len(all_findings) / files_scanned if files_scanned > 0 else 0,
        'scan_time_seconds': scan_time,
        'files_per_second': files_scanned / scan_time if scan_time > 0 else 0,
        'findings_by_scanner': findings_by_scanner,
        'findings_by_severity': findings_by_severity,
        'findings_by_type': findings_by_type,
        'all_findings': all_findings,
        'errors': errors
    }


def generate_report(scan_results: Dict, download_results: Dict):
    """Generate comprehensive report"""
    
    results_dir = Path(__file__).parent / "results"
    results_dir.mkdir(exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Phase 1 ML results (known)
    phase1_ml = {
        'files_scanned': 21000,
        'total_findings': 500,
        'findings_per_file': 0.024,
        'approach': 'ML-only'
    }
    
    # Calculate improvements
    improvement_factor = scan_results['total_findings'] / phase1_ml['total_findings'] if phase1_ml['total_findings'] > 0 else 0
    rate_improvement = scan_results['findings_per_file'] / phase1_ml['findings_per_file'] if phase1_ml['findings_per_file'] > 0 else 0
    
    # Projection to 21k
    if scan_results['files_scanned'] > 0:
        projected_21k = int((scan_results['findings_per_file'] / scan_results['files_scanned']) * 21000)
    else:
        projected_21k = 0
    
    report = {
        'report_metadata': {
            'generated_at': datetime.now().isoformat(),
            'report_type': 'REAL 21k Files Scan Results',
            'files_actually_scanned': scan_results['files_scanned']
        },
        'download_stats': download_results,
        'scan_results': scan_results,
        'phase1_ml_experiment': phase1_ml,
        'comparison': {
            'files_scanned_phase1': phase1_ml['files_scanned'],
            'files_scanned_phase2': scan_results['files_scanned'],
            'findings_phase1': phase1_ml['total_findings'],
            'findings_phase2': scan_results['total_findings'],
            'improvement_factor': improvement_factor,
            'rate_improvement': rate_improvement,
            'additional_findings': scan_results['total_findings'] - phase1_ml['total_findings']
        },
        'projection_to_21k': {
            'projected_findings': projected_21k,
            'improvement_vs_ml': projected_21k / phase1_ml['total_findings'] if phase1_ml['total_findings'] > 0 else 0
        }
    }
    
    # Save JSON
    json_path = results_dir / f"real_scan_results_{timestamp}.json"
    with open(json_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"✅ Report saved: {json_path}")
    
    # Save findings CSV
    import csv
    csv_path = results_dir / f"real_findings_{timestamp}.csv"
    
    if scan_results['all_findings']:
        with open(csv_path, 'w', newline='', encoding='utf-8') as f:
            if len(scan_results['all_findings']) > 0:
                fieldnames = scan_results['all_findings'][0].keys()
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(scan_results['all_findings'])
        
        print(f"✅ Findings CSV: {csv_path}")
    
    # Print summary
    print(f"\n{'='*80}")
    print("FINAL COMPARISON: PHASE 1 ML vs PHASE 2 CLOUDGUARD AI")
    print(f"{'='*80}")
    
    print(f"\nPhase 1: ML Experiment")
    print(f"  Files: {phase1_ml['files_scanned']:,}")
    print(f"  Findings: {phase1_ml['total_findings']:,}")
    print(f"  Rate: {phase1_ml['findings_per_file']:.3f} findings/file")
    
    print(f"\nPhase 2: CloudGuard AI (ACTUAL SCAN)")
    print(f"  Files: {scan_results['files_scanned']:,}")
    print(f"  Findings: {scan_results['total_findings']:,}")
    print(f"  Rate: {scan_results['findings_per_file']:.3f} findings/file")
    
    print(f"\nIMPROVEMENT")
    print(f"  Total Findings: {improvement_factor:.1f}x MORE")
    print(f"  Detection Rate: {rate_improvement:.0f}x BETTER")
    print(f"  Additional Findings: +{report['comparison']['additional_findings']:,}")
    
    print(f"\nPROJECTION TO 21k FILES")
    print(f"  Projected: {projected_21k:,} findings")
    print(f"  vs Phase 1 ML: {report['projection_to_21k']['improvement_vs_ml']:.1f}x improvement")
    
    print(f"\n{'='*80}")
    print("✅ THESE ARE REAL FINDINGS FROM ACTUAL SCANS!")
    print(f"{'='*80}\n")
    
    return report


def main():
    """Main execution"""
    
    # Check for downloaded files
    data_dir = Path(__file__).parent.parent.parent / "data"
    files_dir = data_dir / "downloaded_21k_files"
    progress_file = Path(__file__).parent / "download_progress.pkl"
    
    if not files_dir.exists() or len(list(files_dir.glob("*"))) == 0:
        print(f"❌ No downloaded files found in {files_dir}")
        print(f"\n   Please run robust_downloader.py first!")
        return
    
    # Load download stats if available
    download_results = {}
    if progress_file.exists():
        import pickle
        try:
            with open(progress_file, 'rb') as f:
                data = pickle.load(f)
                download_results = {
                    'files_downloaded': len(data.get('downloaded', {})),
                    'repos_processed': len(data.get('repos', set())),
                    'failed_downloads': len(data.get('failed', {}))
                }
        except:
            pass
    
    # Scan files
    scan_results = scan_downloaded_files(files_dir)
    
    if not scan_results:
        return
    
    # Generate report
    generate_report(scan_results, download_results)


if __name__ == "__main__":
    main()
