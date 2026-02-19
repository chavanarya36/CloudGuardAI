import numpy as np
import joblib
import json
from pathlib import Path
from sklearn.linear_model import SGDClassifier
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
from typing import List, Dict, Any, Optional
from datetime import datetime


class ModelRegistry:
    """Track model versions and performance"""
    
    def __init__(self, registry_path: str = "ml/models_artifacts/registry.json"):
        self.registry_path = Path(registry_path)
        self.registry_path.parent.mkdir(parents=True, exist_ok=True)
        self.registry = self._load_registry()
    
    def _load_registry(self) -> Dict[str, Any]:
        """Load registry from disk"""
        if self.registry_path.exists():
            with open(self.registry_path, 'r') as f:
                return json.load(f)
        return {
            "models": [],
            "active_version": None,
            "last_training": None
        }
    
    def save_registry(self):
        """Save registry to disk"""
        with open(self.registry_path, 'w') as f:
            json.dump(self.registry, f, indent=2)
    
    def register_model(
        self,
        version: str,
        model_type: str,
        metrics: Dict[str, float],
        file_path: str,
        training_samples: int,
        metadata: Optional[Dict] = None
    ):
        """Register a new model version"""
        model_info = {
            "version": version,
            "model_type": model_type,
            "accuracy": metrics.get("accuracy"),
            "precision": metrics.get("precision"),
            "recall": metrics.get("recall"),
            "f1_score": metrics.get("f1_score"),
            "training_samples": training_samples,
            "file_path": file_path,
            "created_at": datetime.utcnow().isoformat(),
            "metadata": metadata or {}
        }
        
        self.registry["models"].append(model_info)
        self.registry["last_training"] = datetime.utcnow().isoformat()
        self.save_registry()
    
    def set_active_version(self, version: str):
        """Set the active model version"""
        self.registry["active_version"] = version
        self.save_registry()
    
    def get_active_model(self) -> Optional[Dict]:
        """Get info about active model"""
        active_version = self.registry.get("active_version")
        if not active_version:
            return None
        
        for model in self.registry["models"]:
            if model["version"] == active_version:
                return model
        return None
    
    def get_all_versions(self) -> List[Dict]:
        """Get all model versions"""
        return self.registry.get("models", [])


class OnlineLearner:
    """
    Online learning trainer using SGDClassifier for incremental updates.
    """
    
    def __init__(self, models_dir: str, features_dir: str):
        self.models_dir = Path(models_dir)
        self.features_dir = Path(features_dir)
        self.model_path = self.models_dir / "online_learner.joblib"
        
        # Initialize model registry
        self.registry = ModelRegistry(str(self.models_dir / "registry.json"))
        self.version = "v1.0.0"
        
        # Load or initialize model
        active_model = self.registry.get_active_model()
        if active_model and Path(active_model["file_path"]).exists():
            # Load from registry
            self.model = joblib.load(active_model["file_path"])
            self.version = active_model["version"]
            self._is_fitted = True
        elif self.model_path.exists():
            # Legacy load
            self.model = joblib.load(self.model_path)
            self._is_fitted = True
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
        Extract 40-dim rich features from file content.
        Aligned with the adaptive learning engine's RichFeatureExtractor.
        """
        try:
            return self._extract_rich_features(content, file_path)
        except Exception:
            return self._extract_simple_features(content)

    def _extract_rich_features(self, content: str, filename: str = "") -> np.ndarray:
        """
        Rich 40-dimensional feature vector aligned with the adaptive
        learning engine.  See api/app/adaptive_learning.py for the
        canonical implementation.
        """
        import re
        lower = content.lower()
        lines = content.split("\n")
        features: list = []

        # Structural (5)
        features.append(min(len(content) / 10_000, 10.0))
        features.append(min(len(lines) / 500, 10.0))
        features.append(float(content.count("{")))
        features.append(float(content.count("resource")))
        features.append(float(bool(re.search(r"apiVersion:", content))))

        # Credential signals (8)
        for kw in ["password", "secret", "api_key", "access_key", "private_key",
                    "token", "credential", "auth"]:
            features.append(float(lower.count(kw)))

        # Network signals (8)
        for kw in ["0.0.0.0", "::/0", "public", "ingress", "egress",
                    "security_group", "firewall", "cidr"]:
            features.append(float(lower.count(kw)))

        # Crypto signals (8)
        for kw in ["encrypt", "kms", "ssl", "tls", "https", "certificate",
                    "aes", "sha"]:
            features.append(float(lower.count(kw)))

        # IAM signals (6)
        for kw in ["iam", "role", "policy", "principal", "assume_role", "admin"]:
            features.append(float(lower.count(kw)))

        # Logging/monitoring (5)
        for kw in ["logging", "monitoring", "cloudtrail", "audit", "log_group"]:
            features.append(float(lower.count(kw)))

        features = features[:40]
        while len(features) < 40:
            features.append(0.0)
        return np.array(features, dtype=np.float64)
    
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
    
    def save_model(self, increment_version: bool = True):
        """Save model to disk and update registry."""
        self.models_dir.mkdir(parents=True, exist_ok=True)
        
        if increment_version:
            # Increment version
            major, minor, patch = map(int, self.version.strip('v').split('.'))
            patch += 1
            self.version = f"v{major}.{minor}.{patch}"
        
        # Save with versioned filename
        versioned_path = self.models_dir / f"online_learner_{self.version}.joblib"
        joblib.dump(self.model, versioned_path)
        
        # Also save to default path for backwards compatibility
        joblib.dump(self.model, self.model_path)
        
        return str(versioned_path)
    
    def predict(self, X: np.ndarray) -> np.ndarray:
        """Make predictions."""
        return self.model.predict(X)
    
    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        """Get prediction probabilities."""
        return self.model.predict_proba(X)
    
    def register_training(
        self,
        metrics: Dict[str, float],
        training_samples: int,
        metadata: Optional[Dict] = None
    ):
        """Register training session in registry."""
        model_path = self.save_model(increment_version=True)
        
        self.registry.register_model(
            version=self.version,
            model_type="online_sgd",
            metrics=metrics,
            file_path=model_path,
            training_samples=training_samples,
            metadata=metadata
        )
        
        self.registry.set_active_version(self.version)
    
    def detect_drift(
        self,
        recent_predictions: List[int],
        threshold: float = 0.3
    ) -> Dict[str, Any]:
        """
        Simple drift detection based on prediction distribution.
        
        In production, this would use more sophisticated methods like
        Kolmogorov-Smirnov test or Population Stability Index.
        """
        if len(recent_predictions) < 10:
            return {
                "drift_detected": False,
                "drift_score": 0.0,
                "reason": "Insufficient data"
            }
        
        # Calculate recent positive rate
        recent_positive_rate = np.mean(recent_predictions)
        
        # Compare to expected rate (0.5 for balanced)
        expected_rate = 0.5
        drift_score = abs(recent_positive_rate - expected_rate)
        
        drift_detected = drift_score > threshold
        
        return {
            "drift_detected": drift_detected,
            "drift_score": float(drift_score),
            "recent_positive_rate": float(recent_positive_rate),
            "expected_rate": expected_rate,
            "threshold": threshold,
            "reason": "Significant distribution shift" if drift_detected else "Normal operation"
        }
