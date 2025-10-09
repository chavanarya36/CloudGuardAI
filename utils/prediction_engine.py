import os
import zipfile
import tempfile
from pathlib import Path
import pandas as pd
import numpy as np
from .model_loader import ModelLoader
from .feature_extractor import FeatureExtractor

class PredictionEngine:
    """Handle predictions for single files and batch processing."""
    
    def __init__(self):
        self.model_loader = ModelLoader()
        self.model, self.threshold, self.metrics = self.model_loader.load_all()
        expected = getattr(self.model, 'n_features_in_', None)
        self.feature_extractor = FeatureExtractor(expected_total_features=expected)
        self.expected_total = expected
        self._last_shape_report = None
        
    def predict_single_file(self, file_path, content, custom_threshold=None):
        """Predict risk for a single file."""
        # Extract features
        X, feature_info = self.feature_extractor.extract_features_single(file_path, content)
        expected = self.expected_total
        if expected is not None:
            # record diagnostics before alignment
            self._last_shape_report = FeatureExtractor.debug_shape_report(X, expected)
            X = FeatureExtractor.align_to_expected(X, expected)
        
        # Get prediction
        prob = self.model_loader.predict_proba(X)[0]
        threshold = custom_threshold if custom_threshold is not None else self.threshold
        is_risky = prob >= threshold
        
        # Generate explanation
        explanation = self._generate_explanation(feature_info, prob)
        
        result = {
            'file_path': str(file_path),
            'risk_probability': float(prob),
            'risk_percentage': round(prob * 100, 2),
            'is_risky': bool(is_risky),
            'decision_label': '⚠️ High Risk' if is_risky else '✅ Safe',
            'explanation': explanation,
            'feature_info': feature_info
        }
        
        return result
    
    def predict_batch(self, file_data_list, custom_threshold=None):
        """Predict risk for multiple files."""
        if not file_data_list:
            return []
        
        # Extract features for all files
        X, feature_info_list = self.feature_extractor.extract_features_batch(file_data_list)
        expected = self.expected_total
        if expected is not None:
            self._last_shape_report = FeatureExtractor.debug_shape_report(X, expected)
            X = FeatureExtractor.align_to_expected(X, expected)
        
        # Get predictions
        probs = self.model_loader.predict_proba(X)
        threshold = custom_threshold if custom_threshold is not None else self.threshold
        is_risky = probs >= threshold
        
        results = []
        for i, (file_path, content) in enumerate(file_data_list):
            prob = probs[i]
            risky = is_risky[i]
            
            # Generate explanation
            explanation = self._generate_explanation(feature_info_list[i], prob)
            
            result = {
                'file_path': str(file_path),
                'risk_probability': float(prob),
                'risk_percentage': round(prob * 100, 2),
                'is_risky': bool(risky),
                'decision_label': '⚠️ High Risk' if risky else '✅ Safe',
                'explanation': explanation
            }
            results.append(result)
        
        # Sort by risk probability (highest first)
        results.sort(key=lambda x: x['risk_probability'], reverse=True)
        
        return results
    
    def _generate_explanation(self, feature_info, prob):
        """Generate a human-readable explanation for the prediction."""
        explanations = []
        
        # Check resource tokens
        resource_tokens = feature_info.get('resource_tokens', [])
        if resource_tokens:
            high_risk_resources = [t for t in resource_tokens if any(keyword in t.lower() for keyword in 
                                 ['aws_s3', 'aws_iam', 'aws_ec2', 'secret', 'admin', 'root'])]
            if high_risk_resources:
                explanations.append(f"Contains high-risk resources: {', '.join(high_risk_resources[:3])}")
        
        # Check dense features
        dense = feature_info.get('dense_features', {})
        if dense.get('has_test', 0):
            explanations.append("File appears to be test/example code")
        if dense.get('has_ci', 0):
            explanations.append("Contains CI/CD pipeline configuration")
        
        # Check file type
        if dense.get('is_tf', 0):
            explanations.append("Terraform configuration file")
        elif dense.get('is_yaml', 0):
            explanations.append("YAML configuration file")
        
        # Risk level based on probability
        if prob >= 0.8:
            risk_level = "Very high confidence"
        elif prob >= 0.5:
            risk_level = "High confidence"
        elif prob >= 0.2:
            risk_level = "Medium confidence"
        else:
            risk_level = "Low confidence"
        
        if explanations:
            base_explanation = ". ".join(explanations)
            return f"{risk_level}: {base_explanation}"
        else:
            return f"{risk_level} prediction based on file structure and content patterns"
    
    def process_zip_file(self, zip_path, custom_threshold=None):
        """Process a ZIP file containing IaC files."""
        iac_extensions = {'.tf', '.yaml', '.yml', '.json', '.bicep'}
        file_data_list = []
        
        with tempfile.TemporaryDirectory() as temp_dir:
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(temp_dir)
            
            # Find all IaC files
            for root, dirs, files in os.walk(temp_dir):
                for file in files:
                    file_path = Path(root) / file
                    if file_path.suffix.lower() in iac_extensions:
                        try:
                            with open(file_path, 'r', encoding='utf-8') as f:
                                content = f.read()
                            # Use relative path from zip root
                            rel_path = file_path.relative_to(temp_dir)
                            file_data_list.append((str(rel_path), content))
                        except Exception as e:
                            # Skip files that can't be read
                            continue
        
        return self.predict_batch(file_data_list, custom_threshold)
    
    def get_summary_metrics(self, results):
        """Calculate summary metrics for batch results."""
        if not results:
            return {}
        
        total_files = len(results)
        risky_files = sum(1 for r in results if r['is_risky'])
        
        # Calculate precision at different K values
        def precision_at_k(k):
            if k >= total_files:
                return risky_files / total_files if total_files > 0 else 0
            top_k = results[:k]
            return sum(1 for r in top_k if r['is_risky']) / k if k > 0 else 0
        
        summary = {
            'total_files': total_files,
            'risky_files': risky_files,
            'safe_files': total_files - risky_files,
            'risk_rate': round(risky_files / total_files * 100, 2) if total_files > 0 else 0,
            'precision_at_100': round(precision_at_k(100) * 100, 2),
            'precision_at_200': round(precision_at_k(200) * 100, 2),
            'avg_risk_score': round(np.mean([r['risk_probability'] for r in results]) * 100, 2)
        }
        
        return summary
    
    def results_to_dataframe(self, results):
        """Convert results to pandas DataFrame for display and download."""
        if not results:
            return pd.DataFrame()
        
        df_data = []
        for result in results:
            df_data.append({
                'File Path': result['file_path'],
                'Risk Probability (%)': result['risk_percentage'],
                'Decision': result['decision_label'],
                'Explanation': result['explanation']
            })
        
        return pd.DataFrame(df_data)

    def get_last_shape_report(self):
        """Return diagnostics of the most recent feature matrix before alignment."""
        return self._last_shape_report or {}