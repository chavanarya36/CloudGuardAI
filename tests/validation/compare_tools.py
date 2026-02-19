"""
CloudGuard AI - Tool Comparison Script
Compares CloudGuard AI with Checkov, TFSec, and Terrascan
"""
import os
import sys
import json
import subprocess
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any


class ToolComparator:
    """Compare CloudGuard AI with other security scanning tools"""
    
    def __init__(self, test_path: str):
        self.test_path = Path(test_path)
        self.results = {
            "metadata": {
                "test_date": datetime.utcnow().isoformat(),
                "test_path": str(test_path)
            },
            "tools": {}
        }
    
    def check_tool_installed(self, tool_name: str, check_command: str) -> bool:
        """Check if a tool is installed"""
        try:
            subprocess.run(check_command, shell=True, capture_output=True, check=True)
            return True
        except:
            return False
    
    def run_cloudguard(self) -> Dict[str, Any]:
        """Run CloudGuard AI scan"""
        print("\n🔍 Running CloudGuard AI...")
        
        start_time = time.time()
        
        # Import and run CloudGuard
        sys.path.insert(0, str(Path(__file__).parent.parent.parent))
        from tests.validation.test_terragoat import TerraGoatValidator
        
        validator = TerraGoatValidator(self.test_path)
        tf_files = validator.find_terraform_files()
        
        total_findings = 0
        findings_by_severity = {}
        
        for tf_file in tf_files:
            file_result = validator.scan_file(tf_file)
            if "result" in file_result:
                result = file_result["result"]
                for scanner_type in ['secrets', 'cve', 'compliance', 'rules', 'ml', 'llm']:
                    findings = result.get(f'{scanner_type}_findings', [])
                    total_findings += len(findings)
                    for finding in findings:
                        severity = finding.get('severity', 'UNKNOWN')
                        findings_by_severity[severity] = findings_by_severity.get(severity, 0) + 1
        
        duration = time.time() - start_time
        
        return {
            "installed": True,
            "files_scanned": len(tf_files),
            "total_findings": total_findings,
            "findings_by_severity": findings_by_severity,
            "scan_duration": duration,
            "success": True
        }
    
    def run_checkov(self) -> Dict[str, Any]:
        """Run Checkov scan"""
        print("\n🔍 Running Checkov...")
        
        if not self.check_tool_installed("checkov", "checkov --version"):
            print("   ⚠️  Checkov not installed. Install with: pip install checkov")
            return {"installed": False, "success": False}
        
        try:
            start_time = time.time()
            
            result = subprocess.run(
                f"checkov -d {self.test_path} --output json --quiet",
                shell=True,
                capture_output=True,
                text=True
            )
            
            duration = time.time() - start_time
            
            # Parse Checkov output
            if result.stdout:
                checkov_data = json.loads(result.stdout)
                
                # Count findings
                total_findings = 0
                findings_by_severity = {}
                
                for check_result in checkov_data.get('results', {}).get('failed_checks', []):
                    total_findings += 1
                    severity = check_result.get('check_class', 'UNKNOWN')
                    findings_by_severity[severity] = findings_by_severity.get(severity, 0) + 1
                
                return {
                    "installed": True,
                    "total_findings": total_findings,
                    "findings_by_severity": findings_by_severity,
                    "scan_duration": duration,
                    "success": True
                }
        except Exception as e:
            print(f"   ✗ Error running Checkov: {e}")
            return {"installed": True, "success": False, "error": str(e)}
    
    def run_tfsec(self) -> Dict[str, Any]:
        """Run TFSec scan"""
        print("\n🔍 Running TFSec...")
        
        if not self.check_tool_installed("tfsec", "tfsec --version"):
            print("   ⚠️  TFSec not installed. Install from: https://github.com/aquasecurity/tfsec")
            return {"installed": False, "success": False}
        
        try:
            start_time = time.time()
            
            result = subprocess.run(
                f"tfsec {self.test_path} --format json",
                shell=True,
                capture_output=True,
                text=True
            )
            
            duration = time.time() - start_time
            
            # Parse TFSec output
            if result.stdout:
                tfsec_data = json.loads(result.stdout)
                
                total_findings = len(tfsec_data.get('results', []))
                findings_by_severity = {}
                
                for finding in tfsec_data.get('results', []):
                    severity = finding.get('severity', 'UNKNOWN')
                    findings_by_severity[severity] = findings_by_severity.get(severity, 0) + 1
                
                return {
                    "installed": True,
                    "total_findings": total_findings,
                    "findings_by_severity": findings_by_severity,
                    "scan_duration": duration,
                    "success": True
                }
        except Exception as e:
            print(f"   ✗ Error running TFSec: {e}")
            return {"installed": True, "success": False, "error": str(e)}
    
    def run_terrascan(self) -> Dict[str, Any]:
        """Run Terrascan"""
        print("\n🔍 Running Terrascan...")
        
        if not self.check_tool_installed("terrascan", "terrascan version"):
            print("   ⚠️  Terrascan not installed. Install from: https://github.com/tenable/terrascan")
            return {"installed": False, "success": False}
        
        try:
            start_time = time.time()
            
            result = subprocess.run(
                f"terrascan scan -d {self.test_path} -o json",
                shell=True,
                capture_output=True,
                text=True
            )
            
            duration = time.time() - start_time
            
            # Parse Terrascan output
            if result.stdout:
                terrascan_data = json.loads(result.stdout)
                
                violations = terrascan_data.get('results', {}).get('violations', [])
                total_findings = len(violations)
                findings_by_severity = {}
                
                for violation in violations:
                    severity = violation.get('severity', 'UNKNOWN')
                    findings_by_severity[severity] = findings_by_severity.get(severity, 0) + 1
                
                return {
                    "installed": True,
                    "total_findings": total_findings,
                    "findings_by_severity": findings_by_severity,
                    "scan_duration": duration,
                    "success": True
                }
        except Exception as e:
            print(f"   ✗ Error running Terrascan: {e}")
            return {"installed": True, "success": False, "error": str(e)}
    
    def run_comparison(self):
        """Run comparison across all tools"""
        print("\n" + "="*70)
        print("🏆 CloudGuard AI - Multi-Tool Comparison")
        print("="*70)
        print(f"\n📁 Test Path: {self.test_path}")
        
        # Run all tools
        self.results["tools"]["CloudGuard AI"] = self.run_cloudguard()
        self.results["tools"]["Checkov"] = self.run_checkov()
        self.results["tools"]["TFSec"] = self.run_tfsec()
        self.results["tools"]["Terrascan"] = self.run_terrascan()
        
        # Print comparison table
        self.print_comparison_table()
        
        # Save results
        self.save_results()
    
    def print_comparison_table(self):
        """Print comparison table"""
        print("\n" + "="*70)
        print("📊 COMPARISON RESULTS")
        print("="*70)
        
        print(f"\n{'Tool':<20} {'Installed':<12} {'Findings':<10} {'Time (s)':<10}")
        print("-" * 70)
        
        for tool_name, data in self.results["tools"].items():
            installed = "✓ Yes" if data.get("installed", False) else "✗ No"
            findings = data.get("total_findings", "N/A") if data.get("success", False) else "ERROR"
            duration = f"{data.get('scan_duration', 0):.2f}" if data.get("success", False) else "N/A"
            
            print(f"{tool_name:<20} {installed:<12} {findings:<10} {duration:<10}")
        
        print("\n" + "="*70)
        
        # Show which tool found the most
        successful_tools = {k: v for k, v in self.results["tools"].items() if v.get("success", False)}
        if successful_tools:
            best_tool = max(successful_tools.items(), key=lambda x: x[1].get("total_findings", 0))
            print(f"\n🏆 Most Findings: {best_tool[0]} ({best_tool[1]['total_findings']} findings)")
            
            fastest_tool = min(successful_tools.items(), key=lambda x: x[1].get("scan_duration", float('inf')))
            print(f"⚡ Fastest: {fastest_tool[0]} ({fastest_tool[1]['scan_duration']:.2f}s)")
    
    def save_results(self):
        """Save comparison results"""
        output_dir = Path(__file__).parent / "results"
        output_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        output_file = output_dir / f"tool_comparison_{timestamp}.json"
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, indent=2)
        
        print(f"\n💾 Results saved to: {output_file}")


def main():
    """Main comparison"""
    if len(sys.argv) > 1:
        test_path = sys.argv[1]
    else:
        test_path = Path(__file__).parent / "terragoat"
    
    comparator = ToolComparator(test_path)
    comparator.run_comparison()


if __name__ == "__main__":
    main()
