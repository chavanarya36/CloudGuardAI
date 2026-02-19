#!/usr/bin/env python3
"""
CloudGuard AI - Scan 21k IaC Files Dataset

This script scans all files from the iac_labels_clean.csv dataset
using CloudGuard AI's IntegratedSecurityScanner and compares results
with existing labels.
"""

import sys
import csv
import json
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, List
from collections import defaultdict

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from api.scanners.integrated_scanner import IntegratedSecurityScanner


def load_dataset(csv_path: Path) -> List[Dict]:
    """Load the IaC labels dataset"""
    
    print(f"Loading dataset from {csv_path}...")
    
    files = []
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Fix file paths - they should be in data/samples/iac_subset
            abs_path = row.get('abs_path', '')
            if abs_path:
                # Normalize path separators and fix the base directory
                abs_path = abs_path.replace('d:/CloudGuardAI/iac_subset/', 'd:/CloudGuardAI/data/samples/iac_subset/')
                abs_path = abs_path.replace('d:\\CloudGuardAI\\iac_subset\\', 'd:\\CloudGuardAI\\data\\samples\\iac_subset\\')
                abs_path = abs_path.replace('/', '\\')  # Windows path normalization
                row['abs_path'] = abs_path
            files.append(row)
    
    print(f"✅ Loaded {len(files):,} file records")
    return files


def scan_all_files(dataset: List[Dict], scanner: IntegratedSecurityScanner) -> Dict:
    """Scan all files in the dataset"""
    
    print(f"\n{'='*80}")
    print("SCANNING 21K IAC FILES WITH CLOUDGUARD AI")
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
    
    for idx, file_record in enumerate(dataset, 1):
        abs_path = file_record.get('abs_path', '')
        
        # Check if file exists
        file_path = Path(abs_path)
        if not file_path.exists():
            results['files_skipped'] += 1
            continue
        
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
                'abs_path': abs_path,
                'rel_path': file_record.get('rel_path', ''),
                'ext': file_record.get('ext', ''),
                'ground_truth_has_findings': int(file_record.get('has_findings', 0)),
                'ground_truth_num_findings': int(file_record.get('num_findings', 0)),
                'cloudguard_num_findings': num_findings,
                'cloudguard_has_findings': 1 if num_findings > 0 else 0,
                'findings': all_findings if all_findings else []
            })
            
        except Exception as e:
            print(f"  Error scanning {file_path.name}: {e}")
            results['files_skipped'] += 1
        
        # Progress update every 100 files or 30 seconds
        current_time = time.time()
        if idx % 100 == 0 or (current_time - last_update) > 30:
            elapsed = current_time - start_time
            rate = results['files_scanned'] / elapsed if elapsed > 0 else 0
            remaining = len(dataset) - idx
            eta = remaining / rate if rate > 0 else 0
            
            print(f"Progress: {idx}/{len(dataset)} ({idx/len(dataset)*100:.1f}%) | "
                  f"Scanned: {results['files_scanned']} | "
                  f"Findings: {results['total_findings']} | "
                  f"Rate: {rate:.1f} files/sec | "
                  f"ETA: {eta/60:.1f}m")
            
            last_update = current_time
    
    results['scan_time_seconds'] = time.time() - start_time
    
    return results


def calculate_metrics(results: Dict) -> Dict:
    """Calculate performance metrics comparing CloudGuard vs ground truth"""
    
    print(f"\n{'='*80}")
    print("CALCULATING METRICS")
    print(f"{'='*80}\n")
    
    tp = 0  # True Positive: CloudGuard found, ground truth has
    fp = 0  # False Positive: CloudGuard found, ground truth doesn't have
    tn = 0  # True Negative: CloudGuard didn't find, ground truth doesn't have
    fn = 0  # False Negative: CloudGuard didn't find, ground truth has
    
    for file_result in results['file_results']:
        cg_has = file_result['cloudguard_has_findings']
        gt_has = file_result['ground_truth_has_findings']
        
        if cg_has == 1 and gt_has == 1:
            tp += 1
        elif cg_has == 1 and gt_has == 0:
            fp += 1
        elif cg_has == 0 and gt_has == 0:
            tn += 1
        elif cg_has == 0 and gt_has == 1:
            fn += 1
    
    # Calculate metrics
    accuracy = (tp + tn) / (tp + fp + tn + fn) if (tp + fp + tn + fn) > 0 else 0
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0
    f1_score = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
    
    metrics = {
        'true_positives': tp,
        'false_positives': fp,
        'true_negatives': tn,
        'false_negatives': fn,
        'accuracy': accuracy,
        'precision': precision,
        'recall': recall,
        'f1_score': f1_score
    }
    
    print(f"True Positives:  {tp:,}")
    print(f"False Positives: {fp:,}")
    print(f"True Negatives:  {tn:,}")
    print(f"False Negatives: {fn:,}")
    print(f"\nAccuracy:  {accuracy:.3f}")
    print(f"Precision: {precision:.3f}")
    print(f"Recall:    {recall:.3f}")
    print(f"F1 Score:  {f1_score:.3f}")
    
    return metrics


def save_results(results: Dict, metrics: Dict, output_dir: Path):
    """Save results to files"""
    
    output_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Save JSON report
    report = {
        'scan_metadata': {
            'timestamp': datetime.now().isoformat(),
            'files_scanned': results['files_scanned'],
            'scan_time_seconds': results['scan_time_seconds'],
            'files_per_second': results['files_scanned'] / results['scan_time_seconds'] if results['scan_time_seconds'] > 0 else 0
        },
        'findings_summary': {
            'total_findings': results['total_findings'],
            'files_with_findings': results['files_with_findings'],
            'findings_by_scanner': dict(results['findings_by_scanner']),
            'findings_by_severity': dict(results['findings_by_severity'])
        },
        'performance_metrics': metrics,
        'file_results': results['file_results']
    }
    
    json_path = output_dir / f"cloudguard_21k_scan_{timestamp}.json"
    with open(json_path, 'w') as f:
        json.dump(report, f, indent=2)
    print(f"\n✅ JSON report: {json_path}")
    
    # Save CSV summary
    csv_path = output_dir / f"cloudguard_21k_summary_{timestamp}.csv"
    with open(csv_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=[
            'abs_path', 'rel_path', 'ext',
            'ground_truth_has_findings', 'ground_truth_num_findings',
            'cloudguard_has_findings', 'cloudguard_num_findings'
        ])
        writer.writeheader()
        for result in results['file_results']:
            writer.writerow({
                'abs_path': result['abs_path'],
                'rel_path': result['rel_path'],
                'ext': result['ext'],
                'ground_truth_has_findings': result['ground_truth_has_findings'],
                'ground_truth_num_findings': result['ground_truth_num_findings'],
                'cloudguard_has_findings': result['cloudguard_has_findings'],
                'cloudguard_num_findings': result['cloudguard_num_findings']
            })
    print(f"✅ CSV summary: {csv_path}")
    
    return json_path, csv_path


def print_final_summary(results: Dict, metrics: Dict):
    """Print final summary"""
    
    print(f"\n{'='*80}")
    print("CLOUDGUARD AI - 21K FILES SCAN COMPLETE")
    print(f"{'='*80}\n")
    
    print(f"📊 SCAN STATISTICS")
    print(f"  Files scanned: {results['files_scanned']:,}")
    print(f"  Files skipped: {results['files_skipped']:,}")
    print(f"  Scan time: {results['scan_time_seconds']:.1f} seconds ({results['scan_time_seconds']/60:.1f} minutes)")
    
    if results['files_scanned'] > 0:
        print(f"  Speed: {results['files_scanned']/results['scan_time_seconds']:.1f} files/second")
    
    print(f"\n🔍 FINDINGS")
    print(f"  Total findings: {results['total_findings']:,}")
    
    if results['files_scanned'] > 0:
        print(f"  Files with findings: {results['files_with_findings']:,} ({results['files_with_findings']/results['files_scanned']*100:.1f}%)")
    else:
        print(f"  Files with findings: 0 (0.0%)")
    
    print(f"\n📈 BY SCANNER")
    for scanner, count in sorted(results['findings_by_scanner'].items(), key=lambda x: x[1], reverse=True):
        pct = count / results['total_findings'] * 100 if results['total_findings'] > 0 else 0
        print(f"  {scanner:20s}: {count:6,} ({pct:5.1f}%)")
    
    print(f"\n⚠️  BY SEVERITY")
    for severity, count in sorted(results['findings_by_severity'].items(), key=lambda x: x[1], reverse=True):
        pct = count / results['total_findings'] * 100 if results['total_findings'] > 0 else 0
        print(f"  {severity:20s}: {count:6,} ({pct:5.1f}%)")
    
    print(f"\n✅ PERFORMANCE vs GROUND TRUTH")
    print(f"  Accuracy:  {metrics['accuracy']:.1%}")
    print(f"  Precision: {metrics['precision']:.1%}")
    print(f"  Recall:    {metrics['recall']:.1%}")
    print(f"  F1 Score:  {metrics['f1_score']:.3f}")
    
    print(f"\n{'='*80}\n")


def main():
    """Main execution"""
    
    # Paths
    project_root = Path(__file__).parent.parent.parent
    csv_path = project_root / "data" / "labels_artifacts" / "iac_labels_clean.csv"
    output_dir = project_root / "tests" / "validation" / "results"
    
    if not csv_path.exists():
        print(f"❌ Dataset not found: {csv_path}")
        return
    
    # Load dataset
    dataset = load_dataset(csv_path)
    
    # LIMIT TO FIRST 1000 FILES FOR SPEED
    print(f"\n⚡ Limiting to first 1000 files for faster results...")
    dataset = dataset[:1000]
    print(f"✅ Processing {len(dataset):,} files\n")
    
    # Initialize scanner
    print("Initializing CloudGuard AI scanner...")
    scanner = IntegratedSecurityScanner()
    
    # Scan all files
    results = scan_all_files(dataset, scanner)
    
    # Calculate metrics
    metrics = calculate_metrics(results)
    
    # Save results
    save_results(results, metrics, output_dir)
    
    # Print final summary
    print_final_summary(results, metrics)


if __name__ == "__main__":
    main()
