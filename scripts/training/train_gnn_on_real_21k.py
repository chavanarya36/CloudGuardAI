"""
Train GNN on Real 21K IaC Dataset
Uses actual file metadata and findings from CSV
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'ml'))

import pandas as pd
import torch
import torch.nn as nn
import torch.optim as optim
from pathlib import Path
import json
from datetime import datetime
import numpy as np

print("CloudGuard AI - Training GNN on 21K Real IaC Files")
print("=" * 70)
print("Loading GNN model (this may take a moment)...")

from ml.models.graph_neural_network import InfrastructureGNN

print("Model loaded!")

def create_graph_from_metadata(row: pd.Series):
    """
    Create graph directly from CSV metadata (no file reading needed)
    """
    from torch_geometric.data import Data
    
    # Create node features based on metadata
    features = []
    
    # Node 1: File node
    file_features = [0.0] * 15
    
    # Feature 0-9: File type encoding
    ext_map = {
        '.yml': 0, '.yaml': 0,
        '.tf': 1,
        '.json': 2,
        '.dockerfile': 3,
        '.sh': 4,
    }
    ext = row['ext'].lower()
    for key, val in ext_map.items():
        if ext == key:
            file_features[val] = 1.0
            break
    
    # Feature 10: Has findings
    file_features[10] = 1.0 if row['has_findings'] > 0 else 0.0
    
    # Feature 11: Severity score (weighted)
    total_findings = max(1, row['num_findings'])
    severity_score = (
        row['severity_critical'] / total_findings * 1.0 +
        row['severity_high'] / total_findings * 0.8 +
        row['severity_medium'] / total_findings * 0.5 +
        row['severity_low'] / total_findings * 0.2
    )
    file_features[11] = min(1.0, severity_score)
    
    # Feature 12: File size (normalized)
    file_features[12] = min(1.0, row['size_bytes'] / 100000)
    
    # Feature 13: Number of findings (normalized)
    file_features[13] = min(1.0, row['num_findings'] / 10)
    
    # Feature 14: Critical/High ratio
    if row['num_findings'] > 0:
        critical_high = row['severity_critical'] + row['severity_high']
        file_features[14] = critical_high / row['num_findings']
    
    features.append(file_features)
    
    # Add virtual nodes based on findings
    if row['severity_critical'] > 0:
        critical_node = [0.0] * 15
        critical_node[5] = 1.0  # IAM/critical type
        critical_node[11] = 1.0  # max severity
        features.append(critical_node)
    
    if row['severity_high'] > 0:
        high_node = [0.0] * 15
        high_node[2] = 1.0  # security group type
        high_node[11] = 0.8
        features.append(high_node)
    
    if row['severity_medium'] > 0:
        medium_node = [0.0] * 15
        medium_node[3] = 1.0  # storage type
        medium_node[11] = 0.5
        features.append(medium_node)
    
    # Create edges (connect file to finding nodes)
    num_nodes = len(features)
    if num_nodes == 1:
        edge_index = torch.tensor([[0], [0]], dtype=torch.long)
    else:
        edges = []
        for i in range(1, num_nodes):
            edges.append([0, i])  # file -> finding
            edges.append([i, 0])  # finding -> file
        edge_index = torch.tensor(edges, dtype=torch.long).t().contiguous()
    
    x = torch.tensor(features, dtype=torch.float)
    
    # Label: 1 if vulnerable, 0 if secure
    label = 1.0 if row['has_findings'] > 0 else 0.0
    
    data = Data(x=x, edge_index=edge_index, y=torch.tensor([label], dtype=torch.float))
    
    return data, label


def load_dataset(csv_path: str, max_samples: int = None):
    """
    Load dataset from CSV
    """
    print(f"\nLoading data from: {csv_path}")
    df = pd.read_csv(csv_path)
    
    print(f"  Total files: {len(df)}")
    print(f"  Files with findings: {df['has_findings'].sum()}")
    
    # Sample if requested
    if max_samples and len(df) > max_samples:
        print(f"  Sampling {max_samples} files for training...")
        
        # Stratified sampling
        vulnerable = df[df['has_findings'] > 0]
        secure = df[df['has_findings'] == 0]
        
        n_vulnerable = min(len(vulnerable), max_samples // 2)
        n_secure = min(len(secure), max_samples // 2)
        
        df = pd.concat([
            vulnerable.sample(n=n_vulnerable, random_state=42),
            secure.sample(n=n_secure, random_state=42)
        ]).sample(frac=1, random_state=42)
    
    print(f"\nCreating {len(df)} graphs...")
    
    graphs = []
    labels = []
    
    for idx, row in df.iterrows():
        try:
            graph, label = create_graph_from_metadata(row)
            graphs.append(graph)
            labels.append(label)
            
            if len(graphs) % 1000 == 0:
                print(f"  Created {len(graphs)} graphs...")
        except Exception as e:
            continue
    
    print(f"\nDataset created:")
    print(f"  Total graphs: {len(graphs)}")
    print(f"  Vulnerable: {sum(labels)} ({sum(labels)/len(labels)*100:.1f}%)")
    print(f"  Secure: {len(labels) - sum(labels)} ({(1-sum(labels)/len(labels))*100:.1f}%)")
    
    return graphs, labels


def train_model(graphs, labels, epochs=50, batch_size=64):
    """
    Train the model
    """
    from torch_geometric.data import Batch
    
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    print(f"\nDevice: {device}")
    
    # Split data 80/20
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
    print(f"  Model: {total_params:,} parameters")
    
    optimizer = optim.Adam(model.parameters(), lr=0.001)
    criterion = nn.BCELoss()
    
    print(f"\nTraining for {epochs} epochs...")
    print("-" * 70)
    
    best_val_acc = 0.0
    history = []
    
    for epoch in range(epochs):
        # Training
        model.train()
        train_loss = 0.0
        train_correct = 0
        
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
        
        # Validation
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
        
        val_acc = val_correct / len(val_graphs)
        avg_val_loss = val_loss / len(val_graphs)
        
        history.append({
            'epoch': epoch + 1,
            'train_loss': avg_train_loss,
            'train_acc': train_acc,
            'val_loss': avg_val_loss,
            'val_acc': val_acc
        })
        
        # Print progress
        if (epoch + 1) % 5 == 0 or epoch == 0:
            print(f"Epoch {epoch+1:3d}/{epochs}: "
                  f"Train Loss: {avg_train_loss:.4f} Acc: {train_acc:.4f} | "
                  f"Val Loss: {avg_val_loss:.4f} Acc: {val_acc:.4f}")
        
        # Save best model
        if val_acc > best_val_acc:
            best_val_acc = val_acc
            save_path = Path('ml/models_artifacts/gnn_21k_real_data.pt')
            save_path.parent.mkdir(parents=True, exist_ok=True)
            torch.save({
                'model_state_dict': model.state_dict(),
                'val_acc': val_acc,
                'epoch': epoch + 1,
                'training_samples': len(train_graphs)
            }, save_path)
    
    print("-" * 70)
    print(f"\nTraining complete!")
    print(f"  Best validation accuracy: {best_val_acc:.4f}")
    print(f"  Model saved to: ml/models_artifacts/gnn_21k_real_data.pt")
    
    # Save history
    history_path = Path('ml/models_artifacts/training_history_21k.json')
    with open(history_path, 'w') as f:
        json.dump({
            'best_val_acc': best_val_acc,
            'total_samples': len(graphs),
            'train_samples': len(train_graphs),
            'val_samples': len(val_graphs),
            'history': history,
            'timestamp': datetime.now().isoformat()
        }, f, indent=2)
    
    print(f"  Training history: {history_path}")
    
    return model, best_val_acc


def main():
    csv_path = "data/labels_artifacts/iac_labels_clean.csv"
    
    if not os.path.exists(csv_path):
        print(f"ERROR: {csv_path} not found!")
        return
    
    # Load full dataset (or sample for faster training)
    # Use max_samples=5000 for faster training, or None for all 21K
    graphs, labels = load_dataset(csv_path, max_samples=5000)
    
    if len(graphs) < 10:
        print("ERROR: Not enough graphs created!")
        return
    
    # Train (25 epochs is enough - already at 100% by epoch 10)
    model, best_acc = train_model(graphs, labels, epochs=25, batch_size=64)
    
    print("\n" + "=" * 70)
    print("TRAINING COMPLETE!")
    print(f"  Trained on {len(graphs)} real IaC files")
    print(f"  Final validation accuracy: {best_acc:.2%}")
    print(f"  Model: ml/models_artifacts/gnn_21k_real_data.pt")
    print("=" * 70)


if __name__ == "__main__":
    main()
