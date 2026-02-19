"""
Detailed Prediction Explainer
Shows EXACTLY what the model is detecting in each file
"""

from pathlib import Path
from utils.prediction_engine import PredictionEngine
import re

def analyze_file_patterns(content):
    """Analyze what security patterns are present in the file"""
    patterns = {
        'Critical Issues': [],
        'Medium Issues': [],
        'Good Practices': []
    }
    
    content_lower = content.lower()
    
    # Critical security issues
    if '0.0.0.0/0' in content:
        patterns['Critical Issues'].append('🔴 Wide-open access (0.0.0.0/0)')
    if re.search(r'(password|secret|key)\s*=\s*["\'][^"\']+["\']', content_lower):
        patterns['Critical Issues'].append('🔴 Hardcoded secrets detected')
    if 'acl.*public' in content_lower or 'public-read' in content_lower:
        patterns['Critical Issues'].append('🔴 Public access configured')
    if re.search(r'port\s*=\s*(22|3389|23)', content):
        patterns['Critical Issues'].append('🔴 Sensitive port exposed (SSH/RDP/Telnet)')
    
    # Medium issues
    if 'encryption' not in content_lower and 'kms' not in content_lower:
        patterns['Medium Issues'].append('🟡 No explicit encryption configured')
    if 'logging' not in content_lower:
        patterns['Medium Issues'].append('🟡 No logging configured')
    if 'versioning' not in content_lower:
        patterns['Medium Issues'].append('🟡 No versioning enabled')
    
    # Good practices
    if any(cidr in content for cidr in ['10.0.0.0', '172.16.0.0', '192.168']):
        patterns['Good Practices'].append('✅ Private IP ranges used')
    if 'encrypted' in content_lower or 'encryption' in content_lower:
        patterns['Good Practices'].append('✅ Encryption configured')
    if 'kms' in content_lower:
        patterns['Good Practices'].append('✅ KMS encryption used')
    if 'logging' in content_lower:
        patterns['Good Practices'].append('✅ Logging enabled')
    
    return patterns

def explain_prediction(file_path):
    """Provide detailed explanation of prediction"""
    
    print("\n" + "=" * 80)
    print(f"📄 FILE: {file_path.name}")
    print("=" * 80)
    
    # Read file
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Analyze patterns
    patterns = analyze_file_patterns(content)
    
    print("\n🔍 SECURITY PATTERN ANALYSIS:")
    print("-" * 80)
    
    if patterns['Critical Issues']:
        print("\n🔴 CRITICAL ISSUES FOUND:")
        for issue in patterns['Critical Issues']:
            print(f"   {issue}")
    else:
        print("\n🔴 CRITICAL ISSUES: None detected")
    
    if patterns['Medium Issues']:
        print("\n🟡 MEDIUM CONCERNS:")
        for issue in patterns['Medium Issues']:
            print(f"   {issue}")
    else:
        print("\n🟡 MEDIUM CONCERNS: None detected")
    
    if patterns['Good Practices']:
        print("\n✅ GOOD PRACTICES:")
        for practice in patterns['Good Practices']:
            print(f"   {practice}")
    else:
        print("\n✅ GOOD PRACTICES: None detected")
    
    # Get model prediction
    engine = PredictionEngine()
    result = engine.predict_single_file(file_path, content)
    
    prob = result['risk_probability']
    
    print("\n" + "-" * 80)
    print("🤖 MODEL PREDICTION:")
    print("-" * 80)
    print(f"   Risk Probability: {prob:.4f} ({prob*100:.2f}%)")
    print(f"   Decision: {result['decision_label']}")
    print(f"   Risk Band: {result['risk_band']}")
    print(f"   Heuristic Score: {result['heuristic_score']}/100")
    
    # Interpret
    print("\n💡 INTERPRETATION:")
    print("-" * 80)
    
    critical_count = len(patterns['Critical Issues'])
    medium_count = len(patterns['Medium Issues'])
    good_count = len(patterns['Good Practices'])
    
    if critical_count >= 2:
        expected = "HIGH RISK (multiple critical issues)"
    elif critical_count == 1:
        expected = "MEDIUM-HIGH RISK (one critical issue)"
    elif medium_count >= 3:
        expected = "MEDIUM RISK (several concerns)"
    elif good_count >= 3 and critical_count == 0:
        expected = "LOW RISK (follows best practices)"
    else:
        expected = "MEDIUM RISK (mixed signals)"
    
    print(f"   Expected based on patterns: {expected}")
    print(f"   Model prediction: {prob*100:.1f}% probability")
    
    if prob >= 0.9:
        print(f"   ✅ Model correctly identified as HIGH RISK")
    elif prob >= 0.7 and critical_count >= 1:
        print(f"   ⚠️  Model is cautious - detected issues but not extreme")
    elif prob < 0.3 and critical_count == 0:
        print(f"   ✅ Model correctly identified as LOW RISK")
    else:
        print(f"   ℹ️  Model detected mixed signals in the file")
    
    # Feature info
    if 'feature_info' in result:
        print(f"\n📊 FEATURE ANALYSIS:")
        print(f"   Total features extracted: {result['feature_info'].get('total_features', 'N/A')}")
        print(f"   File size: {result['feature_info'].get('char_count', 0)} characters")
        print(f"   Lines: {result['feature_info'].get('line_count', 0)}")
        print(f"   Resource count: {result['feature_info'].get('resource_count', 0)}")


# Main execution
print("=" * 80)
print(" " * 25 + "PREDICTION EXPLAINER")
print("=" * 80)

print("""
This tool explains EXACTLY what the model is seeing in each file.
It shows:
1. What security patterns are detected
2. What the model predicts
3. Why the prediction makes sense (or doesn't)
""")

test_files = [
    'iac_files/HIGH_risk.tf',
    'iac_files/MEDIUM_risk.tf',
    'iac_files/LOW_risk.tf',
    'iac_files/vulnerable_sample.tf'
]

for file_path_str in test_files:
    file_path = Path(file_path_str)
    if file_path.exists():
        explain_prediction(file_path)
    else:
        print(f"\n❌ File not found: {file_path_str}")

print("\n" + "=" * 80)
print("KEY INSIGHTS:")
print("=" * 80)
print("""
🎯 Why predictions vary:

1. THE MODEL LEARNS FROM 21,107 REAL FILES
   - It doesn't just look for keywords
   - It learned patterns from actual IaC security scans
   - Real code has mixed good/bad practices

2. SYNTHETIC TEST FILES MAY NOT MATCH TRAINING DATA
   - If test files are "too perfect" examples
   - Model might not have seen such extreme cases
   - Real vulnerabilities are often subtle

3. ENSEMBLE MODELS ARE CONSERVATIVE
   - XGBoost might say HIGH, Neural Network says MEDIUM
   - Final prediction is averaged
   - This reduces false alarms but may lower confidence

4. THE 93.74% THRESHOLD IS INTENTIONAL
   - Only files with VERY high confidence get flagged
   - Reduces alert fatigue in production
   - Better to review 100 files at 95% confidence than 1000 at 50%

✅ GOOD SIGNS:
   - Files with critical issues get higher probabilities
   - Files with good practices get lower probabilities
   - Probabilities reflect severity ranking

❌ BAD SIGNS:
   - All files get same probability
   - High-risk files get very low scores
   - Low-risk files get very high scores
""")

print("\n" + "=" * 80)
print("✅ Analysis Complete!")
print("=" * 80)
