"""
Test if supervised model gives DIFFERENT predictions for different files
"""
import pytest
try:
    from utils.prediction_engine import PredictionEngine
except ImportError:
    pytest.skip("utils package not available", allow_module_level=True)

from pathlib import Path

print("="*70)
print("🔍 TESTING IF SUPERVISED MODEL GIVES VARIED PREDICTIONS")
print("="*70)

# Initialize engine
engine = PredictionEngine()

# Test files
test_files = [
    ("HIGH_risk.tf", "iac_files/HIGH_risk.tf"),
    ("LOW_risk.tf", "iac_files/LOW_risk.tf"),
    ("MEDIUM_risk.tf", "iac_files/MEDIUM_risk.tf"),
]

results = []

for name, path in test_files:
    file_path = Path(path)
    if file_path.exists():
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        result = engine.predict_single_file(name, content, custom_threshold=0.5)
        results.append({
            'file': name,
            'risk_pct': result['risk_percentage'],
            'is_risky': result['is_risky'],
            'label': result['decision_label']
        })
        
        print(f"\n📄 {name}")
        print(f"   Risk Score: {result['risk_percentage']:.2f}%")
        print(f"   Decision: {result['decision_label']}")
        print(f"   Risky: {result['is_risky']}")
    else:
        print(f"\n❌ {name} - File not found")

print("\n" + "="*70)
print("📊 SUMMARY")
print("="*70)

if results:
    print(f"\nFiles tested: {len(results)}")
    print(f"\nRisk Scores:")
    for r in results:
        print(f"  {r['file']:20s}: {r['risk_pct']:6.2f}%")
    
    # Check if predictions vary
    unique_scores = len(set(r['risk_pct'] for r in results))
    
    if unique_scores == 1:
        print(f"\n⚠️ WARNING: All {len(results)} files got SAME prediction!")
        print("   This suggests the model is not working properly.")
    elif unique_scores == len(results):
        print(f"\n✅ SUCCESS: All {len(results)} files got DIFFERENT predictions!")
        print("   The model is working correctly and discriminating between files.")
    else:
        print(f"\n✓ GOOD: {unique_scores} unique predictions out of {len(results)} files.")
        print("   The model is giving varied predictions.")
else:
    print("\n❌ No test files found. Check iac_files/ directory.")

print("="*70)
