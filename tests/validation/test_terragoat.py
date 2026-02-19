"""
CloudGuard AI - TerraGoat Validation Test
Tests CloudGuard AI against deliberately vulnerable Terraform configurations
"""
import os
import sys
import json
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from api.scanners.integrated_scanner import IntegratedSecurityScanner


class TerraGoatValidator:
    """Validates CloudGuard AI against TerraGoat vulnerable configs"""
    
    def __init__(self, terragoat_path: str):
        self.terragoat_path = Path(terragoat_path)
        self.scanner = IntegratedSecurityScanner()
        self.results = {
            "metadata": {
                "test_date": datetime.utcnow().isoformat(),
                "tool": "CloudGuard AI",
                "version": "1.0.0",
                "test_suite": "TerraGoat"
            },
            "files_scanned": 0,
            "total_findings": 0,
            "findings_by_scanner": {},
            "findings_by_severity": {},
            "scan_duration_seconds": 0,
            "detailed_results": []
        }
    
    def find_terraform_files(self) -> List[Path]:
        """Find all .tf files in TerraGoat repository"""
        tf_files = []
        
        if not self.terragoat_path.exists():
            print(f"❌ TerraGoat path not found: {self.terragoat_path}")
            print(f"   Please clone TerraGoat first:")
            print(f"   git clone https://github.com/bridgecrewio/terragoat.git")
            return tf_files
        
        for tf_file in self.terragoat_path.rglob("*.tf"):
            # Skip .terraform directories
            if ".terraform" not in str(tf_file):
                tf_files.append(tf_file)
        
        return sorted(tf_files)
    
    def scan_file(self, file_path: Path) -> Dict[str, Any]:
        """Scan a single Terraform file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            print(f"  Scanning: {file_path.name}...", end=" ")
            start_time = time.time()
            
            result = self.scanner.scan_file_integrated(str(file_path), content)
            
            scan_time = time.time() - start_time
            
            # Get findings from the correct structure
            findings_dict = result.get('findings', {})
            finding_count = result.get('summary', {}).get('total_findings', 0)
            
            print(f"✓ ({finding_count} findings in {scan_time:.2f}s)")
            
            return {
                "file": str(file_path.relative_to(self.terragoat_path)),
                "scan_time": scan_time,
                "findings_count": finding_count,
                "result": result
            }
            
        except Exception as e:
            print(f"✗ Error: {str(e)}")
            return {
                "file": str(file_path.relative_to(self.terragoat_path)),
                "error": str(e),
                "findings_count": 0
            }
    
    def run_validation(self):
        """Run complete validation test"""
        print("\n" + "="*70)
        print("🧪 CloudGuard AI - TerraGoat Validation Test")
        print("="*70)
        
        # Find all Terraform files
        print(f"\n📁 Searching for Terraform files in: {self.terragoat_path}")
        tf_files = self.find_terraform_files()
        
        if not tf_files:
            print("❌ No Terraform files found!")
            return
        
        print(f"✓ Found {len(tf_files)} Terraform files\n")
        
        # Scan each file
        print("🔍 Scanning files...")
        print("-" * 70)
        
        start_time = time.time()
        
        for tf_file in tf_files:
            file_result = self.scan_file(tf_file)
            self.results["detailed_results"].append(file_result)
            self.results["files_scanned"] += 1
            
            # Aggregate findings by scanner
            if "result" in file_result:
                result_data = file_result["result"]
                findings_dict = result_data.get('findings', {})
                
                for scanner_type in ['secrets', 'cve', 'compliance', 'rules', 'ml', 'llm']:
                    findings = findings_dict.get(scanner_type, [])
                    if scanner_type not in self.results["findings_by_scanner"]:
                        self.results["findings_by_scanner"][scanner_type] = 0
                    self.results["findings_by_scanner"][scanner_type] += len(findings)
                    
                    # Count by severity
                    for finding in findings:
                        severity = finding.get('severity', 'UNKNOWN')
                        if severity not in self.results["findings_by_severity"]:
                            self.results["findings_by_severity"][severity] = 0
                        self.results["findings_by_severity"][severity] += 1
        
        self.results["scan_duration_seconds"] = time.time() - start_time
        self.results["total_findings"] = sum(self.results["findings_by_scanner"].values())
        
        # Print summary
        self.print_summary()
        
        # Save results
        self.save_results()
    
    def print_summary(self):
        """Print validation summary"""
        print("\n" + "="*70)
        print("📊 VALIDATION RESULTS SUMMARY")
        print("="*70)
        
        print(f"\n📁 Files Scanned: {self.results['files_scanned']}")
        print(f"⏱️  Total Scan Time: {self.results['scan_duration_seconds']:.2f} seconds")
        print(f"📈 Average Time per File: {self.results['scan_duration_seconds'] / max(self.results['files_scanned'], 1):.2f} seconds")
        
        print(f"\n🔍 Total Findings: {self.results['total_findings']}")
        
        print("\n📊 Findings by Scanner:")
        for scanner, count in sorted(self.results["findings_by_scanner"].items(), key=lambda x: x[1], reverse=True):
            percentage = (count / max(self.results['total_findings'], 1)) * 100
            print(f"   {scanner.upper():12} : {count:3} ({percentage:5.1f}%)")
        
        print("\n⚠️  Findings by Severity:")
        severity_order = ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW', 'INFO']
        for severity in severity_order:
            count = self.results["findings_by_severity"].get(severity, 0)
            if count > 0:
                percentage = (count / max(self.results['total_findings'], 1)) * 100
                print(f"   {severity:10} : {count:3} ({percentage:5.1f}%)")
        
        print("\n" + "="*70)
    
    def save_results(self):
        """Save results to JSON file"""
        output_dir = Path(__file__).parent / "results"
        output_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        output_file = output_dir / f"terragoat_validation_{timestamp}.json"
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, indent=2)
        
        print(f"\n💾 Results saved to: {output_file}")
        
        # Also save a summary CSV for easy comparison
        csv_file = output_dir / f"terragoat_summary_{timestamp}.csv"
        self.save_summary_csv(csv_file)
    
    def save_summary_csv(self, csv_file: Path):
        """Save summary in CSV format for comparison"""
        import csv
        
        with open(csv_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['Metric', 'Value'])
            writer.writerow(['Tool', 'CloudGuard AI'])
            writer.writerow(['Test Suite', 'TerraGoat'])
            writer.writerow(['Files Scanned', self.results['files_scanned']])
            writer.writerow(['Total Findings', self.results['total_findings']])
            writer.writerow(['Scan Duration (s)', f"{self.results['scan_duration_seconds']:.2f}"])
            writer.writerow(['Avg Time per File (s)', f"{self.results['scan_duration_seconds'] / max(self.results['files_scanned'], 1):.2f}"])
            writer.writerow([])
            writer.writerow(['Scanner Type', 'Findings'])
            for scanner, count in sorted(self.results["findings_by_scanner"].items()):
                writer.writerow([scanner.upper(), count])
            writer.writerow([])
            writer.writerow(['Severity', 'Count'])
            for severity in ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW', 'INFO']:
                count = self.results["findings_by_severity"].get(severity, 0)
                writer.writerow([severity, count])
        
        print(f"📊 Summary CSV saved to: {csv_file}")


def main():
    """Main validation test"""
    # Check if TerraGoat path provided
    if len(sys.argv) > 1:
        terragoat_path = sys.argv[1]
    else:
        # Default to tests/validation/terragoat
        terragoat_path = Path(__file__).parent / "terragoat"
    
    validator = TerraGoatValidator(terragoat_path)
    validator.run_validation()


if __name__ == "__main__":
    main()
