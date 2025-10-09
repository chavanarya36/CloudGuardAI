import json
import joblib
import numpy as np
import pandas as pd
from pathlib import Path
import os

class ModelLoader:
    """Load and manage the trained CloudGuard AI model and artifacts."""
    
    def __init__(self, models_dir='models_artifacts'):
        self.models_dir = Path(models_dir)
        self.model = None
        self.threshold = None
        self.metrics = None
        
    def load_model(self):
        """Load the trained logistic regression model."""
        model_path = self.models_dir / 'best_model_lr.joblib'
        if not model_path.exists():
            raise FileNotFoundError(f"Model not found at {model_path}")
        self.model = joblib.load(model_path)
        return self.model
    
    def load_threshold(self):
        """Load the global threshold for decision making."""
        threshold_path = self.models_dir / 'threshold_lr.json'
        if not threshold_path.exists():
            raise FileNotFoundError(f"Threshold file not found at {threshold_path}")
        with open(threshold_path, 'r') as f:
            data = json.load(f)
        self.threshold = data.get('threshold_global', 0.055)
        return self.threshold
    
    def load_metrics(self):
        """Load model performance metrics."""
        metrics_path = self.models_dir / 'cv_metrics_lr.json'
        if not metrics_path.exists():
            raise FileNotFoundError(f"Metrics file not found at {metrics_path}")
        with open(metrics_path, 'r') as f:
            self.metrics = json.load(f)
        return self.metrics
    
    def load_all(self):
        """Load model, threshold, and metrics."""
        self.load_model()
        self.load_threshold()
        self.load_metrics()
        return self.model, self.threshold, self.metrics
    
    def predict_proba(self, X):
        """Get prediction probabilities."""
        if self.model is None:
            raise ValueError("Model not loaded. Call load_model() first.")
        return self.model.predict_proba(X)[:, 1]
    
    def predict(self, X, threshold=None):
        """Make binary predictions using threshold."""
        if threshold is None:
            threshold = self.threshold
        if threshold is None:
            raise ValueError("Threshold not set. Call load_threshold() first.")
        probs = self.predict_proba(X)
        return (probs >= threshold).astype(int)
    
    def get_model_info(self):
        """Get formatted model information for display."""
        if self.metrics is None:
            self.load_metrics()
        
        info = {
            'model_type': 'Logistic Regression (liblinear)',
            'pr_auc': round(self.metrics.get('oof_ap', 0), 4),
            'roc_auc': round(self.metrics.get('oof_roc', 0), 4),
            'balanced_accuracy': round(self.metrics.get('oof_bal_acc', 0), 4),
            'threshold': round(self.threshold, 4) if self.threshold else 0.055
        }
        return info