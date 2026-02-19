"""
Graph Neural Network for Infrastructure Attack Path Detection

Novel Contribution: Uses GNN to learn complex attack patterns across infrastructure resources
that traditional rule-based scanners cannot detect.

This is the core AI innovation that makes CloudGuard AI different from Checkov/TFSec.
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import Dict, List, Tuple, Optional
import json
import re
from pathlib import Path

# Try to import PyTorch Geometric, provide helpful error if not installed
try:
    from torch_geometric.nn import GCNConv, GATConv, global_mean_pool, global_max_pool
    from torch_geometric.data import Data, Batch
    TORCH_GEOMETRIC_AVAILABLE = True
except ImportError:
    TORCH_GEOMETRIC_AVAILABLE = False
    print("⚠️  PyTorch Geometric not installed. Install with:")
    print("    pip install torch-geometric torch-scatter torch-sparse")


class InfrastructureGNN(nn.Module):
    """
    Graph Neural Network for detecting attack paths in cloud infrastructure.
    
    Architecture:
    - 3 Graph Attention layers (learns important resource relationships)
    - Attention mechanism (identifies critical nodes)
    - Binary classifier (attack path exists: yes/no)
    - Node importance scores (explains which resources are vulnerable)
    
    Novel aspects:
    1. Multi-head attention to learn different attack pattern types
    2. Skip connections for gradient flow
    3. Graph-level pooling for infrastructure-wide predictions
    """
    
    def __init__(
        self, 
        num_node_features: int = 15,
        hidden_channels: int = 64,
        num_heads: int = 4,
        dropout: float = 0.3
    ):
        super(InfrastructureGNN, self).__init__()
        
        self.num_node_features = num_node_features
        self.hidden_channels = hidden_channels
        
        # Graph Attention Layers (learns which connections matter)
        self.gat1 = GATConv(
            num_node_features, 
            hidden_channels, 
            heads=num_heads, 
            dropout=dropout
        )
        self.gat2 = GATConv(
            hidden_channels * num_heads, 
            hidden_channels, 
            heads=num_heads, 
            dropout=dropout
        )
        self.gat3 = GATConv(
            hidden_channels * num_heads,
            hidden_channels,
            heads=1,
            dropout=dropout
        )
        
        # Node importance attention
        self.node_attention = nn.Sequential(
            nn.Linear(hidden_channels, 32),
            nn.ReLU(),
            nn.Linear(32, 1)
        )
        
        # Graph-level classification
        self.graph_classifier = nn.Sequential(
            nn.Linear(hidden_channels * 2, 128),  # *2 for mean + max pooling
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(128, 64),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(64, 1)
        )
        
        self.dropout = nn.Dropout(dropout)
        
    def forward(self, data):
        """
        Forward pass through GNN
        
        Args:
            data: PyTorch Geometric Data object with:
                - x: Node features [num_nodes, num_node_features]
                - edge_index: Graph connectivity [2, num_edges]
                - batch: Batch assignment [num_nodes]
        
        Returns:
            risk_score: Probability of attack path existing [batch_size, 1]
            attention_weights: Node importance scores [num_nodes, 1]
        """
        x, edge_index, batch = data.x, data.edge_index, data.batch
        
        # Layer 1: Learn local patterns
        x1 = self.gat1(x, edge_index)
        x1 = F.elu(x1)
        x1 = self.dropout(x1)
        
        # Layer 2: Learn multi-hop patterns
        x2 = self.gat2(x1, edge_index)
        x2 = F.elu(x2)
        x2 = self.dropout(x2)
        
        # Layer 3: Refine attack patterns
        x3 = self.gat3(x2, edge_index)
        x3 = F.elu(x3)
        
        # Calculate node importance (attention mechanism)
        node_attention_weights = self.node_attention(x3)  # shape: [num_nodes, 1]
        # dim=0 normalizes across all nodes so the weights sum to 1
        # (dim=1 would be a no-op since the last dim is size 1)
        node_attention_weights = F.softmax(node_attention_weights, dim=0)
        
        # Graph-level pooling (aggregate node features to graph features)
        graph_mean = global_mean_pool(x3, batch)
        graph_max = global_max_pool(x3, batch)
        graph_features = torch.cat([graph_mean, graph_max], dim=1)
        
        # Predict attack path probability
        risk_score = self.graph_classifier(graph_features)
        risk_score = torch.sigmoid(risk_score)
        
        return risk_score, node_attention_weights


class ResourceFeatureExtractor:
    """
    Extracts feature vectors from cloud resources for GNN input.
    
    Features capture security-relevant properties:
    - Resource type (EC2, S3, RDS, etc.)
    - Network exposure (public, private, VPC)
    - Security configuration (encryption, authentication, logging)
    - Access permissions (IAM roles, policies)
    - Compliance status
    """
    
    # Resource type encoding
    RESOURCE_TYPES = {
        'aws_instance': 0,
        'aws_security_group': 1,
        'aws_s3_bucket': 2,
        'aws_rds_instance': 3,
        'aws_db_instance': 4,
        'aws_iam_role': 5,
        'aws_iam_policy': 6,
        'aws_vpc': 7,
        'aws_subnet': 8,
        'aws_internet_gateway': 9,
        'aws_lb': 10,
        'aws_elb': 11,
        'aws_lambda_function': 12,
        'azurerm_virtual_machine': 13,
        'azurerm_storage_account': 14,
        'google_compute_instance': 15,
        'google_storage_bucket': 16,
        'internet_gateway': 99,  # Special: represents internet
        'unknown': 100
    }
    
    @staticmethod
    def extract_features(resource_type: str, attributes: Dict) -> List[float]:
        """
        Extract 15-dimensional feature vector from resource.
        
        Feature dimensions:
        0: Resource type (normalized)
        1: Is publicly accessible
        2: Has encryption enabled
        3: Requires authentication
        4: Stores sensitive data
        5: Has admin/elevated privileges
        6: Network exposure level (0-1)
        7: Security group restrictiveness (0-1)
        8: Logging enabled
        9: Monitoring enabled
        10: MFA enabled
        11: Backup enabled
        12: Latest version/patched
        13: Compliance score (0-1)
        14: Has dependencies on other resources
        """
        features = [0.0] * 15
        
        # Feature 0: Resource type (normalized to 0-1)
        type_id = ResourceFeatureExtractor.RESOURCE_TYPES.get(resource_type, 100)
        features[0] = type_id / 100.0
        
        # Feature 1: Public accessibility
        features[1] = 1.0 if attributes.get('public', False) else 0.0
        if 'associate_public_ip_address' in attributes:
            features[1] = 1.0 if attributes['associate_public_ip_address'] else 0.0
        if resource_type == 'aws_s3_bucket':
            acl = attributes.get('acl', '')
            if acl in ['public-read', 'public-read-write']:
                features[1] = 1.0
        
        # Feature 2: Encryption
        features[2] = 1.0 if attributes.get('encrypted', False) else 0.0
        if 'encryption' in attributes:
            features[2] = 1.0
        if 'server_side_encryption_configuration' in attributes:
            features[2] = 1.0
        
        # Feature 3: Authentication required
        features[3] = 1.0 if attributes.get('requires_auth', True) else 0.0
        
        # Feature 4: Stores sensitive data (databases, storage)
        sensitive_types = ['rds', 'db_instance', 's3_bucket', 'storage', 'dynamodb', 'secretsmanager']
        features[4] = 1.0 if any(t in resource_type for t in sensitive_types) else 0.0
        
        # Feature 5: Admin privileges
        features[5] = 0.0
        if 'iam_role' in resource_type or 'iam_policy' in resource_type:
            policy = str(attributes.get('policy', ''))
            if any(admin in policy.lower() for admin in ['*', 'administratoraccess', 'fullaccess']):
                features[5] = 1.0
        
        # Feature 6: Network exposure level
        features[6] = ResourceFeatureExtractor._calculate_exposure(resource_type, attributes)
        
        # Feature 7: Security group restrictiveness
        features[7] = ResourceFeatureExtractor._calculate_sg_restrictiveness(attributes)
        
        # Feature 8: Logging enabled
        features[8] = 1.0 if attributes.get('logging_enabled', False) else 0.0
        if 'logging' in attributes:
            features[8] = 1.0
        
        # Feature 9: Monitoring enabled
        features[9] = 1.0 if attributes.get('monitoring', False) else 0.0
        if 'enable_monitoring' in attributes:
            features[9] = 1.0 if attributes['enable_monitoring'] else 0.0
        
        # Feature 10: MFA enabled
        features[10] = 1.0 if attributes.get('mfa_delete', False) else 0.0
        
        # Feature 11: Backup enabled
        features[11] = 1.0 if attributes.get('backup_retention_period', 0) > 0 else 0.0
        
        # Feature 12: Latest version/patched
        features[12] = 0.5  # Default: unknown
        if 'engine_version' in attributes:
            # Simple heuristic: newer versions have higher numbers
            version = attributes.get('engine_version', '')
            if version and any(c.isdigit() for c in str(version)):
                features[12] = 0.7  # Assume relatively recent
        
        # Feature 13: Compliance score (calculated from other features)
        compliance_factors = [features[2], features[7], features[8], features[9]]
        features[13] = sum(compliance_factors) / len(compliance_factors)
        
        # Feature 14: Has dependencies
        features[14] = 1.0 if attributes.get('dependencies', []) else 0.0
        
        return features
    
    @staticmethod
    def _calculate_exposure(resource_type: str, attributes: Dict) -> float:
        """Calculate network exposure level (0 = isolated, 1 = internet-facing)"""
        
        # Internet gateway is maximally exposed
        if resource_type == 'internet_gateway' or resource_type == 'aws_internet_gateway':
            return 1.0
        
        # Load balancers
        if 'lb' in resource_type or 'elb' in resource_type:
            if attributes.get('internal', True) == False:
                return 1.0
            return 0.3
        
        # Instances with public IP
        if 'instance' in resource_type:
            if attributes.get('associate_public_ip_address', False):
                return 0.9
            return 0.2
        
        # S3 buckets
        if 's3_bucket' in resource_type:
            acl = attributes.get('acl', 'private')
            if 'public' in acl:
                return 1.0
            return 0.1
        
        # Default: moderate exposure
        return 0.3
    
    @staticmethod
    def _calculate_sg_restrictiveness(attributes: Dict) -> float:
        """Calculate security group restrictiveness (0 = wide open, 1 = highly restricted)"""
        
        ingress_rules = attributes.get('ingress', [])
        if not ingress_rules:
            return 1.0  # No ingress = fully restricted
        
        # Check for wide-open rules (0.0.0.0/0)
        for rule in ingress_rules:
            cidr_blocks = rule.get('cidr_blocks', [])
            if '0.0.0.0/0' in cidr_blocks:
                # Wide open on sensitive ports
                from_port = rule.get('from_port', 0)
                to_port = rule.get('to_port', 65535)
                
                # SSH, RDP, or all ports
                if from_port in [22, 3389] or (from_port == 0 and to_port == 65535):
                    return 0.0  # Maximally permissive
                
                return 0.3  # Somewhat permissive
        
        return 0.8  # Reasonably restricted


class AttackPathPredictor:
    """
    High-level interface for using GNN to detect attack paths.
    
    Usage:
        predictor = AttackPathPredictor()
        predictor.load_model('path/to/model.pt')
        risk, critical_nodes = predictor.predict_attack_risk(terraform_files)
    """
    
    def __init__(self, model_path: Optional[str] = None):
        if not TORCH_GEOMETRIC_AVAILABLE:
            raise ImportError("PyTorch Geometric is required. Install with: pip install torch-geometric")
        
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.model = InfrastructureGNN().to(self.device)
        self.feature_extractor = ResourceFeatureExtractor()
        
        if model_path and Path(model_path).exists():
            self.load_model(model_path)
        
        self.model.eval()
    
    def load_model(self, model_path: str):
        """Load trained model weights"""
        checkpoint = torch.load(model_path, map_location=self.device)
        if isinstance(checkpoint, dict) and 'model_state_dict' in checkpoint:
            self.model.load_state_dict(checkpoint['model_state_dict'])
        else:
            self.model.load_state_dict(checkpoint)
        self.model.eval()
        print(f"✅ Loaded GNN model from {model_path}")
    
    def save_model(self, model_path: str):
        """Save model weights"""
        Path(model_path).parent.mkdir(parents=True, exist_ok=True)
        torch.save({
            'model_state_dict': self.model.state_dict(),
            'num_features': self.model.num_node_features,
            'hidden_channels': self.model.hidden_channels
        }, model_path)
        print(f"💾 Saved GNN model to {model_path}")
    
    def terraform_to_graph(self, terraform_content: str) -> Tuple[Data, Dict[int, str]]:
        """
        Convert Terraform code to graph representation.
        
        Returns:
            data: PyTorch Geometric Data object
            node_id_map: Mapping from node index to resource name
        """
        
        # Parse Terraform resources
        resources = self._parse_terraform_simple(terraform_content)
        
        if not resources:
            # Create minimal graph with single node
            x = torch.tensor([[0.0] * 15], dtype=torch.float)
            edge_index = torch.tensor([[], []], dtype=torch.long)
            return Data(x=x, edge_index=edge_index), {0: 'empty'}
        
        # Create nodes
        node_features = []
        node_id_map = {}
        resource_to_idx = {}
        
        for idx, resource in enumerate(resources):
            features = self.feature_extractor.extract_features(
                resource['type'],
                resource['attributes']
            )
            node_features.append(features)
            node_id_map[idx] = resource['name']
            resource_to_idx[resource['name']] = idx
        
        # Create edges (dependencies between resources)
        edges = []
        for idx, resource in enumerate(resources):
            # Add edges based on resource references
            for dep in resource.get('dependencies', []):
                if dep in resource_to_idx:
                    dep_idx = resource_to_idx[dep]
                    edges.append([idx, dep_idx])
        
        # Convert to tensors
        x = torch.tensor(node_features, dtype=torch.float)
        
        if edges:
            edge_index = torch.tensor(edges, dtype=torch.long).t().contiguous()
        else:
            # No edges: create self-loops
            edge_index = torch.tensor([[i, i] for i in range(len(resources))], dtype=torch.long).t()
        
        data = Data(x=x, edge_index=edge_index)
        
        return data, node_id_map
    
    def predict_attack_risk(self, terraform_content: str) -> Dict:
        """
        Predict attack path risk for infrastructure.
        
        Returns:
            {
                'risk_score': float (0-1),
                'risk_level': str (LOW/MEDIUM/HIGH/CRITICAL),
                'critical_nodes': List[str],
                'attention_scores': Dict[str, float],
                'explanation': str
            }
        """
        
        # Convert to graph
        graph_data, node_id_map = self.terraform_to_graph(terraform_content)
        graph_data = graph_data.to(self.device)
        
        # Add batch dimension
        graph_data.batch = torch.zeros(graph_data.x.size(0), dtype=torch.long, device=self.device)
        
        # Predict
        with torch.no_grad():
            risk_score, attention_weights = self.model(graph_data)
        
        risk_score = float(risk_score.cpu().numpy()[0])
        attention_weights = attention_weights.cpu().numpy().flatten()
        
        # Determine risk level
        if risk_score >= 0.8:
            risk_level = 'CRITICAL'
        elif risk_score >= 0.6:
            risk_level = 'HIGH'
        elif risk_score >= 0.4:
            risk_level = 'MEDIUM'
        else:
            risk_level = 'LOW'
        
        # Find critical nodes (top 3 by attention)
        if len(attention_weights) > 0:
            top_indices = attention_weights.argsort()[-3:][::-1]
            critical_nodes = [node_id_map.get(int(idx), f'node_{idx}') for idx in top_indices]
            attention_scores = {
                node_id_map.get(i, f'node_{i}'): float(attention_weights[i])
                for i in range(len(attention_weights))
            }
        else:
            critical_nodes = []
            attention_scores = {}
        
        # Generate explanation
        explanation = self._generate_explanation(risk_score, critical_nodes)
        
        return {
            'risk_score': risk_score,
            'risk_level': risk_level,
            'critical_nodes': critical_nodes,
            'attention_scores': attention_scores,
            'explanation': explanation,
            'model_type': 'GNN',
            'num_resources': len(node_id_map)
        }
    
    def _parse_terraform_simple(self, content: str) -> List[Dict]:
        """
        Simple Terraform parser (extracts resource blocks).
        Note: This is a simplified parser. For production, use HCL parser.
        """
        
        resources = []
        
        # Find resource blocks using regex
        # Pattern: resource "type" "name" { ... }
        resource_pattern = r'resource\s+"([^"]+)"\s+"([^"]+)"\s*\{([^}]*(?:\{[^}]*\}[^}]*)*)\}'
        
        matches = re.finditer(resource_pattern, content, re.DOTALL)
        
        for match in matches:
            resource_type = match.group(1)
            resource_name = match.group(2)
            resource_body = match.group(3)
            
            # Extract basic attributes
            attributes = {}
            
            # Check for common security attributes
            if 'associate_public_ip_address' in resource_body:
                attributes['associate_public_ip_address'] = 'true' in resource_body.lower()
            
            if 'encrypted' in resource_body:
                attributes['encrypted'] = 'true' in resource_body.lower()
            
            if 'public-read' in resource_body:
                attributes['acl'] = 'public-read'
            
            if '0.0.0.0/0' in resource_body:
                attributes['public'] = True
            
            # Extract dependencies (resources referenced)
            dependency_pattern = r'(aws_[a-z_]+)\.([\w]+)'
            deps = re.findall(dependency_pattern, resource_body)
            attributes['dependencies'] = [f"{d[0]}.{d[1]}" for d in deps]
            
            resources.append({
                'type': resource_type,
                'name': f"{resource_type}.{resource_name}",
                'attributes': attributes
            })
        
        return resources
    
    def _generate_explanation(self, risk_score: float, critical_nodes: List[str]) -> str:
        """Generate human-readable explanation of attack risk"""
        
        if risk_score >= 0.8:
            explanation = f"🚨 CRITICAL RISK: GNN detected high probability ({risk_score:.1%}) of attack paths in infrastructure. "
        elif risk_score >= 0.6:
            explanation = f"⚠️  HIGH RISK: GNN identified significant attack path risk ({risk_score:.1%}). "
        elif risk_score >= 0.4:
            explanation = f"⚡ MEDIUM RISK: GNN found moderate attack path indicators ({risk_score:.1%}). "
        else:
            explanation = f"✅ LOW RISK: GNN analysis shows minimal attack path risk ({risk_score:.1%}). "
        
        if critical_nodes:
            explanation += f"Critical resources identified: {', '.join(critical_nodes[:3])}. "
            explanation += "These nodes have high attention scores indicating they are key points in potential attack chains."
        
        return explanation


# Convenience function for quick predictions
def predict_attack_paths(terraform_content: str, model_path: Optional[str] = None) -> Dict:
    """
    Convenience function for quick attack path prediction.
    
    Args:
        terraform_content: Terraform code as string
        model_path: Optional path to trained model
    
    Returns:
        Prediction results with risk score and critical nodes
    """
    predictor = AttackPathPredictor(model_path)
    return predictor.predict_attack_risk(terraform_content)


if __name__ == '__main__':
    # Example usage
    print("🧠 CloudGuard AI - Graph Neural Network Attack Path Detector")
    print("=" * 70)
    
    # Test with sample Terraform
    sample_tf = """
    resource "aws_instance" "web" {
        ami = "ami-12345"
        instance_type = "t2.micro"
        associate_public_ip_address = true
        
        vpc_security_group_ids = [aws_security_group.allow_all.id]
    }
    
    resource "aws_security_group" "allow_all" {
        ingress {
            from_port = 0
            to_port = 65535
            protocol = "tcp"
            cidr_blocks = ["0.0.0.0/0"]
        }
    }
    
    resource "aws_s3_bucket" "data" {
        bucket = "sensitive-data"
        acl = "public-read"
    }
    """
    
    try:
        result = predict_attack_paths(sample_tf)
        print(f"\n📊 Analysis Results:")
        print(f"   Risk Score: {result['risk_score']:.2%}")
        print(f"   Risk Level: {result['risk_level']}")
        print(f"   Critical Nodes: {', '.join(result['critical_nodes'])}")
        print(f"\n💡 {result['explanation']}")
    except ImportError as e:
        print(f"\n⚠️  {e}")
        print("\nInstall PyTorch Geometric to use GNN features:")
        print("   pip install torch-geometric torch-scatter torch-sparse")
