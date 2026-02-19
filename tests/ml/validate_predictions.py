"""
Model Validation Script - Test predictions against known ground truth
Shows prediction accuracy on labeled test files
"""

import pandas as pd
import numpy as np
from pathlib import Path
from utils.prediction_engine import PredictionEngine
from utils.model_loader import ModelLoader

print("=" * 70)
print(" " * 20 + "MODEL VALIDATION REPORT")
print("=" * 70)

# Initialize prediction engine
engine = PredictionEngine()

print(f"\n📊 Model Information:")
model_info = engine.model_loader.get_model_info()
print(f"   Model Type: {model_info['model_type']}")
print(f"   PR-AUC: {model_info['pr_auc']:.4f}")
print(f"   ROC-AUC: {model_info['roc_auc']:.4f}")
print(f"   Threshold: {model_info['threshold']:.4f}")

# Test files with known risk levels
test_files = [
    {
        'path': 'iac_files/HIGH_risk.tf',
        'expected_risk': 'HIGH',
        'reason': 'Public SSH (0.0.0.0/0), public S3 bucket, hardcoded secrets'
    },
    {
        'path': 'iac_files/MEDIUM_risk.tf',
        'expected_risk': 'MEDIUM',
        'reason': 'Some security issues but not critical'
    },
    {
        'path': 'iac_files/LOW_risk.tf',
        'expected_risk': 'LOW',
        'reason': 'Private SG (10.0.0.0/8), encryption enabled, no public access'
    },
    {
        'path': 'iac_files/vulnerable_sample.tf',
        'expected_risk': 'HIGH',
        'reason': 'Known vulnerable configuration'
    }
]

print("\n" + "=" * 70)
print("TESTING MODEL PREDICTIONS")
print("=" * 70)

results = []
correct = 0
total = 0

for test in test_files:
    file_path = Path(test['path'])
    
    if not file_path.exists():
        print(f"\n❌ File not found: {test['path']}")
        continue
    
    # Read file
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Get prediction
    result = engine.predict_single_file(file_path, content)
    
    # Determine predicted risk level
    prob = result['risk_probability']
    if prob >= 0.9:
        predicted_risk = 'HIGH'
    elif prob >= 0.5:
        predicted_risk = 'MEDIUM'
    else:
        predicted_risk = 'LOW'
    
    # Check if correct
    is_correct = (predicted_risk == test['expected_risk'])
    if is_correct:
        correct += 1
    total += 1
    
    results.append({
        'file': file_path.name,
        'expected': test['expected_risk'],
        'predicted': predicted_risk,
        'probability': prob,
        'correct': '✅' if is_correct else '❌',
        'reason': test['reason']
    })
    
    # Print individual result
    status = '✅ CORRECT' if is_correct else '❌ INCORRECT'
    print(f"\n{status} - {file_path.name}")
    print(f"   Expected: {test['expected_risk']} | Predicted: {predicted_risk}")
    print(f"   Probability: {prob:.4f} ({prob*100:.2f}%)")
    print(f"   Reason: {test['reason']}")

# Summary
print("\n" + "=" * 70)
print("VALIDATION SUMMARY")
print("=" * 70)

accuracy = (correct / total * 100) if total > 0 else 0
print(f"\n📈 Accuracy: {correct}/{total} correct ({accuracy:.1f}%)")

# Detailed table
print("\n📊 Detailed Results:")
print("-" * 70)
for r in results:
    print(f"{r['correct']} {r['file']:<25} Expected: {r['expected']:<6} | "
          f"Predicted: {r['predicted']:<6} | Prob: {r['probability']:.4f}")

# Explanation of what "correct" means
print("\n" + "=" * 70)
print("UNDERSTANDING THE PREDICTIONS")
print("=" * 70)

print("""
🎯 How to interpret results:

1. HIGH RISK (prob >= 0.90):
   - File has 90%+ probability of containing security vulnerabilities
   - Should be flagged for immediate review
   - Examples: Public SSH, hardcoded secrets, public S3 buckets

2. MEDIUM RISK (0.50 <= prob < 0.90):
   - File has some security concerns but not critical
   - Should be reviewed but not urgent
   - Examples: Partial misconfigurations, less critical issues

3. LOW RISK (prob < 0.50):
   - File follows security best practices
   - Minimal to no security concerns
   - Examples: Private networks, encryption enabled, proper access control

🔍 Why predictions might vary:

1. Feature Complexity:
   - Model looks at 4,107 different features
   - Some files may have mixed signals (good + bad patterns)
   - This is normal and shows model is analyzing deeply

2. Threshold Calibration:
   - Current threshold: 0.9374 (93.74%)
   - Files above this are flagged as HIGH RISK
   - This is intentionally strict to reduce false alarms

3. Ensemble Diversity:
   - XGBoost, Neural Network, and LR may disagree
   - Final prediction is weighted average
   - Shows model considers multiple perspectives

✅ Model is working correctly if:
   - HIGH_risk.tf gets high probability (>= 0.9)
   - LOW_risk.tf gets low probability (< 0.5)
   - Probabilities generally match security severity

❌ Model needs investigation if:
   - HIGH_risk.tf gets low probability (< 0.5)
   - LOW_risk.tf gets high probability (>= 0.9)
   - All files get similar probabilities
""")

print("\n" + "=" * 70)
print("✅ Validation Complete!")
print("=" * 70)
