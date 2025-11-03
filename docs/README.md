# CloudGuard AI - Infrastructure Risk Scanner

A professional web application for scanning Infrastructure as Code (IaC) files for security risks using machine learning.

## Features

- **Single File Analysis**: Upload individual .tf, .yaml, .json, or .bicep files for risk assessment
- **Batch Processing**: Upload ZIP archives containing multiple IaC files for bulk analysis
- **Real-time Risk Scoring**: Get probability scores and binary risk decisions
- **Detailed Explanations**: Understand why files are flagged as risky
- **Professional UI**: Clean, intuitive interface suitable for enterprise use
- **Configurable Thresholds**: Adjust risk sensitivity based on your needs
- **Export Results**: Download analysis results in CSV or JSON format

## Installation

### Local Development

1. Clone the repository:
```bash
git clone <repository-url>
cd CloudGuardAI
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Ensure model artifacts are present:
- `models_artifacts/best_model_lr.joblib`
- `models_artifacts/threshold_lr.json`
- `models_artifacts/cv_metrics_lr.json`
- `features_artifacts/meta.json`

4. Run the application:
```bash
streamlit run app.py
```

5. Open your browser to `http://localhost:8501`

### Docker Deployment

1. Build the Docker image:
```bash
docker build -t cloudguard-ai .
```

2. Run the container:
```bash
docker run -p 8501:8501 cloudguard-ai
```

3. Access the application at `http://localhost:8501`

## Usage

### Single File Mode
1. Select "Single File" in the sidebar
2. Upload a supported IaC file (.tf, .yaml, .yml, .json, .bicep)
3. View the risk assessment and explanation
4. Adjust threshold if needed using the sidebar slider

### Batch Mode
1. Select "Batch Upload" in the sidebar
2. Upload a ZIP file containing your IaC files
3. Click "Analyze ZIP Archive"
4. Review the summary metrics and detailed results table
5. Download results as CSV or JSON

## Model Information

- **Algorithm**: Logistic Regression (liblinear solver)
- **Features**: Sparse hash features from file paths and content, plus dense structural features
- **Performance**: PR-AUC ≈ 0.34, ROC-AUC ≈ 0.97
- **Training Data**: 21,107 IaC files with 2.3% positive rate

## Architecture

```
app.py                          # Main Streamlit application
utils/
├── __init__.py
├── model_loader.py            # Load trained model and artifacts
├── feature_extractor.py       # Extract features from IaC files
└── prediction_engine.py       # Handle predictions and batch processing
models_artifacts/              # Trained model files
features_artifacts/            # Feature metadata
requirements.txt               # Python dependencies
Dockerfile                     # Container configuration
```

## API Reference

### PredictionEngine

Main class for handling predictions:

```python
from utils.prediction_engine import PredictionEngine

engine = PredictionEngine()

# Single file prediction
result = engine.predict_single_file(file_path, content)

# Batch prediction
results = engine.predict_batch(file_data_list)

# Process ZIP file
results = engine.process_zip_file(zip_path)
```

### ModelLoader

Load and manage ML artifacts:

```python
from utils.model_loader import ModelLoader

loader = ModelLoader()
model, threshold, metrics = loader.load_all()
```

### FeatureExtractor

Extract features from IaC files:

```python
from utils.feature_extractor import FeatureExtractor

extractor = FeatureExtractor()
X, feature_info = extractor.extract_features_single(file_path, content)
```

## Configuration

### Environment Variables

- `STREAMLIT_SERVER_PORT`: Port for the web application (default: 8501)
- `STREAMLIT_SERVER_ADDRESS`: Server address (default: 0.0.0.0 for Docker)

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