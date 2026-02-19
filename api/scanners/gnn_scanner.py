"""
GNN-based Attack Path Scanner

Integrates Graph Neural Network attack path detection into CloudGuard AI.
This is the novel AI contribution that differentiates CloudGuard from traditional tools.
"""

import sys
from pathlib import Path
from typing import List, Dict, Optional
import json

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Defer GNN imports to avoid loading heavy dependencies
GNN_AVAILABLE = False
try:
    # Try importing just to check availability, don't load the module yet
    import importlib.util
    gnn_spec = importlib.util.find_spec("torch_geometric")
    if gnn_spec is not None:
        GNN_AVAILABLE = True
except ImportError:
    pass


class GNNScanner:
    """
    Graph Neural Network scanner for detecting complex attack paths.
    
    Novel Features:
    - Uses GNN to learn attack patterns (not rule-based)
    - Detects multi-hop attacks across resources
    - Attention mechanism explains critical nodes
    - Trained on synthetic vulnerable infrastructure patterns
    
    Differentiates CloudGuard from:
    - Checkov: Rule-based, misses complex attack chains
    - TFSec: Policy-based, no ML
    - Snyk: Signature-based, no graph analysis
    """
    
    def __init__(self, model_path: Optional[str] = None):
        self.scanner_type = "gnn"
        self.name = "GNN Attack Path Detector"
        self.available = GNN_AVAILABLE
        self.predictor = None
        
        if not GNN_AVAILABLE:
            return
        
        # Default model path
        if model_path is None:
            model_path = str(Path(__file__).parent.parent.parent / 'ml' / 'models_artifacts' / 'gnn_attack_detector.pt')
        
        self.model_path = model_path
        
        # Load model if exists - lazy import to avoid loading heavy dependencies
        if Path(model_path).exists():
            try:
                # Import only when needed
                from ml.models.graph_neural_network import AttackPathPredictor
                self.predictor = AttackPathPredictor(model_path=model_path)
                print(f"✅ GNN scanner initialized with model: {model_path}")
            except Exception as e:
                print(f"⚠️  Failed to load GNN model: {e}")
                self.predictor = None
                self.available = False
        else:
            print(f"⚠️  GNN model not found at {model_path}")
            print("   Train model first: python -m ml.models.train_gnn")
            self.predictor = None
            self.available = False
    
    def scan_file(self, file_path: str) -> List[Dict]:
        """
        Scan a Terraform file for attack paths using GNN.
        
        Args:
            file_path: Path to Terraform file
        
        Returns:
            List of findings with attack path information
        """
        
        if not self.available or self.predictor is None:
            return []
        
        try:
            # Read file
            with open(file_path, 'r', encoding='utf-8') as f:
                terraform_content = f.read()
            
            # Predict attack risk
            result = self.predictor.predict_attack_risk(terraform_content)
            
            # Convert to findings format
            findings = []
            
            # Only report if risk is significant (>= MEDIUM)
            if result['risk_score'] >= 0.4:
                finding = {
                    'scanner': 'gnn',
                    'file': file_path,
                    'type': 'attack_path',
                    'severity': result['risk_level'],
                    'confidence': 'high' if result['risk_score'] >= 0.7 else 'medium',
                    'title': f"GNN detected {result['risk_level'].lower()} risk attack path",
                    'description': result['explanation'],
                    'risk_score': result['risk_score'],
                    'critical_nodes': result['critical_nodes'],
                    'num_resources': result['num_resources'],
                    'model_type': 'Graph Neural Network',
                    'remediation': self._generate_remediation(result),
                    'metadata': {
                        'attention_scores': result.get('attention_scores', {}),
                        'model_confidence': result['risk_score']
                    }
                }
                
                findings.append(finding)
                
                # Add findings for each critical node
                for node in result['critical_nodes'][:3]:  # Top 3
                    node_finding = {
                        'scanner': 'gnn',
                        'file': file_path,
                        'type': 'critical_resource',
                        'severity': 'HIGH' if result['risk_score'] >= 0.7 else 'MEDIUM',
                        'confidence': 'high',
                        'title': f"Critical infrastructure node: {node}",
                        'description': f"GNN attention mechanism identified {node} as a critical point in potential attack paths. "
                                     f"This resource has high importance in the infrastructure attack graph.",
                        'resource': node,
                        'attention_score': result['attention_scores'].get(node, 0.0),
                        'remediation': f"Review security configuration of {node}. Ensure proper access controls, encryption, and network isolation.",
                        'metadata': {
                            'parent_finding': 'attack_path',
                            'graph_importance': 'high'
                        }
                    }
                    
                    findings.append(node_finding)
            
            return findings
        
        except Exception as e:
            print(f"❌ GNN scan error for {file_path}: {e}")
            return []
    
    def scan_directory(self, directory_path: str) -> List[Dict]:
        """
        Scan all Terraform files in directory.
        
        Args:
            directory_path: Path to directory
        
        Returns:
            List of all findings from all files
        """
        
        if not self.available or self.predictor is None:
            return []
        
        all_findings = []
        directory = Path(directory_path)
        
        # Find all Terraform files
        tf_files = list(directory.rglob('*.tf'))
        
        print(f"🔍 GNN scanning {len(tf_files)} Terraform files...")
        
        for tf_file in tf_files:
            findings = self.scan_file(str(tf_file))
            all_findings.extend(findings)
        
        print(f"✅ GNN found {len(all_findings)} attack path findings")
        
        return all_findings
    
    def _generate_remediation(self, result: Dict) -> str:
        """Generate remediation advice based on GNN findings"""
        
        risk_level = result['risk_level']
        critical_nodes = result['critical_nodes']
        
        remediation = []
        
        if risk_level == 'CRITICAL':
            remediation.append("🚨 URGENT: Critical attack paths detected.")
        elif risk_level == 'HIGH':
            remediation.append("⚠️  HIGH PRIORITY: Significant attack path risk.")
        else:
            remediation.append("⚡ MODERATE: Address attack path vulnerabilities.")
        
        remediation.append("\nRecommended actions:")
        
        # Generic remediation based on risk level
        if critical_nodes:
            remediation.append(f"1. Review security of critical resources: {', '.join(critical_nodes[:3])}")
            remediation.append("2. Implement network segmentation to break attack chains")
            remediation.append("3. Add security controls at critical nodes:")
            remediation.append("   - Enable encryption at rest and in transit")
            remediation.append("   - Restrict network access (security groups, NACLs)")
            remediation.append("   - Enable authentication and authorization")
            remediation.append("   - Add monitoring and logging")
            remediation.append("4. Apply principle of least privilege to IAM roles/policies")
            remediation.append("5. Remove public access where not required")
        
        if result['risk_score'] >= 0.8:
            remediation.append("\n⚠️  Consider redesigning infrastructure architecture to eliminate attack paths.")
        
        return "\n".join(remediation)
    
    def get_statistics(self, findings: List[Dict]) -> Dict:
        """Generate statistics from GNN findings"""
        
        if not findings:
            return {
                'total_findings': 0,
                'attack_paths': 0,
                'critical_nodes': 0,
                'risk_distribution': {},
                'average_risk_score': 0.0
            }
        
        attack_path_findings = [f for f in findings if f['type'] == 'attack_path']
        critical_node_findings = [f for f in findings if f['type'] == 'critical_resource']
        
        risk_scores = [f.get('risk_score', 0) for f in attack_path_findings]
        avg_risk = sum(risk_scores) / len(risk_scores) if risk_scores else 0
        
        # Count by severity
        risk_distribution = {}
        for finding in findings:
            severity = finding.get('severity', 'UNKNOWN')
            risk_distribution[severity] = risk_distribution.get(severity, 0) + 1
        
        return {
            'total_findings': len(findings),
            'attack_paths': len(attack_path_findings),
            'critical_nodes': len(critical_node_findings),
            'risk_distribution': risk_distribution,
            'average_risk_score': avg_risk,
            'model_used': 'Graph Neural Network (GNN)'
        }


def test_gnn_scanner():
    """Test GNN scanner on sample infrastructure"""
    
    print("🧪 Testing GNN Scanner")
    print("=" * 70)
    
    scanner = GNNScanner()
    
    if not scanner.available:
        print("❌ GNN scanner not available")
        print("   Install: pip install torch-geometric torch-scatter torch-sparse")
        print("   Train model: python -m ml.models.train_gnn")
        return
    
    # Create test file
    test_tf = """
resource "aws_instance" "web_server" {
    ami = "ami-0c55b159cbfafe1f0"
    instance_type = "t2.micro"
    associate_public_ip_address = true
    
    vpc_security_group_ids = [aws_security_group.web_sg.id]
    
    user_data = <<-EOF
        #!/bin/bash
        echo "DB_PASSWORD=hardcoded123" > /etc/config
        service apache2 start
    EOF
}

resource "aws_security_group" "web_sg" {
    name = "web-security-group"
    
    ingress {
        from_port   = 22
        to_port     = 22
        protocol    = "tcp"
        cidr_blocks = ["0.0.0.0/0"]
    }
    
    ingress {
        from_port   = 80
        to_port     = 80
        protocol    = "tcp"
        cidr_blocks = ["0.0.0.0/0"]
    }
    
    egress {
        from_port   = 0
        to_port     = 0
        protocol    = "-1"
        cidr_blocks = ["0.0.0.0/0"]
    }
}

resource "aws_db_instance" "database" {
    identifier = "production-db"
    engine = "postgres"
    instance_class = "db.t2.micro"
    allocated_storage = 20
    
    publicly_accessible = true
    storage_encrypted = false
    
    username = "admin"
    password = "password123"
    
    vpc_security_group_ids = [aws_security_group.db_sg.id]
}

resource "aws_security_group" "db_sg" {
    name = "db-security-group"
    
    ingress {
        from_port   = 5432
        to_port     = 5432
        protocol    = "tcp"
        cidr_blocks = ["0.0.0.0/0"]
    }
}

resource "aws_s3_bucket" "data_backup" {
    bucket = "company-data-backup"
    acl    = "public-read"
}

resource "aws_s3_bucket_object" "config_file" {
    bucket = aws_s3_bucket.data_backup.id
    key    = "config/database.json"
    content = jsonencode({
        host = aws_db_instance.database.address
        username = "admin"
        password = "password123"
    })
}
"""
    
    # Write test file
    test_file = Path('test_vulnerable.tf')
    test_file.write_text(test_tf)
    
    print(f"📄 Created test file: {test_file}")
    print()
    
    # Scan
    findings = scanner.scan_file(str(test_file))
    
    print(f"\n📊 GNN Scan Results:")
    print(f"   Total Findings: {len(findings)}")
    print()
    
    for i, finding in enumerate(findings, 1):
        print(f"\n{i}. [{finding['severity']}] {finding['title']}")
        print(f"   Type: {finding['type']}")
        print(f"   Confidence: {finding['confidence']}")
        if 'risk_score' in finding:
            print(f"   Risk Score: {finding['risk_score']:.2%}")
        if 'resource' in finding:
            print(f"   Resource: {finding['resource']}")
            print(f"   Attention Score: {finding.get('attention_score', 0):.4f}")
        print(f"\n   {finding['description']}")
    
    # Statistics
    stats = scanner.get_statistics(findings)
    print(f"\n📈 Statistics:")
    print(f"   Attack Paths: {stats['attack_paths']}")
    print(f"   Critical Nodes: {stats['critical_nodes']}")
    print(f"   Average Risk: {stats['average_risk_score']:.2%}")
    print(f"   Risk Distribution: {stats['risk_distribution']}")
    
    # Cleanup
    test_file.unlink()
    print(f"\n🧹 Cleaned up test file")


if __name__ == '__main__':
    test_gnn_scanner()
