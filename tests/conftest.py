"""Pytest configuration and shared fixtures for CloudGuard AI tests"""
import os
import sys
import tempfile
import pytest
import pytest_asyncio
from pathlib import Path
from typing import AsyncGenerator
from unittest.mock import Mock, patch
from httpx import AsyncClient, ASGITransport
from asgi_lifespan import LifespanManager

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
# Add api/ directory so `from app.xxx` imports work
sys.path.insert(0, str(project_root / "api"))
# Add rules/ directory so `import rules_engine` works
sys.path.insert(0, str(project_root / "rules"))
# Add ml/ directory so `from ml.models.xxx` imports work
sys.path.insert(0, str(project_root / "ml"))


@pytest.fixture
def tmp_path_factory_session(tmp_path_factory):
    """Session-scoped temp directory"""
    return tmp_path_factory.mktemp("test_session")


@pytest.fixture
def sample_terraform_file():
    """Sample Terraform file content for testing"""
    return """
resource "aws_s3_bucket" "test" {
  bucket = "test-bucket"
  acl    = "public-read"
}

resource "aws_security_group" "test" {
  name = "test-sg"
  
  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }
}
"""


@pytest.fixture
def sample_iac_files(tmp_path):
    """Create sample IaC files for testing"""
    files = {}
    
    # Terraform file
    tf_file = tmp_path / "test.tf"
    tf_file.write_text("""
resource "aws_s3_bucket" "example" {
  bucket = "test-bucket"
  acl    = "public-read"
}
""")
    files['terraform'] = str(tf_file)
    
    # CloudFormation file
    cf_file = tmp_path / "test.yaml"
    cf_file.write_text("""
Resources:
  S3Bucket:
    Type: AWS::S3::Bucket
    Properties:
      BucketName: test-bucket
      AccessControl: PublicRead
""")
    files['cloudformation'] = str(cf_file)
    
    return files


@pytest.fixture(autouse=True)
def mock_llm_reasoner(monkeypatch):
    """Mock LLM reasoner to return deterministic results (auto-applied to all tests)"""
    def fake_call_llm(prompt, **kwargs):
        return "Deterministic LLM result. Certainty: 0.60"
    
    mock_explain = Mock(return_value={
        'certainty': 0.85,
        'explanation': 'Test explanation for security issue',
        'remediation': 'Test remediation steps',
        'severity_adjustment': None
    })
    
    # Patch the LLM reasoner if it exists
    try:
        monkeypatch.setattr('rules.rules_engine.llm_reasoner.explain_finding', mock_explain)
        monkeypatch.setattr('rules.rules_engine.llm_reasoner._call_llm', fake_call_llm)
    except (ImportError, AttributeError):
        pass  # LLM reasoner not available in this context
    
    return mock_explain


@pytest.fixture
def test_db_url(tmp_path):
    """In-memory SQLite database URL for testing"""
    db_file = tmp_path / "test.db"
    return f"sqlite:///{db_file}"


@pytest.fixture
def mock_ml_model():
    """Mock ML model that returns deterministic predictions"""
    mock_model = Mock()
    mock_model.predict.return_value = [1]  # Positive prediction
    mock_model.predict_proba.return_value = [[0.3, 0.7]]  # 70% confidence
    return mock_model


@pytest_asyncio.fixture
async def async_api_client() -> AsyncGenerator[AsyncClient, None]:
    """Async HTTP client for API service using httpx and LifespanManager"""
    try:
        sys.path.insert(0, str(project_root / "api"))
        from test_server import app
        async with LifespanManager(app):
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as client:
                yield client
    except ImportError:
        pytest.skip("FastAPI or API service not available")


@pytest_asyncio.fixture
async def async_ml_client() -> AsyncGenerator[AsyncClient, None]:
    """Async HTTP client for ML service using httpx and LifespanManager"""
    try:
        sys.path.insert(0, str(project_root / "ml"))
        from ml_service.main import app
        async with LifespanManager(app):
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as client:
                yield client
    except ImportError:
        pytest.skip("ML service not available")


@pytest.fixture
def api_client(async_api_client):
    """Sync wrapper for API client (for tests that need sync access)"""
    return async_api_client


@pytest.fixture
def ml_client(async_ml_client):
    """Sync wrapper for ML client (for tests that need sync access)"""
    return async_ml_client


@pytest.fixture(autouse=True)
def reset_environment():
    """Reset environment variables before each test"""
    original_env = os.environ.copy()
    yield
    os.environ.clear()
    os.environ.update(original_env)


@pytest.fixture
def mock_checkov_scan():
    """Mock Checkov scanning to return deterministic results"""
    mock_result = {
        'results': {
            'failed_checks': [
                {
                    'check_id': 'CKV_AWS_20',
                    'check_name': 'S3 Bucket has an ACL defined which allows public READ access',
                    'file_path': '/test.tf',
                    'file_line_range': [1, 5],
                    'resource': 'aws_s3_bucket.test',
                    'check_class': 'checkov.terraform.checks.resource.aws.S3PublicACLRead',
                    'guideline': 'https://docs.bridgecrew.io/docs/s3_1-acl-read-permissions-everyone'
                }
            ],
            'passed_checks': [],
            'skipped_checks': [],
            'parsing_errors': []
        }
    }
    return mock_result


@pytest.fixture
def capture_logs(caplog):
    """Capture logs for assertion"""
    import logging
    caplog.set_level(logging.INFO)
    return caplog


@pytest.fixture
def temp_model_dir(tmp_path):
    """Temporary directory for model artifacts"""
    model_dir = tmp_path / "models"
    model_dir.mkdir()
    return str(model_dir)


@pytest.fixture
def temp_features_dir(tmp_path):
    """Temporary directory for feature artifacts"""
    features_dir = tmp_path / "features"
    features_dir.mkdir()
    return str(features_dir)


@pytest.fixture
def temp_registry_path(tmp_path):
    """Temporary path for model registry"""
    return str(tmp_path / "registry.json")


@pytest.fixture
def sample_training_data():
    """Sample training data for online learning tests"""
    import numpy as np
    return {
        'X': [np.random.randn(100) for _ in range(10)],
        'y': [0, 1, 0, 1, 1, 0, 1, 0, 1, 0]
    }


@pytest.fixture
def mock_requests(monkeypatch):
    """Mock requests library for external API calls"""
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {'status': 'ok'}
    
    mock_get = Mock(return_value=mock_response)
    mock_post = Mock(return_value=mock_response)
    
    monkeypatch.setattr('requests.get', mock_get)
    monkeypatch.setattr('requests.post', mock_post)
    
    return {'get': mock_get, 'post': mock_post}
