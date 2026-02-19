#!/usr/bin/env python3
"""
CloudGuard AI - Scan All Workspace IaC Files

Scans all IaC files found in the CloudGuardAI workspace
"""

import sys
import json
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, List
from collections import defaultdict

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from api.scanners.integrated_scanner import IntegratedSecurityScanner


def find_iac_files(workspace_root: Path) -> List[Path]:
    """Find all IaC files in the workspace"""
    
    print("Scanning workspace for IaC files...")
    
    iac_extensions = {'.tf', '.yaml', '.yml', '.json', '.template', '.hcl'}
    exclude_dirs = {'node_modules', '__pycache__', '.git', 'venv', '.venv', 'dist', 'build'}
    
    files = []
    for ext in iac_extensions:
        for file_path in workspace_root.rglob(f'*{ext}'):
            # Skip excluded directories
            if any(excluded in file_path.parts for excluded in exclude_dirs):
                continue
            files.append(file_path)
    
    print(f"✅ Found {len(files):,} IaC files")
    return files


def scan_all_files(files: List[Path], scanner: IntegratedSecurityScanner) -> Dict:
    """Scan all files with CloudGuard AI"""
    
    print(f"\n{'='*80}")
    print("SCANNING WORKSPACE IAC FILES WITH CLOUDGUARD AI")
    print(f"{'='*80}\n")
    
    results = {
        'files_scanned': 0,
        'files_with_findings': 0,
        'files_skipped': 0,
        'total_findings': 0,
        'scan_time_seconds': 0,
        'findings_by_scanner': defaultdict(int),
        'findings_by_severity': defaultdict(int),
        'file_results': []
    }
    
    start_time = time.time()
    last_update = start_time
    
    for idx, file_path in enumerate(files, 1):
        try:
            # Read file content
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            # Scan the file using integrated scanner
            scan_result = scanner.scan_file_integrated(str(file_path), content)
            
            # Extract all findings from all scanners
            all_findings = []
            for scanner_name, scanner_findings in scan_result.get('findings', {}).items():
                if scanner_findings:
                    for finding in scanner_findings:
                        finding['scanner'] = scanner_name
                        all_findings.append(finding)
            
            results['files_scanned'] += 1
            
            num_findings = len(all_findings)
            if num_findings > 0:
                results['files_with_findings'] += 1
                results['total_findings'] += num_findings
                
                # Count by scanner and severity
                for finding in all_findings:
                    scanner_name = finding.get('scanner', 'unknown')
                    severity = finding.get('severity', 'unknown')
                    results['findings_by_scanner'][scanner_name] += 1
                    results['findings_by_severity'][severity] += 1
            
            # Store result
            results['file_results'].append({
                'file_path': str(file_path.relative_to(Path(__file__).parent.parent.parent)),
                'num_findings': num_findings,
                'findings': all_findings
            })
            
        except Exception as e:
            print(f"  Error scanning {file_path.name}: {e}")
            results['files_skipped'] += 1
        
        # Progress update every 10 files or 30 seconds
        current_time = time.time()
        if idx % 10 == 0 or (current_time - last_update) > 30:
            elapsed = current_time - start_time
            rate = results['files_scanned'] / elapsed if elapsed > 0 else 0
            remaining = len(files) - idx
            eta = remaining / rate if rate > 0 else 0
            
            print(f"Progress: {idx}/{len(files)} files ({idx/len(files)*100:.1f}%) | "
                  f"Scanned: {results['files_scanned']} | "
                  f"Findings: {results['total_findings']} | "
                  f"Speed: {rate:.1f} files/sec | "
                  f"ETA: {eta/60:.1f} min")
            last_update = current_time
    
    results['scan_time_seconds'] = time.time() - start_time
    return results


def save_results(results: Dict, output_dir: Path):
    """Save results to JSON and CSV"""
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Save detailed JSON
    json_path = output_dir / f"cloudguard_workspace_scan_{timestamp}.json"
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"\n✅ JSON report: {json_path}")
    
    # Save CSV summary
    csv_path = output_dir / f"cloudguard_workspace_summary_{timestamp}.csv"
    with open(csv_path, 'w', encoding='utf-8', newline='') as f:
        f.write("file_path,num_findings,scanners,severities\n")
        for file_result in results['file_results']:
            scanners = set()
            severities = set()
            for finding in file_result.get('findings', []):
                scanners.add(finding.get('scanner', 'unknown'))
                severities.add(finding.get('severity', 'unknown'))
            
            f.write(f"{file_result['file_path']},{file_result['num_findings']},")
            f.write(f"\"{';'.join(sorted(scanners))}\",\"{';'.join(sorted(severities))}\"\n")
    
    print(f"✅ CSV summary: {csv_path}")


def print_final_summary(results: Dict):
    """Print final summary"""
    
    print(f"\n{'='*80}")
    print("CLOUDGUARD AI - WORKSPACE SCAN COMPLETE")
    print(f"{'='*80}\n")
    
    print(f"📊 SCAN STATISTICS")
    print(f"  Files scanned: {results['files_scanned']:,}")
    print(f"  Files skipped: {results['files_skipped']:,}")
    print(f"  Scan time: {results['scan_time_seconds']:.1f} seconds ({results['scan_time_seconds']/60:.1f} minutes)")
    
    if results['files_scanned'] > 0:
        print(f"  Speed: {results['files_scanned']/results['scan_time_seconds']:.2f} files/second")
        print(f"\n🔍 FINDINGS")
        print(f"  Total findings: {results['total_findings']:,}")
        print(f"  Files with findings: {results['files_with_findings']:,} ({results['files_with_findings']/results['files_scanned']*100:.1f}%)")
        print(f"  Average findings per file: {results['total_findings']/results['files_scanned']:.1f}")
    
    if results['findings_by_scanner']:
        print(f"\n📈 BY SCANNER")
        for scanner, count in sorted(results['findings_by_scanner'].items(), key=lambda x: x[1], reverse=True):
            pct = count / results['total_findings'] * 100 if results['total_findings'] > 0 else 0
            print(f"  {scanner:20s}: {count:6,} ({pct:5.1f}%)")
    
    if results['findings_by_severity']:
        print(f"\n⚠️  BY SEVERITY")
        severity_order = ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW', 'INFO']
        for severity in severity_order:
            if severity in results['findings_by_severity']:
                count = results['findings_by_severity'][severity]
                pct = count / results['total_findings'] * 100 if results['total_findings'] > 0 else 0
                print(f"  {severity:20s}: {count:6,} ({pct:5.1f}%)")
    
    print(f"\n{'='*80}\n")


def main():
    """Main execution"""
    
    # Paths
    project_root = Path(__file__).parent.parent.parent
    output_dir = project_root / "tests" / "validation" / "results"
    
    # Find all IaC files in workspace
    files = find_iac_files(project_root)
    
    if not files:
        print("❌ No IaC files found in workspace")
        return
    
    # Initialize scanner
    print("\nInitializing CloudGuard AI scanner...")
    scanner = IntegratedSecurityScanner()
    
    # Scan all files
    results = scan_all_files(files, scanner)
    
    # Save results
    save_results(results, output_dir)
    
    # Print final summary
    print_final_summary(results)


if __name__ == "__main__":
    main()
