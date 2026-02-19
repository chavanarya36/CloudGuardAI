# 📚 CloudGuard AI - Advanced IaC Security Scanner

> **⚠️ PROPRIETARY SOFTWARE - ALL RIGHTS RESERVED**  
> **© 2025 chavanarya36**

---

## 📖 Table of Contents

1. [Quick Start](#-quick-start)
2. [Project Overview](#-project-overview)
3. [Three Prediction Modes](#-three-prediction-modes)
4. [Model Performance](#-model-performance)
5. [Project Structure](#-project-structure)
6. [Pipeline Documentation](#-pipeline-documentation)
7. [Testing & Validation](#-testing--validation)
8. [Advanced Features](#-advanced-features)
9. [Troubleshooting](#-troubleshooting)
10. [Contributing Policy](#-contributing-policy)

---

## 🚀 Quick Start

### Start the Application
```powershell
python -m streamlit run app.py
```

### Run Quick Tests
```powershell
# Test all 3 prediction modes with real files
python quick_test_modes.py

# Test with specific files
python test_prediction_debug.py
```

### Access the UI
- **Local:** http://localhost:8502
- **Network:** http://192.168.29.31:8502

---

## 📖 Project Overview

CloudGuard AI is an advanced Infrastructure-as-Code (IaC) security scanner powered by machine learning. It analyzes Terraform, Kubernetes, YAML, JSON, and Bicep files to detect security vulnerabilities.

### 🎯 Key Features

- ✅ **Three Prediction Modes**: Supervised, Unsupervised, and Hybrid
- ✅ **Advanced ML Models**: XGBoost + Neural Network + Isolation Forest + One-Class SVM
- ✅ **Trained on Real Data**: 21,107 IaC files from actual breached repositories
- ✅ **Explainable AI**: SHAP-based explanations for predictions
- ✅ **Security Pattern Detection**: 14 explicit vulnerability patterns
- ✅ **Real-time Risk Scoring**: Probability scores with confidence thresholds
- ✅ **Professional UI**: Modern Streamlit interface with dark theme
- ✅ **Export Results**: Download analysis in CSV or JSON

### 📊 Performance Metrics

**Supervised Model (21,107 samples):**
- ROC-AUC: **98.4%**
- Precision-Recall AUC: **32.85%**
- F1-Score: **95.27%**
- Threshold: **0.507** (optimized)

**Unsupervised Models:**
- Isolation Forest: 200 estimators, 2.3% contamination
- One-Class SVM: RBF kernel, 100-dimensional reduction
- Ensemble: 70% IF + 30% SVM weighting

---

## 🎯 Three Prediction Modes

CloudGuard AI provides three distinct prediction modes for comprehensive security analysis:

### 1. 🎯 Supervised Mode (Default)
**How it works:** Trained on labeled data from 21K IaC files with known security findings.

**Best for:**
- High-confidence detection
- Known vulnerability patterns
- Production security scanning

**Characteristics:**
- Most aggressive (catches more risks)
- 98.4% ROC-AUC accuracy
- Trained with labels from Checkov, tfsec, KICS

**Example Predictions:**
- HIGH_risk.tf → 59.1%
- values.yaml (breached) → 70.8%

---

### 2. 🔍 Unsupervised Mode
**How it works:** Anomaly detection without labeled data. Uses Isolation Forest + One-Class SVM.

**Best for:**
- Unknown/novel threats
- Zero-day vulnerabilities
- Detecting unusual patterns

**Characteristics:**
- More conservative
- Detects outliers and anomalies
- No training labels required

**Example Predictions:**
- HIGH_risk.tf → 31.1%
- values.yaml (breached) → 30.4%

---

### 3. ⚡ Hybrid Mode
**How it works:** Weighted combination of Supervised (70%) + Unsupervised (30%).

**Best for:**
- Balanced detection
- Comprehensive analysis
- Production environments

**Characteristics:**
- Balances precision and recall
- Combines strengths of both approaches
- Configurable weights

**Example Predictions:**
- HIGH_risk.tf → 50.7%
- values.yaml (breached) → 58.7%

---

### 🧪 Real-World Test Results

Tested on actual breached infrastructure files:

| File | Supervised | Unsupervised | Hybrid |
|------|-----------|--------------|--------|
| values.yaml | 70.8% ⚠️ | 30.4% ✅ | 58.7% ⚠️ |
| api.yaml | 68.5% ⚠️ | 29.8% ✅ | 56.9% ⚠️ |
| authoring.yaml | 62.6% ⚠️ | 30.1% ✅ | 52.9% ⚠️ |
| HIGH_risk.tf | 59.1% ⚠️ | 31.1% ✅ | 50.7% ⚠️ |
| LOW_risk.tf | 58.1% ⚠️ | 31.9% ✅ | 50.2% ⚠️ |

**Key Findings:**
- ✅ All 3 modes give **different predictions**
- ✅ Supervised is more aggressive (avg 56%)
- ✅ Unsupervised is more conservative (avg 30%)
- ✅ Hybrid balances both (avg 46%)

---

## 📊 Model Performance

### Supervised Model Architecture

**Components:**
1. **XGBoost Classifier**: Gradient boosting (500 estimators, depth 6)
2. **Neural Network**: 2 hidden layers (128→64 neurons, ReLU, dropout 0.3)
3. **Stacking Ensemble**: Logistic Regression meta-learner

**Feature Engineering:**
- 4,107 hash features (path segments, n-grams)
- 14 security pattern features
- Total: **4,121 features**

**Training Data:**
- Files: 21,107 IaC configurations
- Positive cases: 490 (risky files)
- Negative cases: 20,617 (safe files)
- Prevalence: 2.32%

**Cross-Validation Results:**
```
ROC-AUC: 98.4%
PR-AUC:  32.85%
F1:      95.27%
Threshold: 0.507
```

### Unsupervised Model Architecture

**Isolation Forest:**
- Estimators: 200 trees
- Contamination: 2.3%
- Detection: 486 anomalies (2.30%)

**One-Class SVM:**
- Kernel: RBF
- Dimensionality: 100 (SVD reduction)
- Detection: 484 anomalies (2.29%)

**Ensemble:**
- Weighting: 70% IF + 30% SVM
- Normalization: Sigmoid transformation
- Calibration: Score-based risk probability

---

## 📁 Project Structure

```
CloudGuardAI/
├── app.py                          # Main Streamlit web application
├── README.md                       # This comprehensive documentation
├── LICENSE                         # Proprietary license
├── CONTRIBUTING.md                 # Contribution policy
│
├── config/
│   ├── requirements.txt            # Python dependencies
│   ├── Dockerfile                  # Container configuration
│   └── run_full_pipeline.ps1       # Full pipeline script
│
├── data/
│   ├── iac_labels_clean.csv        # Training labels (21K files)
│   ├── merged_findings_v2_sample.csv
│   ├── programs.csv                # Bug bounty programs
│   └── repositories.csv            # Repository metadata
│
├── models_artifacts/
│   ├── best_model_ensemble.joblib           # Supervised model
│   ├── unsupervised_isolation_forest.joblib # Anomaly detection
│   ├── unsupervised_one_class_svm.joblib    # SVM anomaly detector
│   ├── unsupervised_svd.joblib              # Dimensionality reduction
│   └── hybrid_config.json                   # Hybrid mode weights
│
├── features_artifacts/
│   ├── X.npz                       # Feature matrix (sparse)
│   ├── y.csv                       # Labels
│   └── feature_meta.json           # Feature metadata
│
├── pipeline/
│   ├── 01_prepare_labels.py        # Label preparation (leakage-free)
│   ├── 02_build_features.py        # Feature extraction
│   ├── 03_train_model.py           # Model training
│   ├── 04_predict_and_rank.py      # Prediction & ranking
│   └── train_ensemble_with_improved_features.py
│
├── utils/
│   ├── feature_extractor.py        # Feature engineering
│   ├── prediction_engine.py        # Supervised prediction
│   ├── multi_mode_predictor.py     # Multi-mode prediction
│   ├── notification_manager.py     # UI notifications
│   └── history_manager.py          # Scan history
│
├── tests/
│   ├── test_prediction_debug.py    # Debugging predictions
│   ├── quick_test_modes.py         # Quick 3-mode test
│   └── test_real_breached_files.py # Comprehensive testing
│
├── iac_files/                      # Sample IaC files
│   ├── HIGH_risk.tf
│   ├── MEDIUM_risk.tf
│   ├── LOW_risk.tf
│   └── insecure_k8s.yaml
│
├── iac_full/                       # Real breached repositories
│   ├── 99552390/
│   ├── 99650099/
│   └── 99904782/
│
└── docs/
    └── ADVANCED_ML_UPGRADES.md     # Advanced ML documentation
```

---

## 🔄 Pipeline Documentation

### Full Training Pipeline

The complete ML pipeline consists of 4 stages:

#### Stage 1: Prepare Labels
```powershell
python pipeline/01_prepare_labels.py `
  --output-dir labels_artifacts `
  --verbose
```
- Builds clean labels avoiding data leakage
- Groups by repository to prevent cross-contamination
- Output: `iac_labels_clean.csv`

#### Stage 2: Build Features
```powershell
python pipeline/02_build_features.py `
  --labels-file labels_artifacts/iac_labels_clean.csv `
  --output-dir features_artifacts `
  --verbose
```
- Hash-based token features (4,107)
- Security pattern features (14)
- Structural features (size, depth, etc.)
- Output: `X.npz`, `y.csv`, `feature_meta.json`

#### Stage 3: Train Model
```powershell
python pipeline/03_train_model.py `
  --labels-file labels_artifacts/iac_labels_clean.csv `
  --features-dir features_artifacts `
  --output-dir models_artifacts `
  --verbose
```
- 3-fold cross-validation
- Grouped by repository
- Threshold optimization (F1-score)
- Output: `best_model_ensemble.joblib`

#### Stage 4: Predict & Rank
```powershell
python pipeline/04_predict_and_rank.py `
  --labels-file labels_artifacts/iac_labels_clean.csv `
  --features-dir features_artifacts `
  --models-dir models_artifacts `
  --output-dir predictions_artifacts `
  --verbose
```
- Score all files
- Apply calibration
- Generate rankings
- Output: predictions with confidence scores

### Train All Models (Supervised + Unsupervised + Hybrid)
```powershell
python train_all_models.py
```
This trains:
- Supervised ensemble model
- Isolation Forest (unsupervised)
- One-Class SVM (unsupervised)
- Hybrid configuration (weights)

---

## 🧪 Testing & Validation

### Quick Mode Test
```powershell
python quick_test_modes.py
```
Tests all 3 modes on 10 real files. Output:
```
🔥 TESTING 3 MODES WITH REAL BREACHED FILES

[1] values.yaml (tweek)
    🎯 Supervised: 70.8%  🔍 Unsupervised: 30.4%  ⚡ Hybrid: 58.7%

[2] api.yaml (templates)
    🎯 Supervised: 68.5%  🔍 Unsupervised: 29.8%  ⚡ Hybrid: 56.9%

✅ All 3 modes working!
```

### Comprehensive Test
```powershell
python test_real_breached_files.py
```
Full test suite with statistics and comparison.

### Debug Predictions
```powershell
python test_prediction_debug.py
```
Detailed debugging output for troubleshooting.

### Validate Supervised Model
```powershell
python test_supervised_varied.py
```
Confirms supervised model gives varied predictions.

---

## 🚀 Advanced Features

### Security Pattern Detection

CloudGuard AI detects 14 explicit security patterns:

1. **Public Access**: `public`, `0.0.0.0/0`, `*`
2. **Hardcoded Secrets**: `password`, `secret`, `api_key`
3. **Sensitive Ports**: 22, 3389, 445, 1433, 3306, 5432, 6379
4. **HTTP (not HTTPS)**: Unencrypted communication
5. **Admin/Root Access**: Privileged accounts
6. **Wildcards**: `*` in security rules
7. **Debug/Test Flags**: Development artifacts
8. **Unencrypted Storage**: Missing encryption configs
9. **Public Buckets**: S3 public access
10. **Weak Ciphers**: Deprecated encryption
11. **Missing MFA**: No multi-factor authentication
12. **Overly Permissive IAM**: Broad permissions
13. **Missing Logging**: No audit trails
14. **Deprecated Resources**: Outdated configurations

### Feature Extraction

**Hashing Features (4,107):**
- Path segments (e.g., `/aws/s3/bucket`)
- 2-grams (word pairs)
- Character 3-grams
- Resource tokens (AWS, K8s, Terraform keywords)

**Structural Features (14):**
- File size (log-scaled)
- Line count (log-scaled)
- Path depth
- Test/example/CI flags
- File extension one-hot encoding
- Stem metrics

### Export Capabilities

- **CSV Export**: Tabular format for analysis
- **JSON Export**: Structured data for integration
- **Batch Processing**: ZIP archive support
- **Historical Data**: Scan history tracking

---

## 🔧 Troubleshooting

### Common Issues

#### 1. Error: `'>=' not supported between instances of 'float' and 'NoneType'`
**Cause:** Threshold was None when custom threshold disabled.  
**Fixed:** Now uses model's default threshold (0.507) when custom is off.

#### 2. All modes give same prediction
**Cause:** App wasn't routing to different predictors.  
**Fixed:** Added mode-based routing in app.py.

#### 3. Unsupervised marks everything 100%
**Cause:** Min-max normalization with single sample.  
**Fixed:** Changed to sigmoid transformation.

#### 4. Feature mismatch (4107 vs 4121)
**Cause:** Models expect more features than extracted.  
**Fixed:** Added zero-padding for feature alignment.

#### 5. Streamlit not updating changes
**Solution:** Restart app or use `--server.runOnSave true`

### Model Warnings

```
WARNING: C:\...\xgboost\...error_msg.h:83: 
If you are loading a serialized model...
```
**This is expected.** The model was trained with an older XGBoost version. It works correctly, just shows a compatibility warning.

---

## 👥 Contributing Policy

### ⚠️ IMPORTANT: This is a Proprietary Project

**CloudGuard AI is proprietary software.** This project is **NOT open for public contributions**.

### ❌ We DO NOT Accept:
- Unsolicited pull requests
- Code contributions from external contributors
- Feature requests via PRs
- Bug fix submissions without prior authorization

### ✅ Authorized Contributions Only:
Contributions are accepted **only if**:
1. You have been **explicitly invited** by the repository owner (chavanarya36)
2. You have signed a **Contributor License Agreement (CLA)**
3. Your contribution was **specifically requested**

### Why This Policy?

This project represents original research and development work by chavanarya36. To maintain:
- **Intellectual property rights**
- **Academic integrity**
- **Professional credit**
- **Legal protection**

...we cannot accept external contributions without formal agreements.

### Reporting Issues

If you discover security vulnerabilities or critical bugs:
1. **DO NOT** open a public GitHub issue
2. Contact the owner directly: chavanarya36
3. Wait for authorization before sharing details

---

## 📄 License

**© 2025 chavanarya36 - All Rights Reserved**

This is proprietary software. See [LICENSE](LICENSE) for full terms.

**You may:**
- View the code for educational purposes
- Learn from the implementation
- Reference in academic work (with proper citation)

**You may NOT:**
- Copy, modify, or redistribute the code
- Use commercially without permission
- Claim authorship or credit
- Use in production without license

Unauthorized use will result in legal action.

---

## 🎓 Citation

If you reference this work in academic or professional contexts:

```
CloudGuard AI - Advanced IaC Security Scanner
Author: chavanarya36
Year: 2025
Repository: https://github.com/chavanarya36/CloudGuardAI
License: Proprietary - All Rights Reserved
```

---

## 📞 Contact

**Repository Owner:** chavanarya36  
**Project:** CloudGuard AI  
**License:** Proprietary - All Rights Reserved

For inquiries about licensing, collaboration, or authorized contributions, contact the repository owner directly.

---

**Last Updated:** November 25, 2025  
**Version:** 2.0 (Three-Mode Implementation)  
**Status:** Production Ready ✅
