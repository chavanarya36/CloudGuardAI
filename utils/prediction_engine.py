import os
import zipfile
import tempfile
import json
import re
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
        # Prefer a triage-budget threshold (e.g., Top-500) if available for UI decisions
        self._load_budget_threshold()

    def _load_budget_threshold(self):
        """Attempt to override default threshold using models_artifacts/threshold_budget.json.
        Prefer a Top-500-style threshold when present to avoid over-flagging at very low base thr.
        """
        try:
            budget_path = Path('models_artifacts') / 'threshold_budget.json'
            if not budget_path.exists():
                return
            with open(budget_path, 'r', encoding='utf-8') as f:
                tb = json.load(f)

            # Helper to locate a numeric threshold value in a flexible structure
            def find_thr(obj, keys):
                for k in keys:
                    if k in obj:
                        v = obj[k]
                        if isinstance(v, dict):
                            # common shapes: {"threshold": 0.215, ...}
                            if 'threshold' in v and isinstance(v['threshold'], (int, float)):
                                return float(v['threshold'])
                        elif isinstance(v, (int, float)):
                            return float(v)
                return None

            # Try a few common key variants
            thr500 = find_thr(tb, [
                'Top-500', 'top_500', 'top500', 'budget_500', 'triage_500'
            ])
            if thr500 is not None and 0 < thr500 < 1:
                self.threshold = float(thr500)
                # Keep loader threshold in sync so UI shows the effective value
                try:
                    self.model_loader.threshold = float(thr500)
                except Exception:
                    pass
        except Exception:
            # Keep original threshold on any error
            pass
        
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

        # Heuristic overlay banding for stability and interpretability
        h_score, h_band, h_reasons = self._heuristic_risk(str(content))
        
        # Generate explanation
        explanation = self._generate_explanation(feature_info, prob)
        
        result = {
            'file_path': str(file_path),
            'filename': Path(str(file_path)).name,
            'risk_probability': float(prob),
            'risk_percentage': round(prob * 100, 2),
            'is_risky': bool(is_risky),
            'decision_label': '⚠️ High Risk' if is_risky else '✅ Safe',
            'risk_band': h_band,
            'heuristic_score': int(h_score),
            'heuristic_reasons': h_reasons,
            'confidence_pct': round(prob * 100, 2),
            'decision_threshold': float(threshold),
            'explanation': explanation,
            'feature_info': feature_info
        }

        # Derive a final unified label prioritizing heuristic band and probability magnitude
        result['final_label'] = self._compose_final_label(result)
        
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
            h_score, h_band, h_reasons = self._heuristic_risk(str(content))
            
            result = {
                'file_path': str(file_path),
                'filename': Path(str(file_path)).name,
                'risk_probability': float(prob),
                'risk_percentage': round(prob * 100, 2),
                'is_risky': bool(risky),
                'decision_label': '⚠️ High Risk' if risky else '✅ Safe',
                'risk_band': h_band,
                'heuristic_score': int(h_score),
                'heuristic_reasons': h_reasons,
                'confidence_pct': round(float(prob) * 100, 2),
                'decision_threshold': float(threshold),
                'explanation': explanation
            }
            result['final_label'] = self._compose_final_label(result)
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

    def _heuristic_risk(self, content: str):
        """Lightweight heuristic to derive a human-friendly risk band.
        High: severe public exposure or explicit public S3
        Medium: some risky defaults (open HTTP, missing enc)
        Low: protective controls present and no 0.0.0.0/0
        """
        try:
            text = content.lower()
        except Exception:
            text = str(content)

        score = 0
        reasons = []

        # Severe exposures
        cidr_any = re.findall(r"\b0\.0\.0\.0/0\b", text)
        if cidr_any:
            score += 2 if len(cidr_any) == 1 else 3
            reasons.append(f"open_cidr_anywhere x{len(cidr_any)}")

        if re.search(r'\bacl\s*=\s*"(public-read|public-read-write)"', text):
            score += 3
            reasons.append("s3_public_acl")

        if 'aws_s3_bucket_public_access_block' in text:
            # If any of the public-block flags is false, penalize
            if re.search(r'block_public_acls\s*=\s*false', text) or \
               re.search(r'block_public_policy\s*=\s*false', text) or \
               re.search(r'ignore_public_acls\s*=\s*false', text) or \
               re.search(r'restrict_public_buckets\s*=\s*false', text):
                score += 2
                reasons.append("s3_public_block_disabled")

        # Missing encryption keywords
        if re.search(r'encrypted\s*=\s*false', text):
            score += 2
            reasons.append("storage_unencrypted")

        # Secret-like tokens
        if re.search(r'akia[a-z0-9]{16}', text) or 'password' in text:
            score += 1
            reasons.append("secret_like_literal")

        # Protective controls (reduce score)
        if 'aws_s3_bucket_server_side_encryption_configuration' in text:
            score -= 3
            reasons.append("s3_sse_enabled")

        if 'aws_s3_bucket_public_access_block' in text:
            if re.search(r'block_public_acls\s*=\s*true', text) and \
               re.search(r'block_public_policy\s*=\s*true', text) and \
               re.search(r'ignore_public_acls\s*=\s*true', text) and \
               re.search(r'restrict_public_buckets\s*=\s*true', text):
                score -= 2
                reasons.append("s3_public_block_all_true")

        # Private-only SG (RFC1918) and no any-open
        if not cidr_any and (
            re.search(r'cidr_blocks\s*=\s*\[.*10\.', text) or
            re.search(r'cidr_blocks\s*=\s*\[.*192\.168\.', text) or
            re.search(r'cidr_blocks\s*=\s*\[.*172\.(1[6-9]|2\d|3[0-1])\.', text)
        ):
            score -= 1
            reasons.append("sg_rfc1918_only")

        # Map to band
        score = max(-5, min(5, score))
        if score >= 4:
            band = "High Risk"
        elif score >= 1:
            band = "Medium Risk"
        else:
            band = "Low Risk"
        return score, band, reasons

    def _compose_final_label(self, r):
        """Compose a final human-facing label blending heuristic band & model confidence.
        Rules:
          - If probability extremely low (< 0.02) always Low Risk unless heuristic High.
          - Elevate to High only if (band High AND prob >= max(decision_threshold*1.5, 0.08)).
          - Medium band with low prob (<0.05) becomes Low (monitor) to reduce noise.
          - Provide suffix for low-confidence high flags.
        """
        prob = r.get('risk_probability', 0.0)
        thr = r.get('decision_threshold', self.threshold or 0.05)
        band = r.get('risk_band') or 'Unknown'

        # Extreme low probability guard
        if prob < 0.02 and band != 'High Risk':
            return '✅ Low Risk'

        if band == 'High Risk':
            if prob >= max(thr * 1.5, 0.08):
                return '🚨 High Risk'
            else:
                return '⚠️ Potential High Risk (Low Confidence)'
        elif band == 'Medium Risk':
            if prob < 0.05:
                return '🟡 Medium (Low Confidence)'
            return '🟠 Medium Risk'
        elif band == 'Low Risk':
            return '✅ Low Risk'
        return band
    
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
                'Risk Band': result.get('risk_band', ''),
                'Final Label': result.get('final_label',''),
                'Explanation': result['explanation']
            })
        
        return pd.DataFrame(df_data)

    def get_last_shape_report(self):
        """Return diagnostics of the most recent feature matrix before alignment."""
        return self._last_shape_report or {}