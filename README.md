# CloudGuard AI - Infrastructure Risk Scanner

> **⚠️ PROPRIETARY SOFTWARE - ALL RIGHTS RESERVED**  
> **© 2025 chavanarya36**  
> This repository is available for **viewing and educational purposes only**.  
> Redistribution, modification, commercial use, or claiming credit is **strictly prohibited**.  
> See [LICENSE](LICENSE) for full terms. Unauthorized use will result in legal action.

---

AI-powered Infrastructure-as-Code (IaC) security scanner using machine learning to detect potential security vulnerabilities.

## 🎯 Features

- **Single File Analysis**: Upload individual .tf, .yaml, .json, or .bicep files for risk assessment
- **Batch Processing**: Upload ZIP archives containing multiple IaC files for bulk analysis
- **Real-time Risk Scoring**: Get probability scores and binary risk decisions
- **Detailed Explanations**: Understand why files are flagged as risky
- **Professional UI**: Clean, intuitive interface with dark theme
- **Configurable Thresholds**: Adjust risk sensitivity based on your needs
- **Export Results**: Download analysis results in CSV or JSON format



---```- **Real-time Risk Scoring**: Get probability scores and binary risk decisions



## 📁 Project StructureCloudGuardAI/- **Detailed Explanations**: Understand why files are flagged as risky



```├── app.py                      # Streamlit web application- **Professional UI**: Clean, intuitive interface suitable for enterprise use

CloudGuardAI/

├── app.py                      # Streamlit web application├── data/                       # Data files and datasets- **Configurable Thresholds**: Adjust risk sensitivity based on your needs

├── README.md                   # This file

├── data/                       # Data files and datasets│   ├── iac_labels_clean.csv    # Labeled IaC security findings- **Export Results**: Download analysis results in CSV or JSON format

│   ├── iac_labels_clean.csv

│   ├── programs.csv│   ├── iac_labels_summary.csv  # Label statistics summary

│   └── repositories.csv

├── pipeline/                   # ML pipeline scripts│   ├── programs.csv            # IaC program inventory## Installation

│   ├── 01_prepare_labels.py

│   ├── 02_build_features.py│   ├── repositories.csv        # GitHub repository list

│   ├── 03_train_model.py

│   └── ... (8 more scripts)│   └── merged_findings_v2_sample.csv### Local Development

├── scanners/                   # IaC scanner integration

│   ├── scan_checkov.py├── pipeline/                   # ML pipeline scripts

│   ├── scan_tfsec.py

│   └── scan_kics.py│   ├── 01_prepare_labels.py1. Clone the repository:

├── features_artifacts/         # Extracted ML features

├── models_artifacts/           # Trained models│   ├── 02_build_features.py```bash

├── predictions_artifacts/      # Model predictions

├── utils/                      # Utility functions│   ├── 03_train_model.pygit clone <repository-url>

│   ├── model_loader.py

│   ├── feature_extractor.py│   ├── 04_predict_and_rank.pycd CloudGuardAI

│   └── prediction_engine.py

├── docs/                       # Documentation│   ├── 05_leakage_sanity.py```

│   ├── README.md

│   ├── README_pipeline.md│   ├── 05_validation_sanity.py

│   └── model_report.md

└── config/                     # Configuration│   ├── 06_reliability_diagnostics.py2. Install dependencies:

    ├── requirements.txt

    ├── Dockerfile│   ├── 07_threshold_tuning.py```bash

    └── run_full_pipeline.ps1

```│   ├── 08_per_repo_validation.pypip install -r requirements.txt



---│   └── summarize_metrics.py```



## 🚀 Quick Start├── scanners/                   # IaC scanner integration



### 1. Install Dependencies│   ├── scan_checkov.py3. Ensure model artifacts are present:



```bash│   ├── scan_tfsec.py- `models_artifacts/best_model_lr.joblib`

pip install -r config/requirements.txt

```│   ├── scan_kics.py- `models_artifacts/threshold_lr.json`



### 2. Run Web Application│   ├── merge_findings.py- `models_artifacts/cv_metrics_lr.json`



```bash│   └── *_outputs/              # Scanner results- `features_artifacts/meta.json`

streamlit run app.py

# or├── features_artifacts/         # Extracted ML features

python -m streamlit run app.py

```├── models_artifacts/           # Trained models4. Run the application:



### 3. Open Browser├── predictions_artifacts/      # Model predictions```bash



Navigate to `http://localhost:8501`├── labels_artifacts/           # Processed labelsstreamlit run app.py



---├── utils/                      # Utility functions```



## 🐳 Docker Deployment├── scripts/                    # Helper scripts



### Build Image├── tests/                      # Test files5. Open your browser to `http://localhost:8501`



```bash├── docs/                       # Documentation

docker build -t cloudguard-ai -f config/Dockerfile .

```│   ├── README.md               # Main documentation### Docker Deployment



### Run Container│   ├── README_pipeline.md      # Pipeline guide



```bash│   ├── README_PROJECT.md       # Project overview1. Build the Docker image:

docker run -p 8501:8501 cloudguard-ai

```│   └── model_report.md         # Model performance```bash



Access at `http://localhost:8501`└── config/                     # Configurationdocker build -t cloudguard-ai .



---    ├── requirements.txt```



## 💻 Usage    ├── Dockerfile



### Single File Mode    └── run_full_pipeline.ps12. Run the container:



1. Select "📄 Single File Analysis" in the sidebar``````bash

2. Upload a supported IaC file (.tf, .yaml, .yml, .json, .bicep)

3. Click "🔍 Analyze File Security"docker run -p 8501:8501 cloudguard-ai

4. View the risk assessment, gauge, and detailed explanation

5. Adjust threshold if needed using the sidebar slider---```



### Batch Mode



1. Select "📦 Batch Processing" in the sidebar## 🚀 Quick Start3. Access the application at `http://localhost:8501`

2. Upload a ZIP file containing your IaC files

3. Click "🔍 Analyze ZIP Archive"

4. Review summary metrics and detailed results

5. Use filters to find specific risk levels### 1. Install Dependencies## Usage

6. Download results as CSV or JSON

```bash

---

pip install -r config/requirements.txt### Single File Mode

## 🧠 Model Information

```1. Select "Single File" in the sidebar

- **Algorithm**: Logistic Regression (liblinear solver, L2 regularization)

- **Features**: 32,768 sparse hash features + 8 dense structural features2. Upload a supported IaC file (.tf, .yaml, .yml, .json, .bicep)

- **Performance**: 

  - PR-AUC: 0.3379### 2. Run Web Application3. View the risk assessment and explanation

  - ROC-AUC: 0.9726

  - Balanced Accuracy: 0.9500```bash4. Adjust threshold if needed using the sidebar slider

- **Training Data**: 21,107 IaC files with 2.3% positive rate

- **Calibration**: 5-fold Sigmoid calibrationstreamlit run app.py



See [Model Report](docs/model_report.md) for detailed performance metrics.```### Batch Mode



---1. Select "Batch Upload" in the sidebar



## 🔧 Configuration### 3. Run Full Pipeline2. Upload a ZIP file containing your IaC files



### Model Artifacts Required```bash3. Click "Analyze ZIP Archive"



The application requires these files:python pipeline/01_prepare_labels.py4. Review the summary metrics and detailed results table

- `models_artifacts/best_model_lr.joblib` - Trained scikit-learn model

- `models_artifacts/threshold_lr.json` - Global decision thresholdpython pipeline/02_build_features.py5. Download results as CSV or JSON

- `models_artifacts/cv_metrics_lr.json` - Model performance metrics

- `features_artifacts/meta.json` - Feature extraction metadatapython pipeline/03_train_model.py



### Supported File Types```## Model Information



- **Terraform**: `.tf` files

- **YAML**: `.yaml`, `.yml` files (Kubernetes, Docker Compose, etc.)

- **JSON**: `.json` files (CloudFormation, etc.)---- **Algorithm**: Logistic Regression (liblinear solver)

- **Bicep**: `.bicep` files (Azure Resource Manager)

- **Features**: Sparse hash features from file paths and content, plus dense structural features

---

## 📚 Documentation- **Performance**: PR-AUC ≈ 0.34, ROC-AUC ≈ 0.97

## 📚 Documentation

- **Training Data**: 21,107 IaC files with 2.3% positive rate

- **[Main Documentation](docs/README.md)** - Comprehensive project guide

- **[Pipeline Guide](docs/README_pipeline.md)** - ML pipeline details- **[Main Documentation](docs/README.md)** - Comprehensive project guide

- **[Project Overview](docs/README_PROJECT.md)** - Architecture and design

- **[Model Report](docs/model_report.md)** - Performance metrics and analysis- **[Pipeline Guide](docs/README_pipeline.md)** - ML pipeline details## Architecture



---- **[Project Overview](docs/README_PROJECT.md)** - Architecture and design



## 🛠️ Development- **[Model Report](docs/model_report.md)** - Performance metrics```



### Run ML Pipelineapp.py                          # Main Streamlit application



```bash---utils/

# Prepare labels

python pipeline/01_prepare_labels.py├── __init__.py



# Build features## 🔧 Configuration├── model_loader.py            # Load trained model and artifacts

python pipeline/02_build_features.py

├── feature_extractor.py       # Extract features from IaC files

# Train model

python pipeline/03_train_model.pyConfiguration files located in `config/`:└── prediction_engine.py       # Handle predictions and batch processing



# Make predictions- `requirements.txt` - Python dependenciesmodels_artifacts/              # Trained model files

python pipeline/04_predict_and_rank.py

```- `Dockerfile` - Container configurationfeatures_artifacts/            # Feature metadata



### Run Tests- `run_full_pipeline.ps1` - Automated pipeline executionrequirements.txt               # Python dependencies



```bashDockerfile                     # Container configuration

pytest tests/

```---```



### Run Scanners



```bash## 📊 Key Features## API Reference

# Checkov scanner

python scanners/scan_checkov.py



# tfsec scanner✅ Multi-scanner integration (Checkov, tfsec, KICS)  ### PredictionEngine

python scanners/scan_tfsec.py

✅ Machine learning-based vulnerability prioritization  

# KICS scanner

python scanners/scan_kics.py✅ Interactive web interface with Streamlit  Main class for handling predictions:

```

✅ Comprehensive reliability diagnostics  

---

✅ Per-repository validation  ```python

## 📊 Performance

✅ Threshold tuning for precision/recall optimization  from utils.prediction_engine import PredictionEngine

- **Single file analysis**: < 1 second

- **Batch processing**: ~100 files per second

- **Memory usage**: ~200MB base + ~1MB per 1000 files

---engine = PredictionEngine()

---



## 🔒 Security Considerations

## 📈 Model Performance# Single file prediction

- Files are processed in memory without persistent storage

- Temporary files are automatically cleaned up after processingresult = engine.predict_single_file(file_path, content)

- No data is transmitted outside the application

- Suitable for air-gapped environments- **PR-AUC**: 0.3379

- All processing happens locally

- **ROC-AUC**: 0.9726# Batch prediction

---

- **Dataset**: 21,107 labeled IaC filesresults = engine.predict_batch(file_data_list)

## 🐛 Troubleshooting

- **Positive cases**: 490 (2.3%)

### Model Not Found Error

Ensure all model artifacts are present in `models_artifacts/` and `features_artifacts/` directories.# Process ZIP file



### Feature Extraction ErrorsSee [Model Report](docs/model_report.md) for detailed metrics.results = engine.process_zip_file(zip_path)

Check that uploaded files are valid IaC formats and properly encoded (UTF-8).

```

### Memory Errors on Large Batches

Process smaller ZIP files or increase available memory. Docker users can use `--memory` flag.---



### Streamlit Command Not Found### ModelLoader

Use `python -m streamlit run app.py` instead of `streamlit run app.py`.

## 🛠️ Development

---

Load and manage ML artifacts:

## 📝 License

### Run Tests

[Add your license information here]

```bash```python

---

pytest tests/from utils.model_loader import ModelLoader

**Last Updated**: October 31, 2025  

**Version**: 1.0  ```

**Status**: ✅ Production Ready

loader = ModelLoader()

### Rebuild Featuresmodel, threshold, metrics = loader.load_all()

```bash```

python pipeline/02_build_features.py

```### FeatureExtractor



### Retrain ModelExtract features from IaC files:

```bash

python pipeline/03_train_model.py```python

```from utils.feature_extractor import FeatureExtractor



---extractor = FeatureExtractor()

X, feature_info = extractor.extract_features_single(file_path, content)

## 📝 License```



[Your License Here]## Configuration



---### Environment Variables



**Last Updated**: October 31, 2025  - `STREAMLIT_SERVER_PORT`: Port for the web application (default: 8501)

**Version**: 1.0  - `STREAMLIT_SERVER_ADDRESS`: Server address (default: 0.0.0.0 for Docker)

**Status**: Production Ready ✅

### Model Artifacts

The application requires these files to be present:

- `models_artifacts/best_model_lr.joblib`: Trained scikit-learn model
- `models_artifacts/threshold_lr.json`: Global decision threshold
- `models_artifacts/cv_metrics_lr.json`: Model performance metrics
- `features_artifacts/meta.json`: Feature extraction metadata

## Supported File Types

- **Terraform**: `.tf` files
- **YAML**: `.yaml`, `.yml` files (Kubernetes, Docker Compose, etc.)
- **JSON**: `.json` files (CloudFormation, etc.)
- **Bicep**: `.bicep` files (Azure Resource Manager)

## Performance

- Single file analysis: < 1 second
- Batch processing: ~100 files per second (depends on file size)
- Memory usage: ~200MB base + ~1MB per 1000 files in batch

## Security Considerations

- Files are processed in memory without persistent storage
- Temporary files are automatically cleaned up
- No data is transmitted outside the application
- Suitable for air-gapped environments

## Troubleshooting

### Common Issues

1. **Model not found error**: Ensure all model artifacts are present in the correct directories
2. **Feature extraction errors**: Check that uploaded files are valid IaC formats
3. **Memory errors on large batches**: Process smaller ZIP files or increase container memory

### Logs

When running with Docker, view logs with:
```bash
docker logs <container-id>
```

## Contributing

1. Follow the existing code structure
2. Add tests for new features
3. Update documentation as needed
4. Ensure Docker build succeeds

## License

[Add your license information here]