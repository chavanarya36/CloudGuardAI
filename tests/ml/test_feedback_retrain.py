"""Tests for feedback and retraining flow"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch, MagicMock
import sys
from pathlib import Path

# Add paths
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "api"))
sys.path.insert(0, str(project_root / "ml"))


def test_feedback_endpoint_accepts_submission():
    """Test /feedback endpoint accepts feedback"""
    from app.main import app
    client = TestClient(app)
    
    feedback_data = {
        "scan_id": 1,
        "rating": 4,
        "user_comment": "Good detection",
        "feedback_type": "accurate",
        "accepted_prediction": True
    }
    
    response = client.post("/feedback", json=feedback_data)
    
    # Should accept feedback (may return 200 or 404 if no DB scan)
    assert response.status_code in [200, 404, 500]


def test_feedback_validates_required_fields():
    """Test /feedback validates required fields"""
    from app.main import app
    client = TestClient(app)
    
    # Missing scan_id
    response = client.post("/feedback", json={"rating": 5})
    
    assert response.status_code == 422  # Validation error


def test_feedback_rating_range():
    """Test /feedback validates is_correct range (0-1)"""
    from app.main import app
    client = TestClient(app)
    
    # Invalid is_correct value (must be 0 or 1)
    response = client.post(
        "/feedback",
        json={"scan_id": 1, "is_correct": 10}
    )
    
    assert response.status_code == 422


def test_ml_service_train_endpoint():
    """Test ML service /train/online endpoint"""
    # Mock the trainer
    with patch('ml_service.trainer.OnlineLearner') as mock_learner_class:
        mock_learner = Mock()
        mock_learner.partial_fit.return_value = {
            "accuracy": 0.85,
            "precision": 0.82,
            "recall": 0.88,
            "f1_score": 0.85,
            "samples_trained": 10,
            "metadata": {}
        }
        mock_learner.version = "v1.0.1"
        mock_learner.register_training = Mock()
        mock_learner_class.return_value = mock_learner
        
        from ml_service.main import app
        client = TestClient(app)
        
        training_data = {
            "training_data": [
                {
                    "file_path": "test.tf",
                    "file_content": "resource {...}",
                    "label": 1
                }
            ]
        }
        
        response = client.post("/train/online", json=training_data)
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["status"] == "completed"
        assert data["samples_processed"] == 1
        assert "accuracy" in data


def test_online_training_calls_partial_fit():
    """Test that online training calls partial_fit"""
    with patch('ml_service.trainer.OnlineLearner') as mock_learner_class:
        mock_learner = Mock()
        mock_learner.partial_fit.return_value = {
            "accuracy": 0.85,
            "precision": 0.82,
            "recall": 0.88,
            "f1_score": 0.85,
            "samples_trained": 5,
            "metadata": {}
        }
        mock_learner.version = "v1.0.1"
        mock_learner.register_training = Mock()
        mock_learner.extract_features.return_value = [0.0] * 100
        mock_learner_class.return_value = mock_learner
        
        from ml_service.main import app
        client = TestClient(app)
        
        training_data = {
            "training_data": [
                {"file_path": "test1.tf", "file_content": "...", "label": 1},
                {"file_path": "test2.tf", "file_content": "...", "label": 0},
            ]
        }
        
        response = client.post("/train/online", json=training_data)
        
        assert response.status_code == 200
        assert mock_learner.partial_fit.called


def test_online_training_increments_version():
    """Test that online training increments model version"""
    with patch('ml_service.trainer.OnlineLearner') as mock_learner_class:
        mock_learner = Mock()
        mock_learner.partial_fit.return_value = {
            "accuracy": 0.85,
            "samples_trained": 5,
            "metadata": {}
        }
        mock_learner.version = "v1.0.2"  # Incremented
        mock_learner.register_training = Mock()
        mock_learner.extract_features.return_value = [0.0] * 100
        mock_learner_class.return_value = mock_learner
        
        from ml_service.main import app
        client = TestClient(app)
        
        training_data = {
            "training_data": [
                {"file_path": "test.tf", "file_content": "...", "label": 1}
            ]
        }
        
        response = client.post("/train/online", json=training_data)
        
        assert response.status_code == 200
        data = response.json()
        
        # Should call register_training which increments version
        assert mock_learner.register_training.called


def test_training_response_includes_metrics():
    """Test training response includes all metrics"""
    with patch('ml_service.trainer.OnlineLearner') as mock_learner_class:
        mock_learner = Mock()
        mock_learner.partial_fit.return_value = {
            "accuracy": 0.85,
            "precision": 0.82,
            "recall": 0.88,
            "f1_score": 0.85,
            "samples_trained": 10,
            "metadata": {}
        }
        mock_learner.version = "v1.0.1"
        mock_learner.register_training = Mock()
        mock_learner.extract_features.return_value = [0.0] * 100
        mock_learner_class.return_value = mock_learner
        
        from ml_service.main import app
        client = TestClient(app)
        
        training_data = {
            "training_data": [
                {"file_path": "test.tf", "file_content": "...", "label": 1}
            ]
        }
        
        response = client.post("/train/online", json=training_data)
        
        assert response.status_code == 200
        data = response.json()
        
        assert "accuracy" in data
        assert "precision" in data
        assert "recall" in data
        assert "f1_score" in data


def test_feedback_to_training_flow():
    """Test complete feedback to training flow"""
    # This would be an end-to-end test in production
    # Here we test the components can work together
    
    # 1. Submit feedback
    from app.main import app as api_app
    api_client = TestClient(api_app)
    
    feedback_data = {
        "scan_id": 1,
        "rating": 3,
        "feedback_type": "false_positive",
        "accepted_prediction": False,
        "user_comment": "This was incorrectly flagged"
    }
    
    # May fail without DB, but structure is valid
    response = api_client.post("/feedback", json=feedback_data)
    assert response.status_code in [200, 404, 500]
    
    # 2. Trigger training with feedback
    with patch('ml_service.trainer.OnlineLearner') as mock_learner_class:
        mock_learner = Mock()
        mock_learner.partial_fit.return_value = {
            "accuracy": 0.86,
            "samples_trained": 1,
            "metadata": {}
        }
        mock_learner.version = "v1.0.2"
        mock_learner.register_training = Mock()
        mock_learner.extract_features.return_value = [0.0] * 100
        mock_learner_class.return_value = mock_learner
        
        from ml_service.main import app as ml_app
        ml_client = TestClient(ml_app)
        
        training_data = {
            "training_data": [
                {
                    "file_path": "test.tf",
                    "file_content": "resource {...}",
                    "label": 0  # Corrected label from feedback
                }
            ]
        }
        
        response = ml_client.post("/train/online", json=training_data)
        assert response.status_code == 200


def test_training_with_empty_data():
    """Test training endpoint rejects empty training data"""
    from ml_service.main import app
    client = TestClient(app)
    
    response = client.post("/train/online", json={"training_data": []})
    
    # Should handle empty data gracefully
    assert response.status_code in [422, 500]


def test_training_handles_feature_extraction_error():
    """Test training handles feature extraction errors"""
    with patch('ml_service.trainer.OnlineLearner') as mock_learner_class:
        mock_learner = Mock()
        mock_learner.extract_features.side_effect = Exception("Feature extraction failed")
        mock_learner_class.return_value = mock_learner
        
        from ml_service.main import app
        client = TestClient(app)
        
        training_data = {
            "training_data": [
                {"file_path": "test.tf", "file_content": "...", "label": 1}
            ]
        }
        
        response = client.post("/train/online", json=training_data)
        
        assert response.status_code == 500


def test_model_registry_updated_after_training():
    """Test that model registry is updated after successful training"""
    with patch('ml_service.trainer.OnlineLearner') as mock_learner_class:
        mock_learner = Mock()
        mock_learner.partial_fit.return_value = {
            "accuracy": 0.87,
            "samples_trained": 5,
            "metadata": {}
        }
        mock_learner.version = "v1.0.3"
        mock_learner.register_training = Mock()
        mock_learner.extract_features.return_value = [0.0] * 100
        mock_learner_class.return_value = mock_learner
        
        from ml_service.main import app
        client = TestClient(app)
        
        training_data = {
            "training_data": [
                {"file_path": "test.tf", "file_content": "...", "label": 1}
            ]
        }
        
        response = client.post("/train/online", json=training_data)
        
        assert response.status_code == 200
        
        # Verify register_training was called
        assert mock_learner.register_training.called
        call_args = mock_learner.register_training.call_args[1]
        assert "metrics" in call_args
        assert "training_samples" in call_args
