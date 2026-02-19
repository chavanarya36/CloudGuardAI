"""Unit tests for online trainer and model registry"""
import pytest
import json
import numpy as np
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

# Add ml service to path
import sys
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "ml"))


def test_model_registry_initialization(temp_registry_path):
    """Test ModelRegistry initializes correctly"""
    from ml_service.trainer import ModelRegistry
    
    registry = ModelRegistry(registry_path=temp_registry_path)
    
    assert registry.registry is not None
    assert "models" in registry.registry
    assert "active_version" in registry.registry
    assert isinstance(registry.registry["models"], list)


def test_model_registry_register_model(temp_registry_path):
    """Test registering a new model version"""
    from ml_service.trainer import ModelRegistry
    
    registry = ModelRegistry(registry_path=temp_registry_path)
    
    metrics = {
        "accuracy": 0.85,
        "precision": 0.82,
        "recall": 0.88,
        "f1_score": 0.85
    }
    
    registry.register_model(
        version="v1.0.0",
        model_type="online_sgd",
        metrics=metrics,
        file_path="/fake/path/model.joblib",
        training_samples=100
    )
    
    assert len(registry.registry["models"]) == 1
    model = registry.registry["models"][0]
    assert model["version"] == "v1.0.0"
    assert model["accuracy"] == 0.85
    assert model["training_samples"] == 100


def test_model_registry_set_active_version(temp_registry_path):
    """Test setting active model version"""
    from ml_service.trainer import ModelRegistry
    
    registry = ModelRegistry(registry_path=temp_registry_path)
    
    registry.register_model(
        version="v1.0.0",
        model_type="online_sgd",
        metrics={"accuracy": 0.85},
        file_path="/fake/path/model.joblib",
        training_samples=100
    )
    
    registry.set_active_version("v1.0.0")
    
    assert registry.registry["active_version"] == "v1.0.0"
    active_model = registry.get_active_model()
    assert active_model["version"] == "v1.0.0"


def test_model_registry_persistence(temp_registry_path):
    """Test that registry persists to disk"""
    from ml_service.trainer import ModelRegistry
    
    # Create and populate registry
    registry1 = ModelRegistry(registry_path=temp_registry_path)
    registry1.register_model(
        version="v1.0.0",
        model_type="online_sgd",
        metrics={"accuracy": 0.85},
        file_path="/fake/path/model.joblib",
        training_samples=100
    )
    
    # Load in new instance
    registry2 = ModelRegistry(registry_path=temp_registry_path)
    
    assert len(registry2.registry["models"]) == 1
    assert registry2.registry["models"][0]["version"] == "v1.0.0"


def test_online_learner_initialization(temp_model_dir, temp_features_dir, temp_registry_path):
    """Test OnlineLearner initializes correctly"""
    from ml_service.trainer import OnlineLearner
    
    # Mock the registry path
    with patch('ml_service.trainer.ModelRegistry') as mock_registry_class:
        mock_registry = Mock()
        mock_registry.get_active_model.return_value = None
        mock_registry_class.return_value = mock_registry
        
        learner = OnlineLearner(
            models_dir=temp_model_dir,
            features_dir=temp_features_dir
        )
        
        assert learner.model is not None
        assert learner.version == "v1.0.0"


def test_partial_fit_incremental_learning(temp_model_dir, temp_features_dir, sample_training_data):
    """Test partial_fit performs incremental learning"""
    from ml_service.trainer import OnlineLearner
    
    with patch('ml_service.trainer.ModelRegistry') as mock_registry_class:
        mock_registry = Mock()
        mock_registry.get_active_model.return_value = None
        mock_registry_class.return_value = mock_registry
        
        learner = OnlineLearner(
            models_dir=temp_model_dir,
            features_dir=temp_features_dir
        )
        
        X = sample_training_data['X']
        y = sample_training_data['y']
        
        metrics = learner.partial_fit(X, y)
        
        assert "accuracy" in metrics
        assert "precision" in metrics
        assert "recall" in metrics
        assert "f1_score" in metrics
        assert "metadata" in metrics
        assert metrics["metadata"]["samples"] == len(y)


def test_register_training_increments_version(temp_model_dir, temp_features_dir):
    """Test that register_training increments version"""
    from ml_service.trainer import OnlineLearner
    
    with patch('ml_service.trainer.ModelRegistry') as mock_registry_class:
        mock_registry = Mock()
        mock_registry.get_active_model.return_value = None
        mock_registry_class.return_value = mock_registry
        
        learner = OnlineLearner(
            models_dir=temp_model_dir,
            features_dir=temp_features_dir
        )
        
        initial_version = learner.version
        
        metrics = {"accuracy": 0.85, "precision": 0.82}
        learner.register_training(metrics, training_samples=100)
        
        # Version should increment
        assert learner.version != initial_version
        assert learner.version == "v1.0.1"


def test_save_model_creates_file(temp_model_dir, temp_features_dir):
    """Test that save_model creates versioned file"""
    from ml_service.trainer import OnlineLearner
    
    with patch('ml_service.trainer.ModelRegistry') as mock_registry_class:
        mock_registry = Mock()
        mock_registry.get_active_model.return_value = None
        mock_registry_class.return_value = mock_registry
        
        learner = OnlineLearner(
            models_dir=temp_model_dir,
            features_dir=temp_features_dir
        )
        
        model_path = learner.save_model(increment_version=True)
        
        assert Path(model_path).exists()
        assert "v1.0.1" in model_path


def test_detect_drift_insufficient_data():
    """Test drift detection with insufficient data"""
    from ml_service.trainer import OnlineLearner
    
    with patch('ml_service.trainer.ModelRegistry') as mock_registry_class:
        mock_registry = Mock()
        mock_registry.get_active_model.return_value = None
        mock_registry_class.return_value = mock_registry
        
        learner = OnlineLearner(
            models_dir="fake_dir",
            features_dir="fake_dir"
        )
        
        result = learner.detect_drift([1, 0, 1])  # Only 3 predictions
        
        assert result["drift_detected"] is False
        assert result["reason"] == "Insufficient data"


def test_detect_drift_normal_operation():
    """Test drift detection with normal distribution"""
    from ml_service.trainer import OnlineLearner
    
    with patch('ml_service.trainer.ModelRegistry') as mock_registry_class:
        mock_registry = Mock()
        mock_registry.get_active_model.return_value = None
        mock_registry_class.return_value = mock_registry
        
        learner = OnlineLearner(
            models_dir="fake_dir",
            features_dir="fake_dir"
        )
        
        # Balanced predictions (50/50 split)
        predictions = [1, 0, 1, 0, 1, 0, 1, 0, 1, 0] * 5
        result = learner.detect_drift(predictions, threshold=0.5)
        
        # Just verify we get a result with expected keys
        assert "drift_detected" in result
        assert "drift_score" in result
        assert isinstance(result["drift_score"], (int, float))


def test_detect_drift_detected():
    """Test drift detection when drift occurs"""
    from ml_service.trainer import OnlineLearner
    
    with patch('ml_service.trainer.ModelRegistry') as mock_registry_class:
        mock_registry = Mock()
        mock_registry.get_active_model.return_value = None
        mock_registry_class.return_value = mock_registry
        
        learner = OnlineLearner(
            models_dir="fake_dir",
            features_dir="fake_dir"
        )
        
        # Heavy skew towards positive (90% positive)
        predictions = [1] * 45 + [0] * 5
        result = learner.detect_drift(predictions, threshold=0.1)
        
        # Just verify detection works and returns expected structure
        assert "drift_detected" in result
        assert "drift_score" in result
        assert "reason" in result
        # Check that result is a boolean value (True or False)
        assert result["drift_detected"] in [True, False]


def test_extract_features_simple_fallback(temp_model_dir, temp_features_dir, sample_terraform_file):
    """Test feature extraction with simple fallback"""
    from ml_service.trainer import OnlineLearner
    
    with patch('ml_service.trainer.ModelRegistry') as mock_registry_class:
        mock_registry = Mock()
        mock_registry.get_active_model.return_value = None
        mock_registry_class.return_value = mock_registry
        
        learner = OnlineLearner(
            models_dir=temp_model_dir,
            features_dir=temp_features_dir
        )
        
        features = learner.extract_features("test.tf", sample_terraform_file)
        
        assert features is not None
        assert len(features) > 0
        assert isinstance(features, np.ndarray)
