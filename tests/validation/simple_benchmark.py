"""
Simple benchmark comparison - CloudGuard AI vs Checkov
"""
import subprocess
import json
import time
from pathlib import Path

def run_checkov(test_path):
    """Run Checkov and return results"""
    print("\n🔍 Running Checkov...")
    try:
        start = time.time()
        result = subprocess.run(
            f'checkov -d "{test_path}" --quiet --compact --framework terraform',
            shell=True,
            capture_output=True,
            text=True,
            timeout=300
        )
        duration = time.time() - start
        
        # Count findings from output
        output = result.stdout + result.stderr
        failed_checks = output.count("Check:")
        passed_checks = output.count("Passed checks:")
        
        return {
            "tool": "Checkov",
            "duration": round(duration, 2),
            "findings": failed_checks,
            "status": "✅ Completed"
        }
    except subprocess.TimeoutExpired:
        return {"tool": "Checkov", "status": "❌ Timeout"}
    except Exception as e:
        return {"tool": "Checkov", "status": f"❌ Error: {e}"}

def main():
    terragoat_path = Path("tests/validation/terragoat")
    
    print("="*70)
    print("🏆 CloudGuard AI vs Checkov Benchmark")
    print("="*70)
    print(f"📁 Test Dataset: TerraGoat ({terragoat_path})")
    print(f"📊 Files: 47 Terraform files (AWS, Azure, GCP, Alicloud, Oracle)")
    print()
    
    # CloudGuard AI results (from previous validation)
    cloudguard = {
        "tool": "CloudGuard AI",
        "duration": 267.40,  # From validation test
        "findings": 230,  # 229 + 1 new CVE finding
        "breakdown": {
            "Secrets": 162,
            "Rules": 28,
            "ML": 27,
            "Compliance": 12,
            "CVE": 1,
            "LLM": 0
        },
        "ai_contribution": "24% (55 AI findings)",
        "status": "✅ Completed"
    }
    
    # Run Checkov
    checkov = run_checkov(terragoat_path)
    
    # Display results
    print("\n" + "="*70)
    print("📊 BENCHMARK RESULTS")
    print("="*70)
    print()
    
    print(f"CloudGuard AI:")
    print(f"  Status: {cloudguard['status']}")
    print(f"  Duration: {cloudguard['duration']}s (~5.7s per file)")
    print(f"  Total Findings: {cloudguard['findings']}")
    print(f"  AI Contribution: {cloudguard['ai_contribution']}")
    print(f"  Scanner Breakdown:")
    for scanner, count in cloudguard['breakdown'].items():
        print(f"    - {scanner}: {count}")
    print()
    
    print(f"Checkov:")
    print(f"  Status: {checkov['status']}")
    if 'duration' in checkov:
        print(f"  Duration: {checkov['duration']}s")
        print(f"  Total Findings: {checkov.get('findings', 'N/A')}")
    print()
    
    # Comparison
    print("="*70)
    print("🎯 KEY FINDINGS")
    print("="*70)
    print()
    print("✅ CloudGuard AI Advantages:")
    print("  - 24% AI-powered detection (ML + Rules scanners)")
    print("  - 230 total findings with 6 integrated scanners")
    print("  - Multi-scanner orchestration and risk aggregation")
    print("  - CVE scanner detected Terraform provider vulnerabilities")
    print()
    
    if 'findings' in checkov:
        if checkov['findings'] > cloudguard['findings']:
            print(f"✅ Checkov found {checkov['findings'] - cloudguard['findings']} additional policy violations")
        elif cloudguard['findings'] > checkov['findings']:
            print(f"✅ CloudGuard AI found {cloudguard['findings'] - checkov['findings']} more issues")
        
        if 'duration' in checkov and checkov['duration'] < cloudguard['duration']:
            speedup = round(cloudguard['duration'] / checkov['duration'], 1)
            print(f"⚡ Checkov {speedup}x faster")
        elif 'duration' in checkov:
            speedup = round(checkov['duration'] / cloudguard['duration'], 1)
            print(f"⚡ CloudGuard AI {speedup}x faster")
    
    print()
    print("="*70)
    
    # Save results
    results = {
        "cloudguard_ai": cloudguard,
        "checkov": checkov,
        "test_date": "2026-01-04",
        "test_dataset": "TerraGoat (47 files)"
    }
    
    output_file = Path("tests/validation/results/benchmark_comparison.json")
    output_file.parent.mkdir(exist_ok=True, parents=True)
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"💾 Results saved to: {output_file}")

if __name__ == "__main__":
    main()
