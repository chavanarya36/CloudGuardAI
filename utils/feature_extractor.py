import os
import re
import json
import numpy as np
from pathlib import Path
from scipy import sparse
from sklearn.feature_extraction import FeatureHasher

class FeatureExtractor:
    """Extract features from IaC files with alignment to model expected dimensions.

    Adaptive logic:
      - Reads feature meta (if present) to determine hash_dim and dense feature names.
      - Falls back to defaults but records chosen ordering for deterministic inference.
      - Provides method to pad/truncate a produced feature matrix to match an external
        expected size (model.n_features_in_).
    """

    DEFAULT_HASH_DIM = 32768
    FALLBACK_DENSE_ORDER = [
        # Keep stable ordering; extend carefully if adding new features.
        'log_size', 'log_lines', 'path_depth',
        'is_tf', 'is_yaml', 'is_json', 'is_bicep',
        'has_test', 'has_ci'
    ]

    def __init__(self, features_dir='features_artifacts', expected_total_features: int | None = None):
        self.features_dir = Path(features_dir)
        self.meta = self._load_meta()
        self.hash_dim = int(self.meta.get('hash_dim', self.DEFAULT_HASH_DIM))

        # Determine dense ordering from meta if available
        dense_meta = self.meta.get('dense_meta') or []
        meta_dense_names = [d.get('name') for d in dense_meta if d.get('name')]
        if meta_dense_names:
            self.dense_order = meta_dense_names
        else:
            self.dense_order = self.FALLBACK_DENSE_ORDER

        self.dense_count = len(self.dense_order)

        # If model expected features supplied & mismatch with meta totals, adjust strategy.
        self.expected_total = expected_total_features
        if self.expected_total is not None:
            # If expected < current hash_dim, assume training used smaller hash space.
            if self.expected_total < self.hash_dim:
                # Reduce hash_dim keeping dense_count identical if possible.
                tentative_hash = self.expected_total - self.dense_count
                if tentative_hash > 0:
                    self.hash_dim = tentative_hash
            # If expected > current computed, padding will occur downstream.

        # Use dict mode (token -> 1) for reproducible ordering independent of token list ordering
        self.hasher = FeatureHasher(n_features=self.hash_dim, input_type='dict')

    def _load_meta(self):
        meta_path_candidates = [self.features_dir / 'feature_meta.json', self.features_dir / 'meta.json']
        for mp in meta_path_candidates:
            if mp.exists():
                try:
                    with open(mp, 'r') as f:
                        return json.load(f)
                except Exception:
                    continue
        return {}
    
    def extract_path_tokens(self, file_path):
        """Extract path-based tokens (segments, 2-grams, char 3-grams)."""
        tokens = []
        
        # Normalize path
        path_str = str(file_path).replace('\\', '/').lower()
        
        # Path segments
        segments = [s for s in path_str.split('/') if s]
        tokens.extend([f'seg_{s}' for s in segments])
        
        # 2-grams of segments
        for i in range(len(segments) - 1):
            tokens.append(f'2gram_{segments[i]}_{segments[i+1]}')
        
        # Character 3-grams of filename
        filename = Path(file_path).name.lower()
        for i in range(len(filename) - 2):
            tokens.append(f'char3_{filename[i:i+3]}')
        
        return tokens
    
    def extract_resource_tokens(self, content):
        """Extract resource-specific tokens from file content."""
        if not content:
            return []
        
        content_lower = content.lower()
        tokens = []
        
        # AWS resources
        aws_patterns = [
            r'aws_\w+', r'resource\s*"aws_\w+"', r'\.aws\.', r'amazonaws\.com',
            r'ec2', r's3', r'rds', r'lambda', r'iam', r'vpc'
        ]
        
        # Kubernetes resources
        k8s_patterns = [
            r'apiversion:', r'kind:', r'metadata:', r'spec:', r'deployment',
            r'service', r'ingress', r'configmap', r'secret', r'namespace'
        ]
        
        # Terraform specific
        tf_patterns = [
            r'resource\s*"', r'data\s*"', r'variable\s*"', r'output\s*"',
            r'provider\s*"', r'module\s*"'
        ]
        
        all_patterns = aws_patterns + k8s_patterns + tf_patterns
        
        for pattern in all_patterns:
            matches = re.findall(pattern, content_lower)
            for match in matches:
                tokens.append(f'resource_{match.replace(" ", "_")}')
        
        return tokens
    
    def extract_dense_features(self, file_path, content):
        """Extract dense structural features (return dict aligned by self.dense_order)."""
        features = {}
        size = len(content.encode('utf-8')) if content else 0
        lines = len(content.split('\n')) if content else 0
        ext = Path(file_path).suffix.lower()
        path_depth = len(Path(file_path).parts)
        content_lower = content.lower() if content else ''

        # Base features (matching earlier names; map to meta if possible)
        features['log_size'] = float(np.log1p(size))
        features['log_lines'] = float(np.log1p(lines))
        features['path_depth'] = path_depth
        features['is_tf'] = int(ext == '.tf')
        features['is_yaml'] = int(ext in ['.yaml', '.yml'])
        features['is_json'] = int(ext == '.json')
        features['is_bicep'] = int(ext == '.bicep')
        features['has_test'] = int(any(word in content_lower for word in ['test', 'spec', 'example']))
        features['has_ci'] = int(any(word in content_lower for word in ['ci', 'pipeline', 'github', 'actions']))

        # Meta-driven extension one-hot compatibility (if meta defines ext_is_.* names)
        if self.meta.get('dense_meta'):
            # Derive normalized extension key
            norm_ext = ext if ext else '<empty>'
            for d in self.meta['dense_meta']:
                name = d.get('name')
                if name and name.startswith('ext_is_'):
                    target = name.replace('ext_is_', '')  # includes dot or special token
                    features[name] = int(target == norm_ext)
            # size_bytes_log mapping
            features['size_bytes_log'] = float(np.log1p(size))

        return features
    
    def _dense_vector(self, dense_features: dict):
        # Use self.dense_order, but if meta-driven ext features exist, extend accordingly
        vec_order = list(self.dense_order)
        # Append any meta dense names not already captured
        if self.meta.get('dense_meta'):
            for d in self.meta['dense_meta']:
                n = d.get('name')
                if n and n not in vec_order:
                    vec_order.append(n)
        values = [dense_features.get(name, 0.0) for name in vec_order]
        return np.array(values).reshape(1, -1), vec_order

    def extract_features_single(self, file_path, content):
        path_tokens = self.extract_path_tokens(file_path)
        resource_tokens = self.extract_resource_tokens(content)
        all_tokens = path_tokens + resource_tokens
        token_dict = {t: 1 for t in all_tokens}
        X_sparse = self.hasher.transform([token_dict])
        dense_features = self.extract_dense_features(file_path, content)
        X_dense, used_dense_order = self._dense_vector(dense_features)
        X_combined = sparse.hstack([X_sparse, X_dense])
        return X_combined, {
            'path_tokens': path_tokens[:10],
            'resource_tokens': resource_tokens[:10],
            'dense_features': {k: dense_features.get(k, 0.0) for k in used_dense_order}
        }
    
    def extract_features_batch(self, file_data_list):
        X_sparse_blocks = []
        dense_matrix = []
        feature_info_list = []
        for file_path, content in file_data_list:
            path_tokens = self.extract_path_tokens(file_path)
            resource_tokens = self.extract_resource_tokens(content)
            all_tokens = path_tokens + resource_tokens
            token_dict = {t: 1 for t in all_tokens}
            Xs = self.hasher.transform([token_dict])
            dense_features = self.extract_dense_features(file_path, content)
            Xd, used_dense_order = self._dense_vector(dense_features)
            X_sparse_blocks.append(Xs)
            dense_matrix.append(Xd)
            feature_info_list.append({
                'path_tokens': path_tokens[:10],
                'resource_tokens': resource_tokens[:10],
                'dense_features': {k: dense_features.get(k, 0.0) for k in used_dense_order}
            })
        X_sparse_combined = sparse.vstack(X_sparse_blocks) if X_sparse_blocks else sparse.csr_matrix((0, self.hash_dim))
        X_dense_combined = sparse.vstack([sparse.csr_matrix(dm) for dm in dense_matrix]) if dense_matrix else sparse.csr_matrix((0, 0))
        X_combined = sparse.hstack([X_sparse_combined, X_dense_combined])
        return X_combined, feature_info_list

    @staticmethod
    def align_to_expected(X, expected_total: int):
        """Pad or truncate feature matrix to expected_total columns."""
        current = X.shape[1]
        if current == expected_total:
            return X
        if current < expected_total:
            pad = sparse.csr_matrix((X.shape[0], expected_total - current))
            return sparse.hstack([X, pad])
        # Truncate
        return X[:, :expected_total]

    @staticmethod
    def debug_shape_report(X, expected_total: int | None):
        return {
            'produced_shape': X.shape,
            'expected_total': expected_total,
            'delta': None if expected_total is None else expected_total - X.shape[1]
        }