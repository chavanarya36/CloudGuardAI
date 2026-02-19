"""Debug script to validate all 3 prediction modes using CorePredictor."""
import pytest
from pathlib import Path
try:
    from utils.feature_extractor import FeatureExtractor
    from utils.core_predictor import CorePredictor
except ImportError:
    pytest.skip("utils package not available", allow_module_level=True)

TEST_FILE = Path('iac_files/HIGH_risk.tf')


def main() -> None:
    print("=" * 50)
    print("🔍 DEBUGGING PREDICTION MODES (CorePredictor)")
    print("=" * 50)

    if not TEST_FILE.exists():
        print(f"❌ Test file not found: {TEST_FILE}")
        return

    fe = FeatureExtractor()
    content = TEST_FILE.read_text(encoding='utf-8')

    X, _ = fe.extract_features_single(TEST_FILE.name, content)
    print(f"\n✓ Features extracted: {X.shape}")

    for mode in ["supervised", "unsupervised", "hybrid"]:
        cp = CorePredictor(mode=mode)
        result = cp.predict_X(X)
        prob = result["risk_probability"] * 100.0
        level = result["risk_level"]

        print("\n" + "-" * 50)
        print(f"MODE: {mode.upper()}")
        print(f"Risk probability: {prob:.2f}%")
        print(f"Risk level      : {level}")
        print(f"Details         : {result.get('details')}")

    print("\n" + "=" * 50)


if __name__ == "__main__":
    main()
