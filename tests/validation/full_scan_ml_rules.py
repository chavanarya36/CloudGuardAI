"""
Full workspace scan with all 6 scanners including ML and Rules
Scans all 135 IaC files
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "api"))

from api.scanners.integrated_scanner import IntegratedSecurityScanner
import json
from datetime import datetime

def find_iac_files(workspace_root):
    """Find all IaC files"""
    extensions = ['.tf', '.yaml', '.yml', '.json']
    files = []
    for ext in extensions:
        files.extend(workspace_root.rglob(f'*{ext}'))
    
    # Filter out common non-IaC files
    excluded = {'node_modules', '.git', '__pycache__', 'venv', '.venv', 'package-lock.json'}
    files = [f for f in files if not any(ex in str(f) for ex in excluded)]
    return files

def main():
    project_root = Path(__file__).parent.parent.parent
    
    print("=" * 80)
    print("CLOUDGUARD AI - FULL WORKSPACE SCAN (ALL 6 SCANNERS)")
    print("=" * 80)
    
    # Find files
    print("\nFinding IaC files...")
    files = find_iac_files(project_root)
    print(f"Found {len(files)} IaC files")
    
    # Initialize scanner
    print("\nInitializing scanner...")
    scanner = IntegratedSecurityScanner()
    
    # Scan all files
    all_findings = []
    scanner_counts = {
        'gnn': 0, 'secrets': 0, 'cve': 0, 'compliance': 0,
        'rules': 0, 'ml': 0, 'llm': 0
    }
    
    files_scanned = 0
    files_with_findings = 0
    files_with_ml = 0
    files_with_rules = 0
    
    print(f"\n{'=' * 80}")
    print(f"Scanning {len(files)} files...")
    print(f"{'=' * 80}\n")
    
    start_time = datetime.now()
    
    for i, file_path in enumerate(files, 1):
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            result = scanner.scan_file_integrated(str(file_path), content)
            files_scanned += 1
            
            has_findings = False
            for scanner_name in scanner_counts.keys():
                if scanner_name in result['findings']:
                    count = len(result['findings'][scanner_name])
                    scanner_counts[scanner_name] += count
                    if count > 0:
                        has_findings = True
                    
                    if scanner_name == 'ml' and count > 0:
                        files_with_ml += 1
                    if scanner_name == 'rules' and count > 0:
                        files_with_rules += 1
            
            if has_findings:
                files_with_findings += 1
            
            # Progress update every 10 files
            if i % 10 == 0:
                print(f"[{i}/{len(files)}] Scanned {file_path.name} - Total findings so far: {sum(scanner_counts.values())}")
            
            all_findings.extend(result.get('all_findings', []))
            
        except Exception as e:
            print(f"[{i}/{len(files)}] ERROR scanning {file_path.name}: {e}")
    
    scan_time = (datetime.now() - start_time).total_seconds()
    
    # Results
    print("\n" + "=" * 80)
    print("SCAN COMPLETE")
    print("=" * 80)
    
    print(f"\n📊 FILES:")
    print(f"   Total scanned: {files_scanned}")
    print(f"   With findings: {files_with_findings}")
    print(f"   Success rate: {files_with_findings/files_scanned*100:.1f}%")
    
    print(f"\n📊 FINDINGS:")
    print(f"   Total findings: {sum(scanner_counts.values()):,}")
    
    print(f"\n📊 PERFORMANCE:")
    print(f"   Scan time: {scan_time:.1f}s")
    print(f"   Speed: {files_scanned/scan_time:.2f} files/sec")
    
    print(f"\n📈 BY SCANNER:")
    for scanner, count in sorted(scanner_counts.items(), key=lambda x: x[1], reverse=True):
        if count > 0:
            pct = count / sum(scanner_counts.values()) * 100
            marker = "✅" if scanner in ['ml', 'rules'] else "  "
            print(f"{marker} {scanner:20s}: {count:6,} ({pct:5.1f}%)")
    
    # ML/Rules specific stats
    print("\n" + "=" * 80)
    print("ML + RULES SCANNER PERFORMANCE")
    print("=" * 80)
    
    print(f"\n✅ ML SCANNER:")
    print(f"   Files with ML findings: {files_with_ml}/{files_scanned} ({files_with_ml/files_scanned*100:.1f}%)")
    print(f"   Total ML findings: {scanner_counts['ml']}")
    print(f"   Status: {'OPERATIONAL' if scanner_counts['ml'] > 0 else 'NO FINDINGS'}")
    
    print(f"\n✅ RULES SCANNER:")
    print(f"   Files with Rules findings: {files_with_rules}/{files_scanned} ({files_with_rules/files_scanned*100:.1f}%)")
    print(f"   Total Rules findings: {scanner_counts['rules']}")
    print(f"   Status: {'OPERATIONAL' if scanner_counts['rules'] > 0 else 'NO FINDINGS'}")
    
    # Save results
    output_dir = project_root / "tests" / "validation" / "results"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_file = output_dir / f"full_scan_ml_rules_{timestamp}.json"
    
    results = {
        'timestamp': timestamp,
        'files_scanned': files_scanned,
        'files_with_findings': files_with_findings,
        'total_findings': sum(scanner_counts.values()),
        'scan_time_seconds': scan_time,
        'files_per_second': files_scanned / scan_time,
        'scanner_counts': scanner_counts,
        'ml_files': files_with_ml,
        'rules_files': files_with_rules
    }
    
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n💾 Results saved to: {results_file.name}")
    print("\n" + "=" * 80)

if __name__ == "__main__":
    main()
