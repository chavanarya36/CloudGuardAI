"""
Test all 3 prediction modes with REAL breached IaC files
These files are from actual repositories with security issues
"""
import os
import pytest
from pathlib import Path
try:
    from utils.multi_mode_predictor import MultiModePredictor
    from utils.feature_extractor import FeatureExtractor
except ImportError:
    pytest.skip("utils package not available", allow_module_level=True)

print("=" * 80)
print("🔥 TESTING WITH REAL BREACHED IaC FILES")
print("=" * 80)

# Initialize
fe = FeatureExtractor()

# Find real IaC files from breached repos
iac_full_dir = Path('iac_full')
test_files = []

# Collect sample files from each repository
for repo_dir in iac_full_dir.iterdir():
    if repo_dir.is_dir():
        # Find .tf, .yaml, .yml files
        for ext in ['*.tf', '*.yaml', '*.yml']:
            files = list(repo_dir.rglob(ext))
            if files:
                # Take first file from this repo
                test_files.append(files[0])
                break
        if len(test_files) >= 10:  # Test 10 files max
            break

print(f"\n📂 Found {len(test_files)} real breached files to test\n")

# Test each file with all 3 modes
results = []

for i, filepath in enumerate(test_files, 1):
    print(f"\n{'='*80}")
    print(f"📄 [{i}/{len(test_files)}] Testing: {filepath.name}")
    print(f"   Repository: {filepath.parts[-2]}")
    print(f"{'='*80}")
    
    try:
        # Read file
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        print(f"   Size: {len(content)} bytes")
        
        # Extract features
        X, feature_info = fe.extract_features_single(filepath.name, content)
        print(f"   Features extracted: {X.shape}")
        
        # Test all 3 modes
        file_results = {
            'file': str(filepath),
            'name': filepath.name,
            'repo': filepath.parts[-2],
            'size': len(content)
        }
        
        # Supervised
        try:
            predictor_sup = MultiModePredictor(mode='supervised')
            result_sup = predictor_sup.predict(X)
            sup_score = result_sup.get('risk_probability', 0) * 100
            file_results['supervised'] = sup_score
            print(f"   🎯 Supervised:    {sup_score:.1f}%")
        except Exception as e:
            print(f"   ❌ Supervised failed: {e}")
            file_results['supervised'] = None
        
        # Unsupervised
        try:
            predictor_unsup = MultiModePredictor(mode='unsupervised')
            result_unsup = predictor_unsup.predict(X)
            unsup_score = result_unsup.get('risk_probability', 0) * 100
            file_results['unsupervised'] = unsup_score
            print(f"   🔍 Unsupervised:  {unsup_score:.1f}%")
        except Exception as e:
            print(f"   ❌ Unsupervised failed: {e}")
            file_results['unsupervised'] = None
        
        # Hybrid
        try:
            predictor_hybrid = MultiModePredictor(mode='hybrid')
            result_hybrid = predictor_hybrid.predict(X)
            hybrid_score = result_hybrid.get('risk_probability', 0) * 100
            file_results['hybrid'] = hybrid_score
            print(f"   ⚡ Hybrid:        {hybrid_score:.1f}%")
        except Exception as e:
            print(f"   ❌ Hybrid failed: {e}")
            file_results['hybrid'] = None
        
        results.append(file_results)
        
    except Exception as e:
        print(f"   ❌ ERROR processing file: {e}")
        continue

# Summary
print("\n" + "=" * 80)
print("📊 SUMMARY: ALL 3 MODES ON REAL BREACHED FILES")
print("=" * 80)

if results:
    print(f"\n{'File':<40} {'Supervised':<12} {'Unsupervised':<14} {'Hybrid':<10}")
    print("-" * 80)
    
    for r in results:
        name = r['name'][:37] + '...' if len(r['name']) > 40 else r['name']
        sup = f"{r['supervised']:.1f}%" if r['supervised'] is not None else "FAILED"
        unsup = f"{r['unsupervised']:.1f}%" if r['unsupervised'] is not None else "FAILED"
        hyb = f"{r['hybrid']:.1f}%" if r['hybrid'] is not None else "FAILED"
        print(f"{name:<40} {sup:<12} {unsup:<14} {hyb:<10}")
    
    # Statistics
    sup_scores = [r['supervised'] for r in results if r['supervised'] is not None]
    unsup_scores = [r['unsupervised'] for r in results if r['unsupervised'] is not None]
    hybrid_scores = [r['hybrid'] for r in results if r['hybrid'] is not None]
    
    print("\n" + "-" * 80)
    print("📈 STATISTICS:")
    print("-" * 80)
    
    if sup_scores:
        print(f"🎯 Supervised:    Avg={sum(sup_scores)/len(sup_scores):.1f}%  Min={min(sup_scores):.1f}%  Max={max(sup_scores):.1f}%")
    if unsup_scores:
        print(f"🔍 Unsupervised:  Avg={sum(unsup_scores)/len(unsup_scores):.1f}%  Min={min(unsup_scores):.1f}%  Max={max(unsup_scores):.1f}%")
    if hybrid_scores:
        print(f"⚡ Hybrid:        Avg={sum(hybrid_scores)/len(hybrid_scores):.1f}%  Min={min(hybrid_scores):.1f}%  Max={max(hybrid_scores):.1f}%")
    
    print("\n" + "=" * 80)
    print("✅ TEST COMPLETE")
    print("=" * 80)
    
    # Key findings
    print("\n🔍 KEY FINDINGS:")
    high_risk_sup = sum(1 for s in sup_scores if s > 60)
    high_risk_unsup = sum(1 for s in unsup_scores if s > 60)
    high_risk_hybrid = sum(1 for s in hybrid_scores if s > 60)
    
    print(f"   • Supervised flagged {high_risk_sup}/{len(sup_scores)} files as HIGH RISK (>60%)")
    print(f"   • Unsupervised flagged {high_risk_unsup}/{len(unsup_scores)} files as HIGH RISK (>60%)")
    print(f"   • Hybrid flagged {high_risk_hybrid}/{len(hybrid_scores)} files as HIGH RISK (>60%)")
    
    # Compare modes
    if len(sup_scores) > 0 and len(unsup_scores) > 0:
        avg_diff = abs(sum(sup_scores)/len(sup_scores) - sum(unsup_scores)/len(unsup_scores))
        print(f"\n   💡 Average difference between Supervised & Unsupervised: {avg_diff:.1f}%")
        print(f"   {'✅ Modes give DIFFERENT predictions!' if avg_diff > 10 else '⚠️ Modes are very similar'}")

else:
    print("\n❌ No results to display")

print("\n")
