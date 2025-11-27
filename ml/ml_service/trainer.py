import numpy as np
import joblib
from pathlib import Path
from sklearn.linear_model import SGDClassifier
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
from typing import List, Dict, Any
from datetime import datetime


class OnlineLearner:
    """
    Online learning trainer using SGDClassifier for incremental updates.
    """
    
    def __init__(self, models_dir: str, features_dir: str):
        self.models_dir = Path(models_dir)
        self.features_dir = Path(features_dir)
        self.model_path = self.models_dir / "online_learner.joblib"
        
        # Load or initialize model
        if self.model_path.exists():
            self.model = joblib.load(self.model_path)
        else:
            # Initialize SGDClassifier with good defaults
            self.model = SGDClassifier(
                loss='log_loss',  # Logistic regression
                penalty='l2',
                alpha=0.0001,
                max_iter=1000,
                random_state=42,
                warm_start=True
            )
            self._is_fitted = False
    
    def extract_features(self, file_path: str, content: str) -> np.ndarray:
        """
        Extract features from file content using existing feature extractor.
        """
        try:
            # Import feature extractor
            import sys
            parent_dir = Path(__file__).parent.parent.parent
            sys.path.insert(0, str(parent_dir))
            
            from pipeline.feature_extractor import extract_features_from_content
            
            features = extract_features_from_content(
                file_path=file_path,
                content=content
            )
            
            return features
            
        except Exception as e:
            # Fallback to simple features
            return self._extract_simple_features(content)
    
    def _extract_simple_features(self, content: str) -> np.ndarray:
        """
        Simple feature extraction fallback.
        """
        features = [
            len(content),
            content.count('\n'),
            content.count('password'),
            content.count('secret'),
            content.count('api_key'),
            content.count('private'),
            content.count('public'),
            content.count('*'),
            content.count('0.0.0.0'),
            content.count('http://'),
        ]
        return np.array(features)
    
    def partial_fit(self, X: List[np.ndarray], y: List[int]) -> Dict[str, Any]:
        """
        Perform partial fit on new data.
        """
        X_array = np.array(X)
        y_array = np.array(y)
        
        # Partial fit
        if not hasattr(self, '_is_fitted') or not self._is_fitted:
            # First fit needs classes parameter
            self.model.partial_fit(X_array, y_array, classes=np.array([0, 1]))
            self._is_fitted = True
        else:
            self.model.partial_fit(X_array, y_array)
        
        # Calculate metrics on training data (for monitoring)
        y_pred = self.model.predict(X_array)
        
        metrics = {
            'accuracy': float(accuracy_score(y_array, y_pred)),
            'precision': float(precision_score(y_array, y_pred, average='binary', zero_division=0)),
            'recall': float(recall_score(y_array, y_pred, average='binary', zero_division=0)),
            'f1_score': float(f1_score(y_array, y_pred, average='binary', zero_division=0)),
            'metadata': {
                'timestamp': datetime.utcnow().isoformat(),
                'samples': len(y_array),
                'positive_samples': int(np.sum(y_array)),
                'negative_samples': int(len(y_array) - np.sum(y_array))
            }
        }
        
        return metrics
    
    def save_model(self):
        """Save model to disk."""
        self.models_dir.mkdir(parents=True, exist_ok=True)
        joblib.dump(self.model, self.model_path)
    
    def predict(self, X: np.ndarray) -> np.ndarray:
        """Make predictions."""
        return self.model.predict(X)
    
    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        """Get prediction probabilities."""
        return self.model.predict_proba(X)
