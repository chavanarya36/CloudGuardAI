"""
Train GNN on Real Infrastructure Data
Uses actual IAC files with Checkov findings from your dataset
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'ml'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'api'))

import pandas as pd
import torch
import torch.nn as nn
import torch.optim as optim
import re
from pathlib import Path
from typing import List, Dict, Tuple
import json
from datetime import datetime
import numpy as np

print("CloudGuard AI - GNN Training on Real Data")
print("=" * 70)

# Import Data and Batch later to avoid slow torch_geometric init
from ml.models.graph_neural_network import InfrastructureGNN

class RealIaCDataset:
    """
    Load and process real IaC files with findings
    """
    
    def __init__(self, csv_path: str):
        self.csv_path = csv_path
        
        print(f"\nLoading dataset from: {csv_path}")
        self.df = pd.read_csv(csv_path)
        
        print(f"  Total files: {len(self.df)}")
        print(f"  Files with findings: {self.df['has_findings'].sum()}")
        print(f"  Critical: {self.df['severity_critical'].sum()}")
        print(f"  High: {self.df['severity_high'].sum()}")
        print(f"  Medium: {self.df['severity_medium'].sum()}")
        print(f"  Low: {self.df['severity_low'].sum()}")
        
    def load_file_content(self, file_path: str) -> str:
        """Load file content"""
        try:
            # Try original path
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    return f.read()
            
            # Try with data/samples prefix
            alt_path = file_path.replace('d:/CloudGuardAI/iac_subset', 'd:/CloudGuardAI/data/samples/iac_subset')
            alt_path = alt_path.replace('d:\\CloudGuardAI\\iac_subset', 'd:\\CloudGuardAI\\data\\samples\\iac_subset')
            
            if os.path.exists(alt_path):
                with open(alt_path, 'r', encoding='utf-8', errors='ignore') as f:
                    return f.read()
            
            return ""
        except Exception as e:
            return ""
    
    def extract_resources_simple(self, content: str, file_ext: str) -> List[Dict]:
        """
        Extract resources from IaC files (simplified)
        """
        resources = []
        
        # YAML/YML (Kubernetes, Terraform, CloudFormation)
        if file_ext in ['.yml', '.yaml']:
            # Look for kind: or resource: patterns
            kind_pattern = r'kind:\s*([^\s\n]+)'
            matches = re.finditer(kind_pattern, content, re.IGNORECASE)
            for match in matches:
                resources.append({
                    'type': match.group(1),
                    'name': f'{match.group(1)}_{len(resources)}',
                    'content': content[max(0, match.start()-200):match.end()+200]
                })
        
        # Terraform
        elif file_ext == '.tf':
            resource_pattern = r'resource\s+"([^"]+)"\s+"([^"]+)"\s*\{'
            matches = re.finditer(resource_pattern, content)
            for match in matches:
                resources.append({
                    'type': match.group(1),
                    'name': match.group(2),
                    'content': self._extract_block(content[match.start():])
                })
        
        # JSON (CloudFormation, package files)
        elif file_ext == '.json':
            # Look for Resources or resources keys
            if 'Resources' in content or 'resources' in content:
                try:
                    import json
                    data = json.loads(content)
                    if 'Resources' in data:
                        for res_name, res_data in data['Resources'].items():
                            resources.append({
                                'type': res_data.get('Type', 'unknown'),
                                'name': res_name,
                                'content': str(res_data)
                            })
                except:
                    pass
        
        # Dockerfile
        elif file_ext == '.dockerfile' or 'dockerfile' in file_ext.lower():
            # Each FROM/RUN/COPY is a resource
            for i, line in enumerate(content.split('\n')):
                if any(cmd in line.upper() for cmd in ['FROM', 'RUN', 'COPY', 'ADD']):
                    resources.append({
                        'type': 'DockerInstruction',
                        'name': f'instruction_{i}',
                        'content': line
                    })
        
        return resources
    
    def _extract_block(self, content: str) -> str:
        """Extract Terraform block"""
        brace_count = 0
        start = content.find('{')
        if start == -1:
            return content[:200]
        
        for i, char in enumerate(content[start:], start):
            if char == '{':
                brace_count += 1
            elif char == '}':
                brace_count -= 1
                if brace_count == 0:
                    return content[:i+1]
        
        return content[:500]
    
    def create_graph_from_file(self, row: pd.Series) -> Tuple[object, float]:
        """
        Create graph from single file
        Returns (graph_data, label)
        """
        from torch_geometric.data import Data
        
        file_path = row['abs_path']
        file_ext = row['ext']
        
        # Load content
        content = self.load_file_content(file_path)
        if not content:
            return None, 0.0
        
        # Extract resources
        resources = self.extract_resources_simple(content, file_ext)
        
        if len(resources) == 0:
            # No resources found, create single node
            resources = [{
                'type': 'unknown',
                'name': 'file',
                'content': content[:500]
            }]
        
        # Create features for each resource
        node_features = []
        for resource in resources:
            features = self._create_node_features(
                resource['type'],
                resource['content'],
                row
            )
            node_features.append(features)
        
        # Create edge index (simple chain for now)
        num_nodes = len(node_features)
        if num_nodes == 1:
            edge_index = torch.tensor([[0], [0]], dtype=torch.long)
        else:
            edges = []
            for i in range(num_nodes - 1):
                edges.append([i, i + 1])
                edges.append([i + 1, i])  # bidirectional
            edge_index = torch.tensor(edges, dtype=torch.long).t().contiguous()
        
        x = torch.tensor(node_features, dtype=torch.float)
        
        # Label based on severity
        label = 1.0 if row['has_findings'] > 0 else 0.0
        
        # Calculate risk score for regression
        risk_score = (
            row['severity_critical'] * 1.0 +
            row['severity_high'] * 0.7 +
            row['severity_medium'] * 0.4 +
            row['severity_low'] * 0.2
        ) / max(1, row['num_findings'])
        
        risk_score = min(1.0, risk_score)
        
        data = Data(x=x, edge_index=edge_index, y=torch.tensor([label], dtype=torch.float))
        
        return data, risk_score
    
    def _create_node_features(self, resource_type: str, content: str, row: pd.Series) -> List[float]:
        """
        Create 15-dimensional feature vector
        """
        features = [0.0] * 15
        
        # Features 0-9: Resource type encoding
        type_categories = {
            'pod': 0, 'deployment': 0, 'service': 0,
            'aws_instance': 1, 'aws_ec2': 1,
            'aws_security_group': 2, 'aws_sg': 2,
            'aws_s3': 3, 's3bucket': 3,
            'aws_db': 4, 'aws_rds': 4,
            'aws_iam': 5, 'iam': 5,
            'aws_ebs': 6, 'volume': 6,
            'container': 7, 'docker': 7,
            'network': 8, 'vpc': 8,
        }
        
        category = 9  # default
        for key, val in type_categories.items():
            if key in resource_type.lower():
                category = val
                break
        
        features[category] = 1.0
        
        # Feature 10: Has findings (from CSV)
        features[10] = 1.0 if row['has_findings'] > 0 else 0.0
        
        # Feature 11: Severity score
        total_findings = max(1, row['num_findings'])
        severity_score = (
            row['severity_critical'] / total_findings * 1.0 +
            row['severity_high'] / total_findings * 0.7 +
            row['severity_medium'] / total_findings * 0.4 +
            row['severity_low'] / total_findings * 0.2
        )
        features[11] = min(1.0, severity_score)
        
        # Feature 12: Public exposure indicators
        content_lower = content.lower()
        public_indicators = ['0.0.0.0', 'public', 'internet', 'expose']
        features[12] = 1.0 if any(ind in content_lower for ind in public_indicators) else 0.0
        
        # Feature 13: Encryption indicators
        encrypt_indicators = ['encrypt', 'tls', 'ssl', 'https']
        features[13] = 1.0 if any(ind in content_lower for ind in encrypt_indicators) else 0.0
        
        # Feature 14: Authentication/IAM
        auth_indicators = ['auth', 'iam', 'role', 'permission', 'policy']
        features[14] = 1.0 if any(ind in content_lower for ind in auth_indicators) else 0.0
        
        return features
    
    def load_dataset(self, max_samples: int = None) -> Tuple[List, List[float]]:
        """
        Load all graphs from dataset
        """
        print(f"\nCreating infrastructure graphs...")
        
        graphs = []
        labels = []
        
        # Sample data if needed
        df_sample = self.df
        if max_samples:
            # Stratified sampling to keep balance
            vulnerable = self.df[self.df['has_findings'] > 0]
            secure = self.df[self.df['has_findings'] == 0]
            
            n_vulnerable = min(len(vulnerable), max_samples // 2)
            n_secure = min(len(secure), max_samples // 2)
            
            df_sample = pd.concat([
                vulnerable.sample(n=n_vulnerable, random_state=42),
                secure.sample(n=n_secure, random_state=42)
            ]).sample(frac=1, random_state=42)  # shuffle
        
        print(f"Processing {len(df_sample)} files...")
        
        for idx, row in df_sample.iterrows():
            graph, risk_score = self.create_graph_from_file(row)
            
            if graph is not None:
                graphs.append(graph)
                labels.append(float(row['has_findings'] > 0))
                
                if len(graphs) % 100 == 0:
                    status = "VULNERABLE" if row['has_findings'] > 0 else "SECURE"
                    print(f"  Processed {len(graphs)} graphs... (Current: {status})")
            else:
                # Debug: Print why graphs aren't being created
                if idx < 5:  # Only print first few failures
                    print(f"  FAILED: {row['abs_path'][:80]}...")
        
        print(f"\nDataset created:")
        print(f"  Total graphs: {len(graphs)}")
        
        if len(graphs) > 0:
            print(f"  Vulnerable: {sum(labels)} ({sum(labels)/len(labels)*100:.1f}%)")
            print(f"  Secure: {len(labels) - sum(labels)} ({(1-sum(labels)/len(labels))*100:.1f}%)")
        else:
            print("  WARNING: No graphs created!")
        
        return graphs, labels


def train_model(graphs: List, labels: List[float], epochs: int = 100, batch_size: int = 32):
    """
    Train GNN model
    """
    from torch_geometric.data import Batch
    
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    print(f"\nDevice: {device}")
    
    # Split data
    split_idx = int(len(graphs) * 0.8)
    train_graphs = graphs[:split_idx]
    train_labels = labels[:split_idx]
    val_graphs = graphs[split_idx:]
    val_labels = labels[split_idx:]
    
    print(f"\nDataset split:")
    print(f"  Train: {len(train_graphs)} graphs")
    print(f"  Val: {len(val_graphs)} graphs")
    
    # Create model
    model = InfrastructureGNN(num_node_features=15, hidden_channels=64).to(device)
    total_params = sum(p.numel() for p in model.parameters())
    print(f"  Model parameters: {total_params:,}")
    
    optimizer = optim.Adam(model.parameters(), lr=0.001)
    criterion = nn.BCELoss()
    
    # Training loop
    print(f"\nStarting training for {epochs} epochs...")
    print("-" * 70)
    
    best_val_acc = 0.0
    history = []
    
    for epoch in range(epochs):
        # Train
        model.train()
        train_loss = 0.0
        train_correct = 0
        
        # Process in batches
        for i in range(0, len(train_graphs), batch_size):
            batch_data = train_graphs[i:i+batch_size]
            batch_labels = train_labels[i:i+batch_size]
            
            batch = Batch.from_data_list(batch_data).to(device)
            labels_tensor = torch.tensor(batch_labels, dtype=torch.float, device=device)
            
            optimizer.zero_grad()
            out, _ = model(batch)
            out = out.squeeze()
            
            loss = criterion(out, labels_tensor)
            loss.backward()
            optimizer.step()
            
            train_loss += loss.item() * len(batch_data)
            pred = (out > 0.5).float()
            train_correct += (pred == labels_tensor).sum().item()
        
        train_acc = train_correct / len(train_graphs)
        avg_train_loss = train_loss / len(train_graphs)
        
        # Validate
        model.eval()
        val_loss = 0.0
        val_correct = 0
        
        with torch.no_grad():
            for i in range(0, len(val_graphs), batch_size):
                batch_data = val_graphs[i:i+batch_size]
                batch_labels = val_labels[i:i+batch_size]
                
                batch = Batch.from_data_list(batch_data).to(device)
                labels_tensor = torch.tensor(batch_labels, dtype=torch.float, device=device)
                
                out, _ = model(batch)
                out = out.squeeze()
                
                loss = criterion(out, labels_tensor)
                
                val_loss += loss.item() * len(batch_data)
                pred = (out > 0.5).float()
                val_correct += (pred == labels_tensor).sum().item()
        
        val_acc = val_correct / len(val_graphs) if val_graphs else 0
        avg_val_loss = val_loss / len(val_graphs) if val_graphs else 0
        
        history.append({
            'epoch': epoch + 1,
            'train_loss': avg_train_loss,
            'train_acc': train_acc,
            'val_loss': avg_val_loss,
            'val_acc': val_acc
        })
        
        # Print progress
        if (epoch + 1) % 10 == 0 or epoch == 0:
            print(f"Epoch {epoch+1:3d}/{epochs}: "
                  f"Train Loss: {avg_train_loss:.4f} Acc: {train_acc:.4f} | "
                  f"Val Loss: {avg_val_loss:.4f} Acc: {val_acc:.4f}")
        
        # Save best model
        if val_acc > best_val_acc:
            best_val_acc = val_acc
            save_path = Path('ml/models_artifacts/gnn_real_data.pt')
            save_path.parent.mkdir(parents=True, exist_ok=True)
            torch.save({
                'model_state_dict': model.state_dict(),
                'val_acc': val_acc,
                'epoch': epoch + 1
            }, save_path)
    
    print("-" * 70)
    print(f"\nTraining complete!")
    print(f"  Best validation accuracy: {best_val_acc:.4f}")
    print(f"  Model saved to: ml/models_artifacts/gnn_real_data.pt")
    
    # Save history
    history_path = Path('ml/models_artifacts/training_history_real.json')
    with open(history_path, 'w') as f:
        json.dump({
            'best_val_acc': best_val_acc,
            'history': history,
            'timestamp': datetime.now().isoformat()
        }, f, indent=2)
    
    return model, best_val_acc


def main():
    """
    Main training function
    """
    csv_path = "data/labels_artifacts/iac_labels_clean.csv"
    
    if not os.path.exists(csv_path):
        print(f"ERROR: CSV file not found: {csv_path}")
        return
    
    # Load dataset
    dataset = RealIaCDataset(csv_path)
    
    # Create graphs (limit to reasonable size for training)
    graphs, labels = dataset.load_dataset(max_samples=2000)
    
    if len(graphs) == 0:
        print("ERROR: No graphs created!")
        return
    
    # Train model
    model, best_acc = train_model(graphs, labels, epochs=100, batch_size=32)
    
    print("\nDONE! Model trained on real IaC data.")
    print(f"Final accuracy: {best_acc:.2%}")


if __name__ == "__main__":
    main()
