"""
CloudGuard AI - Full Validation Test (ALL 6 Scanners)
Tests against TerraGoat with complete ML/LLM/Rules integration via API
"""

import requests
import json
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, List
import time


class FullCloudGuardValidator:
    """Validates CloudGuard AI with ALL 6 scanners via API"""
    
    def __init__(self, api_url: str = "http://localhost:8000"):
        self.api_url = api_url
        self.results_dir = Path(__file__).parent / "results"
        self.results_dir.mkdir(exist_ok=True)
        
    def check_services(self) -> bool:
        """Check if all required services are running"""
        print("\nChecking CloudGuard AI services...")
        
        try:
            # Check main API
            response = requests.get(f"{self.api_url}/health", timeout=5)
            if response.status_code != 200:
                print("X Main API not running at", self.api_url)
                print("   Start with: cd api && uvicorn app.main:app --reload")
                return False
            print("+ Main API running")
            
            # Check ML service (optional - endpoint might be different)
            try:
                ml_response = requests.get(f"{self.api_url}/ml/health", timeout=5)
                if ml_response.status_code == 200:
                    print("+ ML service running")
                else:
                    print("! ML service not responding (scans will use fallback)")
            except:
                print("! ML service not available (scans will use fallback)")
            
            return True
            
        except requests.ConnectionError:
            print("X Cannot connect to CloudGuard AI API")
            print(f"   Make sure services are running at {self.api_url}")
            print("\n   Start services:")
            print("   1. cd api && uvicorn app.main:app --reload")
            print("   2. cd ml/ml_service && python main.py (optional)")
            return False
    
    def scan_file_full(self, file_path: Path) -> Dict:
        """
        Scan a file using the FULL CloudGuard AI stack
        This calls the /scan endpoint which runs ALL 6 scanners
        """
        print(f"  Scanning: {file_path.name}...", end=" ")
        
        try:
            with open(file_path, 'rb') as f:
                files = {'file': (file_path.name, f, 'text/plain')}
                
                start_time = time.time()
                response = requests.post(
                    f"{self.api_url}/scan",
                    files=files,
                    timeout=120  # LLM can take time
                )
                scan_time = time.time() - start_time
                
                if response.status_code != 200:
                    print(f"X Scan failed: {response.status_code}")
                    return None
                
                result = response.json()
                
                # Extract findings from all scanners
                total_findings = sum([
                    len(result.get('secrets_findings', [])),
                    len(result.get('cve_findings', [])),
                    len(result.get('compliance_findings', [])),
                    len(result.get('rules_findings', [])),
                    len(result.get('ml_findings', [])),
                    len(result.get('llm_findings', []))
                ])
                
                print(f"+ {total_findings} issues in {scan_time:.2f}s")
                
                return {
                    'file': str(file_path.relative_to(file_path.parent.parent)),
                    'scan_time': scan_time,
                    'total_findings': total_findings,
                    'result': result
                }
                
        except requests.Timeout:
            print(f"X Timeout after 120s")
            return None
        except Exception as e:
            print(f"X Error: {e}")
            return None
    
    def scan_directory(self, directory: Path) -> List[Dict]:
        """Scan all Terraform files in directory"""
        tf_files = list(directory.rglob("*.tf"))
        tf_files = [f for f in tf_files if ".terraform" not in str(f)]
        
        print(f"\nFound {len(tf_files)} Terraform files in {directory.name}")
        print("=" * 70)
        
        results = []
        for i, tf_file in enumerate(tf_files, 1):
            print(f"[{i}/{len(tf_files)}] ", end="")
            result = self.scan_file_full(tf_file)
            if result:
                results.append(result)
            
            # Small delay to not overwhelm the API
            if i < len(tf_files):
                time.sleep(0.1)
        
        return results
    
    def aggregate_results(self, scan_results: List[Dict]) -> Dict:
        """Aggregate results across all scans"""
        
        # Initialize counters
        total_findings = {
            'secrets': 0,
            'cve': 0,
            'compliance': 0,
            'rules': 0,
            'ml': 0,
            'llm': 0
        }
        
        severity_counts = {
            'CRITICAL': 0,
            'HIGH': 0,
            'MEDIUM': 0,
            'LOW': 0,
            'INFO': 0
        }
        
        all_findings = []
        total_scan_time = 0
        
        # Aggregate
        for scan in scan_results:
            result = scan['result']
            total_scan_time += scan['scan_time']
            
            # Count by scanner
            for scanner_type in total_findings.keys():
                findings_key = f"{scanner_type}_findings"
                findings = result.get(findings_key, [])
                total_findings[scanner_type] += len(findings)
                
                # Collect all findings with scanner type
                for finding in findings:
                    finding['scanner'] = scanner_type
                    finding['file'] = scan['file']
                    all_findings.append(finding)
                    
                    # Count severity
                    severity = finding.get('severity', 'INFO').upper()
                    if severity in severity_counts:
                        severity_counts[severity] += 1
        
        # Calculate percentages
        total = sum(total_findings.values())
        scanner_percentages = {
            scanner: (count / total * 100) if total > 0 else 0
            for scanner, count in total_findings.items()
        }
        
        return {
            'total_files_scanned': len(scan_results),
            'total_scan_time': total_scan_time,
            'avg_time_per_file': total_scan_time / len(scan_results) if scan_results else 0,
            'total_findings': total,
            'findings_by_scanner': total_findings,
            'scanner_percentages': scanner_percentages,
            'findings_by_severity': severity_counts,
            'all_findings': all_findings
        }
    
    def generate_report(self, summary: Dict, output_name: str = "full_validation"):
        """Generate comprehensive validation report"""
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save detailed JSON
        json_file = self.results_dir / f"{output_name}_{timestamp}.json"
        with open(json_file, 'w') as f:
            json.dump(summary, f, indent=2, default=str)
        
        print(f"\n+ Detailed results: {json_file}")
        
        # Generate markdown report
        md_file = self.results_dir / f"{output_name}_{timestamp}.md"
        
        with open(md_file, 'w') as f:
            f.write(f"# CloudGuard AI - Full Validation Report\n\n")
            f.write(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write(f"## Overview\n\n")
            f.write(f"- **Files Scanned:** {summary['total_files_scanned']}\n")
            f.write(f"- **Total Findings:** {summary['total_findings']}\n")
            f.write(f"- **Total Scan Time:** {summary['total_scan_time']:.2f}s\n")
            f.write(f"- **Avg Time/File:** {summary['avg_time_per_file']:.3f}s\n\n")
            
            f.write(f"## Scanner Breakdown\n\n")
            f.write(f"| Scanner | Findings | Percentage |\n")
            f.write(f"|---------|----------|------------|\n")
            
            for scanner, count in summary['findings_by_scanner'].items():
                pct = summary['scanner_percentages'][scanner]
                f.write(f"| {scanner.upper()} | {count} | {pct:.1f}% |\n")
            
            f.write(f"\n## Severity Distribution\n\n")
            f.write(f"| Severity | Count | Percentage |\n")
            f.write(f"|----------|-------|------------|\n")
            
            total = summary['total_findings']
            for severity, count in summary['findings_by_severity'].items():
                pct = (count / total * 100) if total > 0 else 0
                f.write(f"| {severity} | {count} | {pct:.1f}% |\n")
        
        print(f"+ Summary report: {md_file}")
        
        return json_file, md_file
    
    def print_summary(self, summary: Dict):
        """Print beautiful console summary"""
        
        print("\n" + "=" * 70)
        print("CloudGuard AI - FULL VALIDATION COMPLETE!")
        print("=" * 70)
        
        print(f"\nSCAN STATISTICS:")
        print(f"   Files Scanned    : {summary['total_files_scanned']}")
        print(f"   Total Findings   : {summary['total_findings']}")
        print(f"   Scan Time        : {summary['total_scan_time']:.2f}s")
        print(f"   Avg Time/File    : {summary['avg_time_per_file']:.3f}s")
        
        print(f"\nSCANNER BREAKDOWN:")
        for scanner, count in summary['findings_by_scanner'].items():
            pct = summary['scanner_percentages'][scanner]
            print(f"   {scanner.upper():12} : {count:3} ({pct:5.1f}%)")
        
        print(f"\nSEVERITY DISTRIBUTION:")
        total = summary['total_findings']
        for severity in ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW', 'INFO']:
            count = summary['findings_by_severity'].get(severity, 0)
            pct = (count / total * 100) if total > 0 else 0
            print(f"   {severity:8} : {count:3} ({pct:5.1f}%)")
        
        # Check AI/ML contribution
        ml_findings = summary['findings_by_scanner']['ml']
        llm_findings = summary['findings_by_scanner']['llm']
        ai_total = ml_findings + llm_findings
        ai_pct = (ai_total / total * 100) if total > 0 else 0
        
        print("\n" + "=" * 70)
        
        if ai_total > 0:
            print(f"\n+ AI/ML Detection Working!")
            print(f"   ML Scanner   : {ml_findings} findings")
            print(f"   LLM Scanner  : {llm_findings} findings")
            print(f"   AI Contribution: {ai_pct:.1f}%")
        else:
            print(f"\n! WARNING: ML and LLM scanners returned 0 findings!")
            print("   This indicates AI/ML services may not be fully integrated.")
            print("   Your project's main differentiator is not being demonstrated!")
            print("\n   To fix:")
            print("   1. Ensure ML service is running")
            print("   2. Check ML models are trained")
            print("   3. Verify /scan endpoint calls ML/LLM scanners")


def main():
    """Run full validation test"""
    
    print("=" * 70)
    print("CloudGuard AI - Full Validation Test (ALL 6 Scanners)")
    print("=" * 70)
    
    validator = FullCloudGuardValidator()
    
    # Check if services are running
    if not validator.check_services():
        print("\nX Services not running. Please start them first.")
        print("\nQuick Start:")
        print("  Terminal 1: cd api && uvicorn app.main:app --reload")
        print("  Terminal 2: cd ml/ml_service && python main.py")
        return
    
    # Find TerraGoat directory
    terragoat_dir = Path(__file__).parent / "terragoat"
    
    if not terragoat_dir.exists():
        print(f"\nX TerraGoat not found at {terragoat_dir}")
        print("   Run setup first: .\\tests\\validation\\setup_validation.ps1")
        return
    
    # Scan all files
    print(f"\nStarting full validation against TerraGoat...")
    print("(This may take a few minutes due to ML/LLM processing)")
    scan_results = validator.scan_directory(terragoat_dir)
    
    if not scan_results:
        print("\nX No results obtained")
        return
    
    # Aggregate results
    print("\nAggregating results...")
    summary = validator.aggregate_results(scan_results)
    
    # Generate reports
    print("\nGenerating reports...")
    validator.generate_report(summary, "terragoat_full_validation")
    
    # Print summary
    validator.print_summary(summary)


if __name__ == "__main__":
    main()
