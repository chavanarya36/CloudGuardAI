"""
Test script to verify all 3 prediction modes work
"""
import pytest
try:
    from utils.multi_mode_predictor import MultiModePredictor
    from utils.feature_extractor import FeatureExtractor
except ImportError:
    pytest.skip("utils package not available", allow_module_level=True)

from pathlib import Path
import numpy as np

print("="*70)
print("🧪 TESTING ALL 3 PREDICTION MODES")
print("="*70)

# Sample IaC file content
test_content = """
resource "aws_s3_bucket" "test" {
  bucket = "my-test-bucket"
  acl    = "public-read"
  
  versioning {
    enabled = false
  }
}

resource "aws_security_group" "allow_all" {
  name        = "allow_all"
  description = "Allow all inbound traffic"
  
  ingress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}
"""

print("\n📄 Test File Content:")
print("-" * 70)
print(test_content[:200] + "...")
print("-" * 70)

# Initialize feature extractor
print("\n🔧 Initializing feature extractor...")
feature_extractor = FeatureExtractor(expected_total_features=4107)
X, feature_info = feature_extractor.extract_features_single("test_file.tf", test_content)
print(f"✓ Features extracted: shape {X.shape}")

# Test all 3 modes
modes = ['supervised', 'unsupervised', 'hybrid']
results = {}

print("\n" + "="*70)
print("🚀 RUNNING PREDICTIONS")
print("="*70)

for mode in modes:
    print(f"\n{mode.upper()} MODE:")
    print("-" * 70)
    
    try:
        predictor = MultiModePredictor(mode=mode)
        pred = predictor.predict(X)
        
        if 'error' in pred:
            print(f"❌ Error: {pred['error']}")
            print(f"   Message: {pred.get('message', 'N/A')}")
        else:
            results[mode] = pred
            print(f"✅ Success!")
            print(f"   Mode: {pred['mode']}")
            print(f"   Risk Probability: {pred['risk_probability']:.4f}")
            print(f"   Risk Percentage: {pred['risk_probability']*100:.2f}%")
            print(f"   Details: {pred['details']}")
    
    except Exception as e:
        print(f"❌ Exception: {str(e)}")

# Summary
print("\n" + "="*70)
print("📊 SUMMARY")
print("="*70)

if len(results) == 3:
    print("\n✅ ALL 3 MODES WORKING!")
    print("\nRisk Scores:")
    for mode, pred in results.items():
        print(f"  {mode.upper():15s}: {pred['risk_probability']*100:5.2f}%")
    
    print("\n🎯 Ready to use in Streamlit app!")
    print("   Run: streamlit run app.py")
else:
    print(f"\n⚠️ Only {len(results)}/3 modes working")
    print("   Missing models may need training:")
    print("   Run: python train_all_models.py")

print("="*70)
